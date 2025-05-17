import streamlit as st
import pandas as pd
import re
import pdfplumber
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Grocery Cart Compare",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state='collapsed'
)

# User Preferences Section
def show_preferences():
    st.sidebar.title("🎯 Shopping Preferences")
    preferences = {
        "delivery_speed": st.sidebar.selectbox(
            "Preferred Delivery Time",
            ["11-20 minutes", "45 minutes", "1 day"],
            index=2,
            help="Select your preferred delivery time window"
        ),
        "family_size": st.sidebar.number_input("Family Size", 1, 10, 4),
        "dietary_restrictions": st.sidebar.multiselect(
            "Dietary Restrictions",
            ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "None"]
        )
    }
    return preferences

# Monthly Meal Plan to Grocery List
def meal_plan_to_grocery():
    st.subheader("📋 Monthly Meal Plan to Grocery List")
    meal_plan = st.text_area(
        "Enter your monthly meal plan (one meal per line)",
        height=150,
        help="Example: Dal Rice (4 servings)\nPaneer Butter Masala (3 servings)"
    )
    
    if meal_plan and st.button("Generate Grocery List"):
        meals = meal_plan.split('\n')
        grocery_list = []
        
        # Basic conversion ratios (can be expanded)
        ratios = {
            "dal": 50,  # grams per serving
            "rice": 75,  # grams per serving
            "paneer": 100,  # grams per serving
            "vegetables": 150,  # grams per serving
        }
        
        for meal in meals:
            if not meal.strip():
                continue
            
            # Extract servings if specified
            servings = 4  # default
            if '(' in meal:
                meal_name, serving_info = meal.split('(')
                servings = int(re.search(r'\d+', serving_info).group())
                meal_name = meal_name.strip()
            else:
                meal_name = meal
            
            # Convert meal to ingredients (simplified)
            if 'dal' in meal_name.lower():
                grocery_list.append({
                    "product_title": "Toor Dal",
                    "brand": "Tata Sampann",
                    "quantity": f"{ratios['dal'] * servings}g",
                    "lock_brand": False,
                    "lock_qty": False
                })
            
            if 'rice' in meal_name.lower():
                grocery_list.append({
                    "product_title": "Basmati Rice",
                    "brand": "India Gate",
                    "quantity": f"{ratios['rice'] * servings}g",
                    "lock_brand": False,
                    "lock_qty": False
                })
                
        return pd.DataFrame(grocery_list)
    return None

# 🌍 Location Detection
location = streamlit_geolocation()
if location:
    st.session_state.latitude = location['latitude']
    st.session_state.longitude = location['longitude']
    st.write(f"📍 Location: ({location['latitude']}, {location['longitude']})")

# Get user preferences
preferences = show_preferences()
st.session_state.preferences = preferences

# 📦 PDF Parsing Utilities
def parse_weight_unit(text):
    match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g|ml|l|L)\b', text, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        cleaned = re.sub(r',?\s*\d+(?:\.\d+)?\s*(kg|g|ml|l|L)\b', '', text, flags=re.IGNORECASE).strip().rstrip(',')
        return value, unit, cleaned
    return None, None, text.strip().rstrip(',')

def extract_items_from_invoice(uploaded_file):
    items = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            lines = text.split('\n')

            start, end = None, None
            for i, line in enumerate(lines):
                if line.strip().startswith('FOOD ITEMS'):
                    start = i + 1
                if line.strip().startswith('Summary'):
                    end = i
                    break

            if start is not None and end is not None:
                for line in lines[start:end]:
                    if not line.strip() or line.strip().startswith(('S. No', 'Item')):
                        continue

                    m = re.match(r'\s*\d+\s+(.+?)\s+\d{8,}\s+(\d+)\s+', line)
                    if m:
                        item_full, qty = m.groups()
                        qty = int(qty)
                        value, unit, name = parse_weight_unit(item_full)
                        brand = extract_brand(name)
                        name_cleaned = remove_brand_from_name(name, brand)
                        quantity = f"{int(value)} {unit}" if value and unit else str(qty)
                        items.append({
                            "product_title": name_cleaned,
                            "brand": brand,
                            "quantity": quantity,
                            "lock_brand": False,
                            "lock_qty": False
                        })
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return pd.DataFrame(columns=["product_title", "brand", "quantity", "lock_brand", "lock_qty"])

    df = pd.DataFrame(items)
    df = df.drop_duplicates(subset=["product_title"])
    return df

