import azure.functions as func
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import azure.cosmos.cosmos_client as cosmos_client
import os

# Environment variables for Cosmos DB (set in Azure Function configuration)
COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
COSMOS_KEY = os.environ.get('COSMOS_KEY')

DATABASE_NAME = 'QuickCompareCache'
CONTAINER_NAME = 'ProductCache'

def get_cosmos_client():
    """Create Cosmos DB client with environment variables"""
    return cosmos_client.CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

def extract_image_from_html(html_snippet):
    """Extract image URL from product HTML snippet"""
    soup = BeautifulSoup(html_snippet, 'html.parser')
    img_tag = soup.find('img', class_='h-24 w-full bg-transparent object-contain gap-2')
    return img_tag['src'] if img_tag and img_tag.get('src') else ""

def get_cached_results(query, lat, lon):
    """Get cached results from Cosmos DB with parameterized query"""
    try:
        client = get_cosmos_client()
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        
        # Parameterized query for security
        cache_key = f"{query}_{lat}_{lon}"
        query_spec = {
            'query': "SELECT * FROM c WHERE c.id = @id",
            'parameters': [{'name': '@id', 'value': cache_key}]
        }
        
        items = list(container.query_items(query=query_spec, enable_cross_partition_query=True))
        
        if items and datetime.fromisoformat(items[0]['timestamp']) > datetime.now() - timedelta(hours=24):
            return items[0]['results']
        return None
    except Exception as e:
        logging.error(f"Cache access error: {str(e)}")
        return None

def cache_results(query, lat, lon, results):
    """Cache results in Cosmos DB with TTL"""
    try:
        client = get_cosmos_client()
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)
        
        cache_entry = {
            'id': f"{query}_{lat}_{lon}",
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'ttl': 86400  # 24-hour expiration
        }
        
        container.upsert_item(cache_entry)
    except Exception as e:
        logging.error(f"Cache write error: {str(e)}")

def scrape_quickcompare(product_query, lat=19.0760, lon=72.8777):
    """Scrape product data with enhanced error handling"""
    url = "https://yr338c15si.execute-api.ap-south-1.amazonaws.com/getQCResults"
    params = {'lat': lat, 'lon': lon, 'type': 'groupsearch', 'query': product_query}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return process_api_response(response.json())
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        return []

def process_api_response(data):
    """Process API response with validation"""
    results = []
    for platform_data in data:
        if not isinstance(platform_data, dict) or 'data' not in platform_data:
            continue
            
        for item in platform_data['data']:
            processed_item = validate_and_process_item(item)
            if processed_item:
                results.append(processed_item)
    return results

def validate_and_process_item(item):
    """Validate and process individual items"""
    try:
        return {
            'platform': item['platform']['name'],
            'product': item['name'],
            'brand': item.get('brand', ''),
            'mrp': item['mrp'],
            'offer_price': item['offer_price'],
            'quantity': item['quantity'],
            'delivery_time': item['platform']['sla'],
            'image_html': get_image_url(item)
        }
    except KeyError as e:
        logging.warning(f"Invalid item structure: {str(e)}")
        return None

def get_image_url(item):
    """Safe image URL extraction"""
    return (
        extract_image_from_html(item.get("html", "")) 
        or next(iter(item.get("images", [])), "")
    )

app = func.FunctionApp()

@app.function_name(name="QuickCompareScraper")
@app.route(route="scrape", auth_level=func.AuthLevel.FUNCTION)
def quick_compare_scraper(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        product_query = req_body.get('query', '').strip()
        lat = float(req_body.get('lat', 19.0760))
        lon = float(req_body.get('lon', 72.8777))
        
        if not product_query:
            return func.HttpResponse("Product query required", status_code=400)

        if cached := get_cached_results(product_query, lat, lon):
            return func.HttpResponse(json.dumps(cached), mimetype="application/json")

        results = scrape_quickcompare(product_query, lat, lon)
        cache_results(product_query, lat, lon, results)
        return func.HttpResponse(json.dumps(results), mimetype="application/json")

    except Exception as e:
        logging.error(f"Request processing error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
