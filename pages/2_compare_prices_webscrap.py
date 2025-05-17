import streamlit as st
import pandas as pd
import requests
import re
import json
import os
from PIL import Image
import io
from collections import defaultdict


PLATFORM_CONFIG = {
    'Blinkit': {'delivery_time': 15, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/blinkit.webp"},
    'Zepto': {'delivery_time': 19, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/zepto.webp"},
    'Swiggy': {'delivery_time': 45, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/swiggy.webp"},
    'JioMart': {'delivery_time': 1440, 'logo': "https://qcsearch.s3.ap-south-1.amazonaws.com/platforms/jiomart.webp"},
    'Dmart': {'delivery_time': 1440, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/dmart.webp"},
    'Bigbasket': {'delivery_time': 11, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/bigbasket.webp"},
}



def load_cached_results(product_query):
    """Load results from cached JSON file in ./data directory"""
    sanitized_query = re.sub(r'[^a-z0-9]', '', product_query.lower())
    json_files = [f for f in os.listdir('./data') if f.startswith('qc_') and f.endswith('.json')]
    if not json_files:
        return None

    best_match = None
    best_match_score = 0

    for file in json_files:
        file_product = file.split('_')[1]
        file_product_clean = re.sub(r'[^a-z0-9]', '', file_product.lower())
        query_clean = re.sub(r'[^a-z0-9]', '', sanitized_query.lower())
        query_words = query_clean.split()
        matching_words = sum(1 for word in query_words if word in file_product_clean)
        match_score = matching_words
        if (matching_words >= 2 or query_clean in file_product_clean) and match_score > best_match_score:
            best_match = file
            best_match_score = match_score

    if best_match:
        file_path = os.path.join('./data', best_match)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error reading cache file: {str(e)}")
            return None

    return None
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
    """Convert quantity string to grams with multiplier support"""
    try:
        # Handle empty or invalid input
        if not quantity_str or not isinstance(quantity_str, str):
            return None
        
        # Split into quantity and multiplier parts
        parts = quantity_str.lower().split('x')
        base_quantity = parts[0].strip()
        multiplier = float(parts[1].strip()) if len(parts) > 1 else 1.0
        
        # Parse base quantity
        if 'kg' in base_quantity:
            grams = float(base_quantity.replace('kg', '').strip()) * 1000
        elif 'g' in base_quantity:
            grams = float(base_quantity.replace('g', '').strip())
        else:  # Handle raw numbers assuming grams
            grams = float(base_quantity.strip())
        
        return grams * multiplier
        
    except (ValueError, AttributeError, TypeError):
        return None
def get_price(item):
    for key in ['offer_price', 'unit_level_price', 'mrp']:
        val = item.get(key, None)
        if val is not None:
            val_str = str(val).strip()
            if val_str and any(c.isdigit() for c in val_str):
                try:
                    # Remove all non-digit/decimal characters (handles â‚¹, commas, etc.)
                    price = float(re.sub(r'[^\d.]', '', val_str))
                    return price
                except Exception:
                    continue
    return 0.0


def process_platform_data(data):
    """Process platform data into standardized format"""
    processed = []
    platform_items = defaultdict(list)
    platform_top_items = {}

    exclude_keywords = ['special', 'rich', 'flavourful', 'roasted','salted','mini','tasty','healthy','classic','organic','new','soft','fluffy','roti','chakki', 'refined', 'box','combo']
    
    for platform in data:
        for item in platform.get('data', []):
            try:
                image_url = next((img for img in item.get('images', []) 
                                if img.startswith(('http://', 'https://'))), 
                               'https://via.placeholder.com/100x100.png?text=No+Image')

                # Platform handling
                platform_name = item.get('platform', {}).get('name', '').title()
                if not platform_name or platform_name not in PLATFORM_CONFIG:
                    continue

                # Get price from item, not platform
                price = get_price(item)

                quantity = item.get('quantity', '')
                grams = parse_quantity(quantity) or 1

                name = clean_product_name(item.get('name', '').strip().lower(), exclude_keywords)
                unique_id = f"{name}_{quantity}_{platform_name}"
                price_per_g = float(price / grams) if grams and price else 0.0

                entry = {
                    'title': name,
                    'platform': platform_name,
                    'platform_logo': PLATFORM_CONFIG[platform_name]['logo'],
                    'price': price,
                    'quantity': quantity,
                    'grams': grams,
                    'image_url': image_url,
                    'delivery_time': '1 day' if PLATFORM_CONFIG[platform_name]['delivery_time']==1440 else f"{PLATFORM_CONFIG[platform_name]['delivery_time']} mins",
                    'id' : unique_id,
                    'price_per_g': price_per_g
                }
                if unique_id in st.session_state.get('removed_ids', set()):
                    continue
                
                platform_items[platform_name].append(entry)
                current_top = platform_top_items.get(platform_name, {'price_per_g': float('inf')})

                if not platform_top_items.get(platform_name) or price_per_g < current_top['price_per_g']:
                    platform_top_items[platform_name] = entry

                processed.append(entry)

            except Exception as e:
                print(f"Debug - Error processing {item.get('name')}: {str(e)}")
                continue
        
        for platform, config in PLATFORM_CONFIG.items():
            if platform not in platform_items:
                continue
            if not any(item['platform'] == platform for item in processed):
                processed.append(platform_top_items[platform])
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
            if st.button("âŒ", key=f"remove_{item['id']}"):
                if 'removed_ids' not in st.session_state:
                    st.session_state['removed_ids'] = set()
                    st.session_state['removed_ids'].add(item['id'])
                    st.success(f"Removed {item['title']} from cart.")



def page_2():
    st.title("🛒 Price Comparison")
    
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
            cached_data = load_cached_results(product_query)
            if not cached_data:
                st.info("No cached data available for this product")
                continue
                
            results = process_platform_data(cached_data)
            
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