def extract_brand(name):
    match = re.search(r'by\s+(.+?)(?:,|$)', name, re.IGNORECASE)
    return match.group(1).strip() if match else name.split()[0] if name else ""

def remove_brand_from_name(name, brand):
    name = re.sub(r'by\s+.+?(,|$)', '', name, flags=re.IGNORECASE).strip()
    return name[len(brand):].strip(" ,") if name.lower().startswith(brand.lower()) else name.strip()

# 🧾 Main UI Logic
st.title("🧾 Upload Grocery Bills")

platforms = st.multiselect(
    "🔍 Do you have any Platform Subscriptions that Eliminate Delivery Fee?",
    ["Swiggy", "Zepto", "Big Basket", "Blinkit"]
)

uploaded_files = st.file_uploader("Upload Invoice PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("🔍 Processing invoices..."):
        all_items = pd.concat(
            [extract_items_from_invoice(file) for file in uploaded_files],
            ignore_index=True
        )

    if not all_items.empty:
        st.success(f"✅ Extracted {len(all_items)} unique items.")
        st.markdown("### 🛒 Editable Cart")

        if "cart_items" not in st.session_state:
            st.session_state.cart_items = all_items.to_dict("records")

        updated_items = []
        for i, row in enumerate(st.session_state.cart_items):
            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1, 2, 1, 1])
            with c1:
                title = st.text_input("Product", row["product_title"], key=f"title_{i}")
            with c2:
                brand = st.text_input("Brand", row["brand"], key=f"brand_{i}", disabled=row["lock_brand"])
            with c3:
                lock_b = st.checkbox("🔒", value=row["lock_brand"], key=f"lockb_{i}")
            with c4:
                qty = st.text_input("Quantity", row["quantity"], key=f"qty_{i}", disabled=row["lock_qty"])
            with c5:
                lock_q = st.checkbox("🔒", value=row["lock_qty"], key=f"lockq_{i}")
            with c6:
                remove = st.button("➖", key=f"remove_{i}")

            if not remove:
                updated_items.append({
                    "product_title": title,
                    "brand": brand,
                    "quantity": qty,
                    "lock_brand": lock_b,
                    "lock_qty": lock_q
                })

        st.session_state.cart_items = updated_items

        # Add item button
        col_add = st.columns([1])[0]
        if col_add.button("➕ Add Item"):
            st.session_state.cart_items.append({
                "product_title": "",
                "brand": "",
                "quantity": "",
                "lock_brand": False,
                "lock_qty": False
            })

        # 💾 Save to session state for Page 2
        st.session_state.selected_items = updated_items

        # ✅ Navigation
        st.markdown("👉 Go to **Compare Options** from the sidebar")

        # After processing uploaded files, add meal plan conversion
        if "cart_items" in st.session_state:
            st.markdown("---")
            meal_plan_items = meal_plan_to_grocery()
            
            if meal_plan_items is not None and not meal_plan_items.empty:
                st.success("✅ Generated grocery list from meal plan")
                # Merge with existing cart items
                new_items = pd.concat([
                    pd.DataFrame(st.session_state.cart_items),
                    meal_plan_items
                ]).drop_duplicates(subset=["product_title"]).to_dict("records")
                st.session_state.cart_items = new_items

        # Add monthly estimation
        if st.session_state.cart_items:
            st.markdown("---")
            st.subheader("📊 Monthly Estimation")
            monthly_multiplier = st.slider("How many weeks worth of groceries is this?", 1, 4, 1)
            
            if monthly_multiplier > 1:
                monthly_items = []
                for item in st.session_state.cart_items:
                    monthly_item = item.copy()
                    if 'g' in item['quantity'].lower():
                        qty = float(re.search(r'\d+', item['quantity']).group())
                        monthly_item['quantity'] = f"{int(qty * monthly_multiplier)}g"
                    monthly_items.append(monthly_item)
                
                st.session_state.monthly_cart = monthly_items
                st.success(f"✅ Generated {monthly_multiplier}-week grocery list")

    else:
        st.warning("⚠️ No items extracted. Try another invoice.")
else:
    st.info("📤 Please upload grocery invoice PDFs.")
