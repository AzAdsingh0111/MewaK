"""
MewaK E-Commerce Platform Application (v2)
Connected Streamlit Frontend + FastAPI Backend Integration.

Features:
- Live REST API Connection to FastAPI Backend (configured via API_BASE_URL env or UI)
- Fallback / Standalone Mode if API Server is offline
- Real-time Product Catalog Ingestion & Browsing
- User Auth & Role Management via API
- Persistent Shopping Cart & Atomic Order Checkout via Backend
- Owner / Admin Control Center for inventory and bulk CSV upload
"""

import streamlit as st
import pandas as pd
import requests
import datetime
import random
import io
import json
import os

import streamlit as st
import pandas as pd
import requests
import datetime
import random
import io
import json
import os
import base64

# Page Configuration
st.set_page_config(
    page_title="MewaK - Premium Dry Fruits & Marketplace",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to get base64 encoded image
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

logo_b64 = get_base64_image("assets/mewak_logo.png")

# Custom CSS for MewaK Luxury Branding
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    .stApp {
        background-color: #F8F5EE;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .mewak-header-card {
        background: linear-gradient(135deg, #1A120B 0%, #2B1B17 100%);
        padding: 16px 28px;
        color: white;
        border-radius: 14px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 6px 20px rgba(26, 18, 11, 0.15);
        border: 1px solid #D4AF37;
    }
    .mewak-logo-container {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .mewak-logo-img {
        height: 52px;
        border-radius: 6px;
        background: #FDFBF7;
        padding: 4px 10px;
    }
    .mewak-logo-text {
        font-family: 'Cinzel', serif;
        font-size: 28px;
        font-weight: 800;
        color: #ECC86A;
        letter-spacing: 2px;
    }
    .mewak-tagline {
        font-size: 13px;
        color: #D6C7B2;
        letter-spacing: 0.5px;
    }
    .status-online {
        background: rgba(46, 125, 50, 0.18);
        color: #81C784;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #66BB6A;
    }
    .status-offline {
        background: rgba(230, 81, 0, 0.18);
        color: #FFB74D;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #FFA726;
    }
    .price-tag {
        font-size: 20px;
        font-weight: 800;
        color: #2B1B17;
    }
    .original-price {
        font-size: 14px;
        text-decoration: line-through;
        color: #8D7B68;
        margin-left: 8px;
    }
    .discount-badge {
        font-size: 12px;
        font-weight: 700;
        color: #2E7D32;
        background-color: #E8F5E9;
        padding: 3px 8px;
        border-radius: 4px;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration - Default from env or localhost
DEFAULT_API_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
if "api_base_url" not in st.session_state:
    st.session_state["api_base_url"] = DEFAULT_API_URL

API_BASE_URL = st.session_state["api_base_url"]

# Helper Functions for FastAPI Integration
def check_api_connection():
    try:
        response = requests.get(f"{st.session_state['api_base_url']}/", timeout=1.5)
        if response.status_code == 200:
            return True, response.json()
    except Exception:
        pass
    return False, None

def api_login(email, password):
    try:
        res = requests.post(f"{st.session_state['api_base_url']}/api/auth/login", json={"email": email, "password": password}, timeout=2)
        if res.status_code == 200:
            return True, res.json()
        return False, res.json().get("detail", "Login failed")
    except Exception as e:
        return False, f"API Connection Error: {str(e)}"

def api_register(email, password, full_name, role="CUSTOMER", phone=None, address=None):
    try:
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
            "phone": phone,
            "shipping_address": address
        }
        res = requests.post(f"{st.session_state['api_base_url']}/api/auth/register", json=payload, timeout=2)
        if res.status_code == 201:
            return True, res.json()
        return False, res.json().get("detail", "Registration failed")
    except Exception as e:
        return False, f"API Connection Error: {str(e)}"

def api_get_products(category=None, search=None):
    try:
        params = {}
        if category and category != "All Categories":
            params["category"] = category
        if search:
            params["search"] = search
        res = requests.get(f"{st.session_state['api_base_url']}/api/products", params=params, timeout=2)
        if res.status_code == 200:
            return True, res.json()
    except Exception:
        pass
    return False, []

def api_create_product(product_dict):
    try:
        res = requests.post(f"{st.session_state['api_base_url']}/api/products", json=product_dict, timeout=2)
        if res.status_code == 201:
            return True, res.json()
        return False, res.json().get("detail", "Failed to create product")
    except Exception as e:
        return False, str(e)

def api_bulk_create_products(products_list):
    try:
        res = requests.post(f"{st.session_state['api_base_url']}/api/products/bulk", json=products_list, timeout=3)
        if res.status_code == 201:
            return True, res.json()
        return False, res.json().get("detail", "Bulk creation failed")
    except Exception as e:
        return False, str(e)

def api_add_to_cart(user_id, product_id, quantity=1):
    try:
        payload = {"user_id": user_id, "product_id": product_id, "quantity": quantity}
        res = requests.post(f"{st.session_state['api_base_url']}/api/cart", json=payload, timeout=2)
        if res.status_code == 200:
            return True, res.json()
        return False, res.json().get("detail", "Cart update failed")
    except Exception as e:
        return False, str(e)

def api_get_cart(user_id):
    try:
        res = requests.get(f"{st.session_state['api_base_url']}/api/cart/{user_id}", timeout=2)
        if res.status_code == 200:
            return True, res.json()
    except Exception:
        pass
    return False, []

def api_checkout_order(user_id, address):
    try:
        payload = {"user_id": user_id, "shipping_address": address}
        res = requests.post(f"{st.session_state['api_base_url']}/api/orders", json=payload, timeout=3)
        if res.status_code == 201:
            return True, res.json()
        return False, res.json().get("detail", "Checkout failed")
    except Exception as e:
        return False, str(e)

def api_get_user_orders(user_id):
    try:
        res = requests.get(f"{st.session_state['api_base_url']}/api/orders/user/{user_id}", timeout=2)
        if res.status_code == 200:
            return True, res.json()
    except Exception:
        pass
    return False, []


# Check API Connectivity
is_api_online, api_meta = check_api_connection()

# Initialize Fallback / Local Session State
if "users" not in st.session_state:
    st.session_state["users"] = {
        "admin@mewak.com": {"user_id": "00000000-0000-0000-0000-000000000001", "name": "Site Owner", "password": "admin", "role": "Owner", "phone": "+91 9876543210", "address": "MewaK HQ, Tech Park, India"},
        "buyer@example.com": {"user_id": "00000000-0000-0000-0000-000000000002", "name": "Alex Johnson", "password": "user123", "role": "Buyer", "phone": "+91 9123456789", "address": "42 Market Street, Bangalore, Karnataka"}
    }

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

if "local_products" not in st.session_state:
    st.session_state["local_products"] = [
        {"product_id": "MWK-P001", "title": "Premium California Almonds (Badam) - 1kg", "category": "Dry Fruits & Nuts", "price": 899.0, "discount_price": 1200.0, "stock_quantity": 45, "image_url": "https://images.unsplash.com/photo-1508061253366-f7da158b6d46?w=400", "description": "Crisp, crunchy, and packed with nutrients."},
        {"product_id": "MWK-P002", "title": "Organic Afghan Anjeer (Figs) - 500g", "category": "Dry Fruits & Nuts", "price": 649.0, "discount_price": 850.0, "stock_quantity": 30, "image_url": "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=400", "description": "Handpicked high-grade figs rich in dietary fiber."},
        {"product_id": "MWK-P003", "title": "Whole Jumbo Cashews (Kaju) W240 - 1kg", "category": "Dry Fruits & Nuts", "price": 999.0, "discount_price": 1350.0, "stock_quantity": 60, "image_url": "https://images.unsplash.com/photo-1543332164-6e82f355badc?w=400", "description": "King-sized crunchy cashews."},
        {"product_id": "MWK-P004", "title": "Wireless Noise Cancelling Headphones", "category": "Electronics", "price": 2499.0, "discount_price": 4999.0, "stock_quantity": 15, "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400", "description": "Deep bass, 30-hour battery life."}
    ]

if "local_cart" not in st.session_state:
    st.session_state["local_cart"] = []

if "local_orders" not in st.session_state:
    st.session_state["local_orders"] = []


# Header Banner with Logo
logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="mewak-logo-img" alt="MewaK Logo" />' if logo_b64 else '<span class="mewak-logo-text">MEWA<sup>🍃K</sup></span>'

st.markdown(f"""
<div class="mewak-header-card">
    <div class="mewak-logo-container">
        {logo_html}
        <div>
            <div class="mewak-tagline">Premium Dry Fruits, Nuts & Artisanal Marketplace</div>
        </div>
    </div>
    <div>
        {'<span class="status-online">🟢 FastAPI Backend Online</span>' if is_api_online else '<span class="status-offline">🟡 Standalone Session Mode</span>'}
    </div>
</div>
""", unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align: center; margin-bottom: 12px;"><img src="data:image/png;base64,{logo_b64}" style="max-width: 180px; background: white; padding: 6px 12px; border-radius: 8px; border: 1px solid #D4AF37;" /></div>', unsafe_allow_html=True)
    else:
        st.header("🍃 MewaK")

    st.markdown("<h4 style='color: #2B1B17; margin-top: 0;'>⚙️ Navigation & Settings</h4>", unsafe_allow_html=True)
    
    # API URL Setting
    with st.expander("🌐 Backend API Connection"):
        new_api_url = st.text_input("FastAPI Base URL", st.session_state["api_base_url"])
        if new_api_url != st.session_state["api_base_url"]:
            st.session_state["api_base_url"] = new_api_url
            st.rerun()
            
        if is_api_online:
            st.success(f"Connected: `{st.session_state['api_base_url']}`")
            st.caption(f"Swagger API Docs: [{st.session_state['api_base_url']}/docs]({st.session_state['api_base_url']}/docs)")
        else:
            st.warning("FastAPI backend is unreachable. Running in standalone fallback mode.")

    st.divider()

    # User Auth Profile Header
    if st.session_state["current_user"]:
        user_info = st.session_state["users"][st.session_state["current_user"]]
        st.success(f"👤 Logged in: **{user_info.get('full_name', user_info.get('name', 'User'))}**")
        st.caption(f"Role: **{user_info.get('role', 'Customer')}**")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["current_user"] = None
            st.rerun()
    else:
        st.info("👋 Welcome! Please sign in to place orders.")

    st.divider()

    menu_options = ["🏬 Storefront", "🛒 Shopping Cart", "📦 My Orders"]
    if st.session_state["current_user"]:
        user_role = str(st.session_state["users"][st.session_state["current_user"]].get("role", "")).upper()
        if user_role in ["OWNER", "ADMIN"]:
            menu_options.append("👑 Owner / Admin Portal")
        menu_options.append("👤 User Profile")
    else:
        menu_options.append("🔑 Login / Signup")

    choice = st.radio("Go to:", menu_options)


# -----------------------------------------------------------------------------
# VIEW 1: STOREFRONT
# -----------------------------------------------------------------------------
if choice == "🏬 Storefront":
    st.title("🛒 Explore Products on MewaK")

    col_search, col_cat, col_sort = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Search products by title or description...", "")
    
    # Fetch Products from API or Local State
    if is_api_online:
        success, products_list = api_get_products(search=search_query if search_query else None)
        if not success:
            products_list = st.session_state["local_products"]
    else:
        products_list = st.session_state["local_products"]
        if search_query:
            products_list = [p for p in products_list if search_query.lower() in p["title"].lower()]

    categories = ["All Categories"] + sorted(list(set([p["category"] for p in products_list if "category" in p])))
    
    with col_cat:
        selected_cat = st.selectbox("Category", categories)
    with col_sort:
        sort_by = st.selectbox("Sort By", ["Featured", "Price: Low to High", "Price: High to Low"])

    if selected_cat != "All Categories":
        products_list = [p for p in products_list if p.get("category") == selected_cat]

    if sort_by == "Price: Low to High":
        products_list = sorted(products_list, key=lambda x: x.get("price", 0))
    elif sort_by == "Price: High to Low":
        products_list = sorted(products_list, key=lambda x: x.get("price", 0), reverse=True)

    st.caption(f"Showing **{len(products_list)}** products")
    st.divider()

    cols = st.columns(3)
    for idx, p in enumerate(products_list):
        with cols[idx % 3]:
            img = p.get("image_url") or "https://via.placeholder.com/300?text=MewaK+Product"
            st.image(img, use_container_width=True)
            st.subheader(p.get("title", "Product Title"))
            st.caption(f"🏷️ {p.get('category', 'General')}")
            
            price = p.get("price", 0.0)
            orig_price = p.get("discount_price") or (price * 1.25)
            discount = int(((orig_price - price) / orig_price) * 100) if orig_price > price else 0

            st.markdown(f"""
            <span class="price-tag">₹{price:,.2f}</span>
            <span class="original-price">₹{orig_price:,.2f}</span>
            <span class="discount-badge">{discount}% OFF</span>
            """, unsafe_allow_html=True)

            st.write(p.get("description", ""))
            stock = p.get("stock_quantity", 0)

            if stock > 0:
                st.write(f"🟢 **{stock}** units in stock")
                if st.button("➕ Add to Cart", key=f"btn_{p['product_id']}", use_container_width=True):
                    if not st.session_state["current_user"]:
                        st.warning("Please log in first to add items to your cart.")
                    else:
                        user_id = st.session_state["users"][st.session_state["current_user"]].get("user_id", "00000000-0000-0000-0000-000000000002")
                        if is_api_online:
                            ok, res = api_add_to_cart(user_id, p["product_id"], 1)
                            if ok:
                                st.toast(f"Added '{p['title']}' to cart!", icon="🛒")
                            else:
                                st.error(f"Failed: {res}")
                        else:
                            # Local fallback cart
                            existing = next((i for i in st.session_state["local_cart"] if i["product_id"] == p["product_id"]), None)
                            if existing:
                                existing["quantity"] += 1
                                existing["subtotal"] = existing["quantity"] * price
                            else:
                                st.session_state["local_cart"].append({
                                    "cart_item_id": f"item_{random.randint(100, 999)}",
                                    "product_id": p["product_id"],
                                    "product_title": p["title"],
                                    "price": price,
                                    "quantity": 1,
                                    "subtotal": price
                                })
                            st.toast(f"Added '{p['title']}' to local cart!", icon="🛒")
            else:
                st.error("🔴 Out of Stock")
            st.markdown("---")


# -----------------------------------------------------------------------------
# VIEW 2: SHOPPING CART
# -----------------------------------------------------------------------------
elif choice == "🛒 Shopping Cart":
    st.title("🛒 Your Shopping Cart")

    if not st.session_state["current_user"]:
        st.info("Please log in to view your shopping cart and complete checkout.")
    else:
        user_info = st.session_state["users"][st.session_state["current_user"]]
        user_id = user_info.get("user_id", "00000000-0000-0000-0000-000000000002")

        if is_api_online:
            _, cart_items = api_get_cart(user_id)
        else:
            cart_items = st.session_state["local_cart"]

        if not cart_items:
            st.info("Your shopping cart is currently empty. Explore the storefront to add items!")
        else:
            total = 0.0
            for item in cart_items:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{item.get('product_title')}**")
                    st.caption(f"Product ID: `{item.get('product_id')}`")
                with c2:
                    st.write(f"Qty: **{item.get('quantity')}**")
                with c3:
                    sub = item.get("subtotal", 0.0)
                    total += sub
                    st.markdown(f"**₹{sub:,.2f}**")
                st.divider()

            st.markdown(f"### Total Amount Payable: **₹{total:,.2f}**")

            with st.form("checkout_form"):
                st.markdown("### 🚚 Delivery & Shipping Details")
                addr = st.text_area("Shipping Address", user_info.get("shipping_address", user_info.get("address", "")))
                payment_method = st.radio("Select Payment Method", ["Instant UPI / Pay (Slack Verified)", "Cash on Delivery", "Credit / Debit Card"])
                
                if st.form_submit_button("💳 Place Order Now", use_container_width=True):
                    if not addr.strip():
                        st.error("Please provide a valid shipping address.")
                    else:
                        if is_api_online:
                            ok, res = api_checkout_order(user_id, addr)
                            if ok:
                                st.balloons()
                                st.success(f"🎉 Order Placed Successfully via FastAPI & Alerted to Slack! Order ID: **{res['order_id']}**")
                            else:
                                st.error(f"Checkout Error: {res}")
                        else:
                            # Local checkout fallback
                            order_id = f"MWK-2026-{random.randint(1000, 9999)}"
                            st.session_state["local_orders"].append({
                                "order_id": order_id,
                                "total_amount": total,
                                "shipping_address": addr,
                                "status": "CONFIRMED",
                                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            st.session_state["local_cart"] = []
                            st.balloons()
                            st.success(f"🎉 Order Placed Successfully! Order ID: **{order_id}**")


# -----------------------------------------------------------------------------
# VIEW 3: MY ORDERS
# -----------------------------------------------------------------------------
elif choice == "📦 My Orders":
    st.title("📦 Order History & Fulfillment Tracking")

    if not st.session_state["current_user"]:
        st.info("Please log in to view your order history.")
    else:
        user_id = st.session_state["users"][st.session_state["current_user"]].get("user_id", "00000000-0000-0000-0000-000000000002")
        if is_api_online:
            _, orders = api_get_user_orders(user_id)
        else:
            orders = st.session_state["local_orders"]

        if not orders:
            st.info("You haven't placed any orders yet.")
        else:
            for ord_rec in reversed(orders):
                with st.expander(f"📦 Order ID: {ord_rec.get('order_id')} | Total: ₹{ord_rec.get('total_amount'):,.2f}"):
                    st.write(f"**Order Status**: 🟢 `{ord_rec.get('order_status', ord_rec.get('status', 'CONFIRMED'))}`")
                    st.write(f"**Shipping Address**: {ord_rec.get('shipping_address')}")
                    st.write(f"**Date**: {ord_rec.get('created_at')}")


# -----------------------------------------------------------------------------
# VIEW 4: OWNER / ADMIN PORTAL
# -----------------------------------------------------------------------------
elif choice == "👑 Owner / Admin Portal":
    st.title("👑 MewaK Owner & Admin Control Center")

    tab1, tab2 = st.tabs(["➕ Add Single Product", "📂 Bulk CSV Ingestion"])

    with tab1:
        st.subheader("Add Single Item to Inventory")
        with st.form("single_prod_form"):
            c1, c2 = st.columns(2)
            with c1:
                p_id = st.text_input("Product ID", f"MWK-P{random.randint(100, 999)}")
                p_title = st.text_input("Product Title", "Premium Organic Walnuts - 500g")
                p_cat = st.selectbox("Category", ["Dry Fruits & Nuts", "Electronics", "Grocery & Staples", "Fashion"])
                p_price = st.number_input("Selling Price (₹)", min_value=1.0, value=599.0)
            with c2:
                p_orig = st.number_input("Original/MRP Price (₹)", min_value=1.0, value=799.0)
                p_stock = st.number_input("Initial Stock Quantity", min_value=1, value=50)
                p_img = st.text_input("Image URL", "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?w=400")
                p_desc = st.text_area("Product Description", "Freshly sourced high quality walnuts.")

            if st.form_submit_button("🚀 Add Product to Catalog", use_container_width=True):
                prod_data = {
                    "product_id": p_id,
                    "title": p_title,
                    "category": p_cat,
                    "price": float(p_price),
                    "discount_price": float(p_orig),
                    "stock_quantity": int(p_stock),
                    "image_url": p_img,
                    "description": p_desc
                }
                if is_api_online:
                    ok, res = api_create_product(prod_data)
                    if ok:
                        st.success(f"Product '{p_title}' ingested into FastAPI backend database!")
                    else:
                        st.error(f"API Error: {res}")
                else:
                    st.session_state["local_products"].append(prod_data)
                    st.success(f"Product '{p_title}' added to local session catalog!")

    with tab2:
        st.subheader("Bulk Ingest Products via CSV File")
        uploaded_csv = st.file_uploader("Upload CSV Product File", type=["csv"])
        
        # Downloadable Template
        template_data = pd.DataFrame([
            {
                "product_id": "MWK-P101",
                "title": "Raw Pistachios (Pista) - 250g",
                "category": "Dry Fruits & Nuts",
                "price": 450.0,
                "discount_price": 600.0,
                "stock_quantity": 100,
                "image_url": "https://images.unsplash.com/photo-1543332164-6e82f355badc?w=400",
                "description": "Premium unsalted raw pistachios."
            }
        ])
        st.download_button("📥 Download CSV Template", template_data.to_csv(index=False), "mewak_bulk_template.csv", "text/csv")

        if uploaded_csv:
            df = pd.read_csv(uploaded_csv)
            st.dataframe(df)
            if st.button("⚡ Process Bulk Upload", use_container_width=True):
                items = df.to_dict(orient="records")
                if is_api_online:
                    ok, res = api_bulk_create_products(items)
                    if ok:
                        st.success(f"Successfully uploaded {len(res)} products to FastAPI backend!")
                    else:
                        st.error(f"Bulk Upload Error: {res}")
                else:
                    st.session_state["local_products"].extend(items)
                    st.success(f"Successfully loaded {len(items)} items into local catalog!")


# -----------------------------------------------------------------------------
# VIEW 5: USER PROFILE
# -----------------------------------------------------------------------------
elif choice == "👤 User Profile":
    st.title("👤 User Account Profile")
    if st.session_state["current_user"]:
        user_info = st.session_state["users"][st.session_state["current_user"]]
        st.json(user_info)


# -----------------------------------------------------------------------------
# VIEW 6: LOGIN / SIGNUP
# -----------------------------------------------------------------------------
elif choice == "🔑 Login / Signup":
    st.title("🔑 MewaK User Portal")

    t1, t2 = st.tabs(["Login", "Create Account"])

    with t1:
        with st.form("login_form"):
            email_in = st.text_input("Email Address", "buyer@example.com")
            pass_in = st.text_input("Password", "user123", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                if is_api_online:
                    ok, res = api_login(email_in, pass_in)
                    if ok:
                        st.session_state["users"][email_in] = res
                        st.session_state["current_user"] = email_in
                        st.success(f"Welcome back, {res.get('full_name', 'User')}!")
                        st.rerun()
                    else:
                        st.error(f"Login Failed: {res}")
                else:
                    if email_in in st.session_state["users"] and st.session_state["users"][email_in]["password"] == pass_in:
                        st.session_state["current_user"] = email_in
                        st.success("Log in successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

    with t2:
        with st.form("signup_form"):
            r_name = st.text_input("Full Name")
            r_email = st.text_input("Email")
            r_pass = st.text_input("Password", type="password")
            r_role = st.selectbox("Role", ["Buyer", "Owner"])
            r_phone = st.text_input("Phone Number")
            r_addr = st.text_area("Default Address")
            if st.form_submit_button("Create Account", use_container_width=True):
                role_enum = "ADMIN" if r_role == "Owner" else "CUSTOMER"
                if is_api_online:
                    ok, res = api_register(r_email, r_pass, r_name, role_enum, r_phone, r_addr)
                    if ok:
                        st.success("Account created successfully! You can now log in.")
                    else:
                        st.error(f"Registration Error: {res}")
                else:
                    st.session_state["users"][r_email] = {
                        "user_id": f"usr_{random.randint(100, 999)}",
                        "full_name": r_name, "password": r_pass, "role": role_enum, "phone": r_phone, "shipping_address": r_addr
                    }
                    st.success("Account created in local session! You can now log in.")
