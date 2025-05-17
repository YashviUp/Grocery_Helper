import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
PLATFORM_CONFIG = {
    'Blinkit': {'delivery_time': 15, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/blinkit.webp"},
    'Zepto': {'delivery_time': 19, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/zepto.webp"},
    'Swiggy': {'delivery_time': 45, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/swiggy.webp"},
    'JioMart': {'delivery_time': 1440, 'logo': "https://qcsearch.s3.ap-south-1.amazonaws.com/platforms/jiomart.webp"},
    'Dmart': {'delivery_time': 1440, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/dmart.webp"},
    'Bigbasket': {'delivery_time': 11, 'logo': "https://d2chhaxkq6tvay.cloudfront.net/platforms/bigbasket.webp"},
}

def display_product_list(products, category):
    """Display a list of products in a category"""
    if not products:
        return
    st.subheader(f"📦 {category}")
    for product in products:
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(product.get('image_url', ''), width=100)
            with col2:
                st.markdown(f"**{product.get('title','')}**")
                st.markdown(f"Price: ₹{product.get('price','')}")
                st.markdown(f"Delivery: {product.get('delivery_time','')}")
                st.markdown(f"Platform: {product.get('platform','')}")

def categorize_product(product):
    """Categorize a product based on price and delivery time"""
    try:
        delivery_time_str = str(product['delivery_time'])
        if 'day' in delivery_time_str:
            delivery_minutes = float(delivery_time_str.split()[0]) * 1440
        else:
            delivery_minutes = float(delivery_time_str.split()[0])
        price = float(product['price'])
        price_threshold = 100
        delivery_threshold = 30
        if price <= price_threshold and delivery_minutes <= delivery_threshold:
            return "Quick & Budget"
        elif price <= price_threshold and delivery_minutes > delivery_threshold:
            return "Budget"
        elif price > price_threshold and delivery_minutes <= delivery_threshold:
            return "Quick"
        else:
            return "Standard"
    except Exception:
        return "Standard"

def create_eisenhower_matrix(products):
    """Create an Eisenhower matrix visualization"""
    import plotly.graph_objects as go
    if not products:
        return None, None
    categories = {
        "Quick & Budget": [],
        "Budget": [],
        "Quick": [],
        "Standard": []
    }
    for product in products:
        category = categorize_product(product)
        categories[category].append(product)
    fig = go.Figure()
    fig.add_annotation(x=0.25, y=0.75, text="Quick & Budget<br>Express Delivery",
                      showarrow=False, font=dict(size=14, color="green"))
    fig.add_annotation(x=0.75, y=0.75, text="Quick<br>Premium Delivery",
                      showarrow=False, font=dict(size=14, color="blue"))
    fig.add_annotation(x=0.25, y=0.25, text="Budget<br>Standard Delivery",
                      showarrow=False, font=dict(size=14, color="orange"))
    fig.add_annotation(x=0.75, y=0.25, text="Standard<br>Regular Delivery",
                      showarrow=False, font=dict(size=14, color="gray"))
    fig.add_shape(type="line", x0=0.5, y0=0, x1=0.5, y1=1, line=dict(color="black", width=2))
    fig.add_shape(type="line", x0=0, y0=0.5, x1=1, y1=0.5, line=dict(color="black", width=2))
    fig.update_layout(
        title="Product Optimization Matrix",
        xaxis=dict(showticklabels=False, range=[0, 1]),
        yaxis=dict(showticklabels=False, range=[0, 1]),
        showlegend=False,
        height=600
    )
    return fig, categories

def render_page_3():
    st.title("🛒 Optimized Cart")

    cart_matrix = st.session_state.get('cart_matrix', defaultdict(list))
    platform_totals = st.session_state.get('platform_totals', defaultdict(float))

    if not cart_matrix:
        st.warning("No cart data found. Please select items first.")
        return
    
    st.header("📈 Product Optimization Matrix")
    all_items = []
    for platform, items in cart_matrix.items():
        for item in items:
            all_items.append({
                'title': item.get('title', ''),
                'price': item.get('price', 0),
                'delivery_time': PLATFORM_CONFIG[platform]['delivery_time'],
                'platform': platform,
                'image_url': item.get('image_url', '')
                })
            
    fig, categories = create_eisenhower_matrix(all_items)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.header("🚚 Cost vs Delivery Time Matrix")
    matrix_data = []
    for platform, items in cart_matrix.items():
        total_price = sum(item['price'] for item in items)
        delivery_time = PLATFORM_CONFIG[platform]['delivery_time']
        matrix_data.append({
            'platform': platform,
            'total_cost': total_price,
            'delivery_time_mins': delivery_time
        })
    
    df_matrix = pd.DataFrame(matrix_data)
    if not df_matrix.empty:
        avg_cost = df_matrix['total_cost'].mean()
        avg_time = df_matrix['delivery_time_mins'].mean()
        
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        
        with col1:
            st.markdown("### 🟢 Low Cost Quick Delivery")
            q1 = df_matrix[(df_matrix.total_cost <= avg_cost) & (df_matrix.delivery_time_mins <= avg_time)]
            for _, row in q1.iterrows():
                st.markdown(f"**{row['platform']}**")
                st.markdown(f"₹{row['total_cost']:.2f}")
        
        with col2:
            st.markdown("### 🟡 Low Cost Standard Delivery")
            q2 = df_matrix[(df_matrix.total_cost <= avg_cost) & (df_matrix.delivery_time_mins > avg_time)]
            for _, row in q2.iterrows():
                st.markdown(f"**{row['platform']}**")
                st.markdown(f"₹{row['total_cost']:.2f}")
        
        with col3:
            st.markdown("### 🔵 Premium Quick Delivery")
            q3 = df_matrix[(df_matrix.total_cost > avg_cost) & (df_matrix.delivery_time_mins <= avg_time)]
            for _, row in q3.iterrows():
                st.markdown(f"**{row['platform']}**")
                st.markdown(f"₹{row['total_cost']:.2f}")
        
        with col4:
            st.markdown("### ⚪ Standard Delivery")
            q4 = df_matrix[(df_matrix.total_cost > avg_cost) & (df_matrix.delivery_time_mins > avg_time)]
            for _, row in q4.iterrows():
                st.markdown(f"**{row['platform']}**")
                st.markdown(f"₹{row['total_cost']:.2f}")
        
        # Best option
        if not df_matrix.empty:
            best_platform = df_matrix.loc[df_matrix['total_cost'].idxmin()]
            st.success(f"Best Option: {best_platform['platform']} - ₹{best_platform['total_cost']:.2f} (Delivery in {best_platform['delivery_time_mins']} mins)")
    
    # Display platform-wise totals with different metrics
    st.header("📊 Platform-wise Summary")
    for platform, items in cart_matrix.items():
        if items:
            total = sum(item['price'] for item in items)
            items_count = len(items)
            avg_price = total / items_count
            
            st.markdown(f"### {platform}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Cost", f"₹{total:.2f}")
            with col2:
                st.metric("Items", str(items_count))
            with col3:
                st.metric("Avg Price/Item", f"₹{avg_price:.2f}")
            
            # Display items in a table
            items_df = pd.DataFrame([{
                'Product': item['title'],
                'Price': f"₹{item['price']:.2f}",
                'Quantity': item['quantity'],
                'Delivery': item['delivery_time']
            } for item in items])
            
            st.dataframe(
                items_df.style.background_gradient(subset=['Price'], cmap='RdYlGn_r'),
                use_container_width=True
            )
            st.divider()
    # 3. Cart Summary Table
    st.subheader("🛒 Cart Summary")
    cart_data = []
    for platform, items in cart_matrix.items():
        for item in items:
            cart_data.append({
                'Platform': platform,
                'Product': item.get('title', ''),
                'Price': item.get('price', 0),
                'Quantity': item.get('quantity', '')
            })
    if cart_data:
        df = pd.DataFrame(cart_data)
        st.dataframe(
            df.style.background_gradient(subset=['Price'], cmap='RdYlGn_r'),
            use_container_width=True
        )
        st.subheader("Platform-wise Totals")
        for platform, total in platform_totals.items():
            if total > 0:
                st.metric(f"{platform} Total", f"₹{total:.2f}")

    # 4. Product Recommendations
    st.header("🌟 Recommended Products")
    display_product_list(categories.get("Quick & Budget", []), "Best Value (Quick & Budget)")
    display_product_list(categories.get("Budget", []), "Budget Choices")
    display_product_list(categories.get("Quick", []), "Premium Fast Delivery")
    display_product_list(categories.get("Standard", []), "Standard Delivery")

if __name__ == "__main__":
    render_page_3()
