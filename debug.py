import requests
import pandas as pd
from bs4 import BeautifulSoup

def extract_image_from_html(html_snippet):
    """Extract image URL from product HTML snippet"""
    soup = BeautifulSoup(html_snippet, 'html.parser')
    img_tag = soup.find('img', class_='h-24 w-full bg-transparent object-contain gap-2')
    return img_tag['src'] if img_tag and img_tag.get('src') else ""

def scrape_quickcompare(product_query, lat=19.0760, lon=72.8777):
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
                                
                # Ensure all required fields exist
                entry = {
                    'platform': item.get('platform', {}).get('name', 'Unknown'),
                    'product': item.get('name', 'Unnamed Product'),
                    'brand': item.get('brand', ''),
                    'mrp': item.get('mrp', 0),
                    'offer_price': item.get('offer_price', 0),
                    'quantity': item.get('quantity', ''),
                    'delivery_time': item.get('platform', {}).get('sla', ''),
                    'image_html': image_url
                }
                results.append(entry)

        return pd.DataFrame(results)

    except Exception as e:
        print(f"Error: {str(e)}")
        return pd.DataFrame()

# Test with proper column checks
df = scrape_quickcompare("low sodium salt")

if not df.empty:
    # Get valid columns that exist in the DataFrame
    valid_columns = [col for col in ['product', 'platform', 'offer_price', 'quantity'] 
                     if col in df.columns]
    
    if valid_columns:
        print(df[valid_columns].head())
    else:
        print("No valid columns found in the DataFrame")
else:
    print("No data returned from the API")
