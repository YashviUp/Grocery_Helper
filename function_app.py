import azure.functions as func
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import azure.cosmos.cosmos_client as cosmos_client
import os

DATABASE_NAME = 'QuickCompareCache'
CONTAINER_NAME = 'ProductCache'

def get_cosmos_client():
    return cosmos_client.CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

def extract_image_from_html(html_snippet):
    """Extract image URL from product HTML snippet"""
    soup = BeautifulSoup(html_snippet, 'html.parser')
    img_tag = soup.find('img', class_='h-24 w-full bg-transparent object-contain gap-2')
    return img_tag['src'] if img_tag and img_tag.get('src') else ""

def get_cached_results(query, lat, lon):
    """Get cached results from Cosmos DB"""
    try:
        client = get_cosmos_client()
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        
        # Create cache key from query parameters
        cache_key = f"{query}_{lat}_{lon}"
        
        # Query for cached results
        query = f"SELECT * FROM c WHERE c.id = '{cache_key}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            cache_entry = items[0]
            # Check if cache is still valid (24 hours)
            if datetime.fromisoformat(cache_entry['timestamp']) > datetime.now() - timedelta(hours=24):
                return cache_entry['results']
        return None
    except Exception as e:
        logging.error(f"Error accessing cache: {str(e)}")
        return None

def cache_results(query, lat, lon, results):
    """Cache results in Cosmos DB"""
    try:
        client = get_cosmos_client()
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        
        # Create cache entry
        cache_key = f"{query}_{lat}_{lon}"
        cache_entry = {
            'id': cache_key,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
        # Upsert cache entry
        container.upsert_item(cache_entry)
    except Exception as e:
        logging.error(f"Error caching results: {str(e)}")

def scrape_quickcompare(product_query, lat=19.0760, lon=72.8777):
    """Scrape product data from QuickCompare API"""
    url = "https://yr338c15si.execute-api.ap-south-1.amazonaws.com/getQCResults"
    params = {
        'lat': lat,
        'lon': lon,
        'type': 'groupsearch',
        'query': product_query
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []
        for platform_data in data:
            for item in platform_data.get('data', []):
                # Extract image from HTML first
                html_image = extract_image_from_html(item.get("html", ""))
                images = item.get("images", [])
                image_url = html_image if html_image else (images[0] if images else "")
                                
                results.append({
                    'platform': item['platform']['name'],
                    'product': item['name'],
                    'brand': item.get('brand', ''),
                    'mrp': item['mrp'],
                    'offer_price': item['offer_price'],
                    'quantity': item['quantity'],
                    'delivery_time': item['platform']['sla'],
                    'image_html': image_url
                })
        return results
    except Exception as e:
        logging.error(f"Error scraping data: {str(e)}")
        return []

app = func.FunctionApp()

@app.function_name(name="QuickCompareScraper")
@app.route(route="scrape", auth_level=func.AuthLevel.FUNCTION)
def quick_compare_scraper(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        product_query = req_body.get('query')
        lat = float(req_body.get('lat', 19.0760))
        lon = float(req_body.get('lon', 72.8777))
        
        if not product_query:
            return func.HttpResponse(
                "Please provide a product query in the request body",
                status_code=400
            )

        # Try to get cached results first
        cached_results = get_cached_results(product_query, lat, lon)
        if cached_results:
            return func.HttpResponse(
                json.dumps(cached_results),
                mimetype="application/json"
            )

        # If no cache, scrape new results
        results = scrape_quickcompare(product_query, lat, lon)
        
        # Cache the results
        cache_results(product_query, lat, lon, results)
        
        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(
            f"Error processing request: {str(e)}",
            status_code=500
        )