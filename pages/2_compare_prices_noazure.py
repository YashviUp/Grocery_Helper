import streamlit as st
import pandas as pd
import requests
import re
import json
import os
from PIL import Image
import io
from collections import defaultdict
from bs4 import BeautifulSoup

PLATFORM_CONFIG = {
    'Blinkit': {'delivery_time': 15, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/blinkit.webp"},
    'Zepto': {'delivery_time': 19, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/zepto.webp"},
    'Swiggy': {'delivery_time': 45, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/swiggy.webp"},
    'JioMart': {'delivery_time': 1440, 'logo': "https://qcsearch.s3.ap-south-1.amazonaws.com/platforms/jiomart.webp"},
    'Dmart': {'delivery_time': 1440, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/dmart.webp"},
    'Bigbasket': {'delivery_time': 11, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/bigbasket.webp"},
}

def extract_image_from_html(html_snippet):
    """Extract image URL from product HTML snippet"""
    soup = BeautifulSoup(html_snippet, 'html.parser')
    img_tag = soup.find('img', class_='h-24 w-full bg-transparent object-contain gap-2')
    return img_tag['src'] if img_tag and img_tag.get('src') else ""


def clean_product_name(name, exclude_keywords):
    """
    Clean product name using Azure Cognitive Services key phrase extraction
    and remove exclude keywords.
    """

    name_clean = name
    for kw in exclude_keywords:
        # Remove keyword as a word or part of a word, case-insensitive
        name_clean = re.sub(r'\b' + re.escape(kw) + r'\b', '', name_clean, flags=re.IGNORECASE)
        # Also remove keyword if it's part of a phrase
        name_clean = re.sub(re.escape(kw), '', name_clean, flags=re.IGNORECASE)
    # Remove extra spaces
    name_clean = re.sub(r'\s+', ' ', name_clean)
    return name_clean.strip()
def parse_quantity(quantity_str):
    """Convert quantity string to grams with detailed validation"""
    try:
        if not quantity_str or not isinstance(quantity_str, str):
            st.warning(f"Invalid quantity format: {quantity_str}")
            return None
        
        # Extract multiplier and base quantity
        multiplier = 1.0
        if 'x' in quantity_str:
            parts = quantity_str.lower().split('x')
            if len(parts) != 2:
                return None
            multiplier_str = parts[1].strip()
            multiplier = float(multiplier_str) if multiplier_str else 1.0
            base_str = parts[0].strip()
        else:
            base_str = quantity_str.strip()

        # Parse base quantity
        if 'kg' in base_str:
            grams = float(re.sub(r'[^\d.]', '', base_str)) * 1000
        elif 'g' in base_str:
            grams = float(re.sub(r'[^\d.]', '', base_str))
        else:  # Raw number assuming grams
            grams = float(re.sub(r'[^\d.]', '', base_str))
        
        total_grams = grams * multiplier
        if total_grams <= 0:
            st.warning(f"Invalid quantity value: {quantity_str}")
            return None
            
        return total_grams
        
    except Exception as e:
        st.error(f"Quantity parsing failed for '{quantity_str}': {str(e)}")
        return None

def get_price(item):
    """Get valid price with strict validation"""
    price_keys = ['offer_price', 'unit_level_price', 'mrp']
    for key in price_keys:
        try:
            raw_value = item.get(key)
            if raw_value is None:
                continue
                
            # Convert to string and clean
            price_str = str(raw_value).strip()
            if not any(c.isdigit() for c in price_str):
                continue
                
            # Extract numeric value
            price = float(re.sub(r'[^\d.]', '', price_str))
            if price <= 0:
                continue
                
            return price
        except Exception as e:
            continue
            
    st.warning(f"No valid price found in {item.get('name')}")
    return None

def process_platform_data(product_query, lat=19.0760, lon=72.8777):
    """Process data with enhanced validation"""
    processed = []
    exclude_keywords = ['special', 'rich', 'flavourful', 'roasted', 'salted', 
                       'mini', 'tasty', 'healthy', 'classic', 'organic', 'new', 
                       'soft', 'fluffy', 'roti', 'chakki', 'refined', 'box', 'combo']
    
    # Fetch data with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "https://yr338c15si.execute-api.ap-south-1.amazonaws.com/getQCResults",
                params={'lat': lat, 'lon': lon, 'type': 'groupsearch', 'query': product_query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            if attempt == max_retries - 1:
                st.error(f"API request failed after {max_retries} attempts: {str(e)}")
                return []
            continue

    if not isinstance(data, list):
        st.error("Invalid API response format")
        return []

    for platform_data in data:
        if not isinstance(platform_data, dict):
            continue
            
        for item in platform_data.get('data', []):
            try:
                # Mandatory fields check
                if not all(key in item for key in ['name', 'platform', 'quantity']):
                    continue
                    
                # Product name matching
                item_name = item.get('name', '').lower()
                if product_query.lower() not in item_name:
                    continue

                # Price validation
                price = get_price(item)
                if price is None:
                    continue
                    
                # Quantity validation
                quantity = item.get('quantity', '')
                grams = parse_quantity(quantity)
                if grams is None or grams <= 0:
                    continue

                # Image handling
                html_image = extract_image_from_html(item.get("html", ""))
                images = item.get("images", [])
                image_url = html_image or (images[0] if images else "")
                
                # Platform validation
                platform_name = item['platform'].get('name', '').title()
                if platform_name not in PLATFORM_CONFIG:
                    continue

                # Name cleaning
                name = clean_product_name(item['name'].strip().lower(), exclude_keywords)
                
                # Price calculation
                price_per_g = round(price / grams, 3)

                processed.append({
                    'title': name,
                    'platform': platform_name,
                    'platform_logo': PLATFORM_CONFIG[platform_name]['logo'],
                    'price': price,
                    'quantity': quantity,
                    'grams': grams,
                    'image_url': image_url,
                    'delivery_time': '1 day' if PLATFORM_CONFIG[platform_name]['delivery_time'] == 1440 
                                   else f"{PLATFORM_CONFIG[platform_name]['delivery_time']} mins",
                    'id': f"{platform_name}_{hash(image_url)}_{hash(name)}",
                    'price_per_g': price_per_g
                })

            except Exception as e:
                st.error(f"Error processing item: {str(e)}")
                continue

    return processed


def display_product_card(item, preferences):
    """Display a product in a nice card format"""
    # Create a container for the card
    with st.container():
        # Main content row
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.image(item['image_url'], width=100)
        
        with col2:
            st.markdown(f"### {item['title']}")
            
            # Platform info in a single row using HTML
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px;">
                    <img src="{item['platform_logo']}" width="50">
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**Quantity:** {item['quantity']}")
            st.markdown(f"**Price/g:** ₹{item['price_per_g']:.3f}")
            st.markdown(f"**Delivery Time:** {item['delivery_time']}")
            
        
        with col3:
            if st.button("❌", key=f"remove_{item['id']}"):
                if 'removed_ids' not in st.session_state:
                    st.session_state['removed_ids'] = set()
                    st.session_state['removed_ids'].add(item['id'])
                    st.success(f"Removed {item['title']} from cart.")



def page_2():
    st.title("💰 Price Comparison")
    
    # Get location and preferences from Page 1
    lat = st.session_state.get('latitude', 19.0760)
    lon = st.session_state.get('longitude', 72.8777)
    delivery = st.session_state.get('preferences', {
        'delivery_speed': '1 day'
    })['delivery_speed']
    st.markdown(delivery)
    max_minutes = {
    "20 minutes": 20,
    "45 minutes": 45,
    "1 day": 1440}[delivery]
    if 'removed_ids' not in st.session_state:
        st.session_state.removed_ids = set()

    allowed_platforms = [p for p, config in PLATFORM_CONFIG.items() 
                        if config.get('delivery_time', 1440) <= max_minutes]

    cart = st.session_state.get('cart_items', [])
    
    if not cart:
        st.warning("Upload your bill on Page 1 first")
        return

    # Initialize cart matrix
    cart_matrix = {platform: [] for platform in allowed_platforms}
    platform_totals = {platform: 0.0 for platform in allowed_platforms}
    
    for item in cart:
        # Use product_title instead of title
        product_query = f"{item['product_title']}".lower().strip()
        
        with st.expander(f"🔍 {product_query}", expanded=True):
            # Get and process data from cache
            results = process_platform_data(product_query, lat, lon)
            
            if not results:
                st.info("No prices available")
                continue
                
            filtered_df = [
                item for item in results
                if item['platform'] in allowed_platforms
                and item['id'] not in st.session_state.get('removed_ids', set())
            ]
            
            platform_groups = defaultdict(list)
            for item in filtered_df:
                platform_groups[item['platform']].append(item)
            
            # Get top items for each platform
            top_items = {}
            for platform in allowed_platforms:
                platform_items = sorted(platform_groups.get(platform, []), key=lambda x: x['price_per_g'])[:5]
                if platform_items:
                    top_items[platform] = platform_items[0]  # Get the cheapest item
                    cart_matrix[platform].append(top_items[platform])
                    platform_totals[platform] += top_items[platform]['price']
            
            if not top_items:
                st.info("No products match your delivery time filter")
                continue            
            
            # Display products in a grid
            cols = st.columns(2)
            for idx, (platform, product) in enumerate(top_items.items()):
                with cols[idx % 2]:
                    display_product_card(
                        product, 
                        delivery
                    )
            
            st.divider()

if __name__ == "__main__":
    page_2()
