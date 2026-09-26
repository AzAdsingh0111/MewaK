"""
MewaK E-Commerce Platform - Python Backend API
Built with FastAPI, SQLAlchemy/In-memory store, and Pydantic.
Connects directly to the PostgreSQL schema defined in mewak_schema.sql.

Features:
- User Authentication & Registration (Customers & Site Owner/Admin)
- Product Management (Single creation, Bulk ingestion, Browsing & Filtering)
- Shopping Cart Operations (Add to cart, View cart, Update cart)
- Order Processing (Order placement, Inventory deduction, Unique Order ID generation)
- Slack Webhook Event Dispatching (New Orders, Low Stock Alerts)
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum
import datetime
import uuid
import random
import os

# Import Slack Notifier
try:
    from slack_notifier import send_new_order_alert, send_low_stock_alert, send_status_change_alert
except ImportError:
    def send_new_order_alert(*args, **kwargs): pass
    def send_low_stock_alert(*args, **kwargs): pass
    def send_status_change_alert(*args, **kwargs): pass

# Initialize FastAPI App
app = FastAPI(
    title="MewaK E-Commerce API",
    description="Backend REST API for MewaK Marketplace Platform",
    version="1.0.0"
)

# Enable CORS for frontend clients (Streamlit, React, mobile apps)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# PYDANTIC DATA MODELS (Request & Response Schemas)
# -----------------------------------------------------------------------------

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class OrderStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

# --- User Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: UserRole = UserRole.CUSTOMER
    phone: Optional[str] = None
    shipping_address: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str]
    shipping_address: Optional[str]

# --- Product Schemas ---
class ProductCreateRequest(BaseModel):
    product_id: str = Field(..., example="MWK-P007")
    title: str
    description: Optional[str] = None
    category: str
    price: float = Field(..., gt=0)
    discount_price: Optional[float] = None
    stock_quantity: int = Field(..., ge=0)
    image_url: Optional[str] = None

class ProductResponse(BaseModel):
    product_id: str
    title: str
    description: Optional[str]
    category: str
    price: float
    discount_price: Optional[float]
    stock_quantity: int
    image_url: Optional[str]

# --- Cart Schemas ---
class CartItemRequest(BaseModel):
    user_id: str
    product_id: str
    quantity: int = Field(1, gt=0)

class CartItemResponse(BaseModel):
    cart_item_id: str
    user_id: str
    product_id: str
    product_title: str
    price: float
    quantity: int
    subtotal: float

# --- Order Schemas ---
class OrderCreateRequest(BaseModel):
    user_id: str
    shipping_address: str
    payment_method: str = "Cash on Delivery"

class OrderResponse(BaseModel):
    order_id: str
    user_id: str
    shipping_address: str
    total_amount: float
    payment_status: PaymentStatus
    order_status: OrderStatus
    created_at: str


# -----------------------------------------------------------------------------
# IN-MEMORY DATABASE STORE (Pre-seeded with initial catalog)
# -----------------------------------------------------------------------------

db_users = {
    "admin@mewak.com": {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "email": "admin@mewak.com",
        "password_hash": "admin123",
        "full_name": "Site Owner",
        "role": UserRole.ADMIN,
        "phone": "+91 9876543210",
        "shipping_address": "MewaK HQ, Tech Park, India"
    },
    "buyer@example.com": {
        "user_id": "00000000-0000-0000-0000-000000000002",
        "email": "buyer@example.com",
        "password_hash": "user123",
        "full_name": "Alex Johnson",
        "role": UserRole.CUSTOMER,
        "phone": "+91 9123456789",
        "shipping_address": "42 Market Street, Bangalore, Karnataka"
    }
}

db_products = {
    "MWK-P001": {
        "product_id": "MWK-P001",
        "title": "Premium California Almonds (Badam) - 1kg",
        "description": "Crisp, crunchy, and packed with nutrients. Direct from California orchards.",
        "category": "Dry Fruits & Nuts",
        "price": 899.0,
        "discount_price": 1200.0,
        "stock_quantity": 45,
        "image_url": "https://images.unsplash.com/photo-1508061253366-f7da158b6d46?w=400"
    },
    "MWK-P002": {
        "product_id": "MWK-P002",
        "title": "Organic Afghan Anjeer (Figs) - 500g",
        "description": "Handpicked high-grade figs rich in dietary fiber.",
        "category": "Dry Fruits & Nuts",
        "price": 649.0,
        "discount_price": 850.0,
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=400"
    },
    "MWK-P003": {
        "product_id": "MWK-P003",
        "title": "Whole Jumbo Cashews (Kaju) W240 - 1kg",
        "description": "King-sized crunchy cashews, vacuum packed for freshness.",
        "category": "Dry Fruits & Nuts",
        "price": 999.0,
        "discount_price": 1350.0,
        "stock_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1543332164-6e82f355badc?w=400"
    },
    "MWK-P004": {
        "product_id": "MWK-P004",
        "title": "Wireless Noise Cancelling Headphones",
        "description": "Deep bass, active noise cancellation, 30-hour battery life.",
        "category": "Electronics",
        "price": 2499.0,
        "discount_price": 4999.0,
        "stock_quantity": 15,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"
    }
}

db_carts = {}  # user_id -> list of cart items
db_orders = {} # order_id -> order dict


# -----------------------------------------------------------------------------
# API ROUTE HANDLERS
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "platform": "MewaK E-Commerce API",
        "status": "Online",
        "documentation": "/docs"
    }

# --- 1. USER AUTHENTICATION & MANAGEMENT ---

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest):
    if payload.email in db_users:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    new_user_id = str(uuid.uuid4())
    user_record = {
        "user_id": new_user_id,
        "email": payload.email,
        "password_hash": payload.password,
        "full_name": payload.full_name,
        "role": payload.role,
        "phone": payload.phone,
        "shipping_address": payload.shipping_address
    }
    db_users[payload.email] = user_record
    return user_record

@app.post("/api/auth/login", response_model=UserResponse)
def login_user(payload: UserLoginRequest):
    user = db_users.get(payload.email)
    if not user or user["password_hash"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user


# --- 2. PRODUCT CATALOG MANAGEMENT ---

@app.get("/api/products", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = Query(None, description="Filter by product category"),
    search: Optional[str] = Query(None, description="Search by product title or description")
):
    results = list(db_products.values())
    if category and category != "All" and category != "All Categories":
        results = [p for p in results if p["category"].lower() == category.lower()]
    if search:
        query = search.lower()
        results = [p for p in results if query in p["title"].lower() or (p.get("description") and query in p["description"].lower())]
    return results

@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: str):
    product = db_products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreateRequest):
    if payload.product_id in db_products:
        raise HTTPException(status_code=400, detail=f"Product ID '{payload.product_id}' already exists")
    
    product_dict = payload.model_dump()
    db_products[payload.product_id] = product_dict
    return product_dict

@app.post("/api/products/bulk", response_model=List[ProductResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_products(payload: List[ProductCreateRequest]):
    created_products = []
    for item in payload:
        if item.product_id in db_products:
            continue
        p_dict = item.model_dump()
        db_products[item.product_id] = p_dict
        created_products.append(p_dict)
    return created_products


# --- 3. SHOPPING CART OPERATIONS ---

@app.post("/api/cart", response_model=List[CartItemResponse])
def add_to_cart(payload: CartItemRequest):
    if payload.product_id not in db_products:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = db_products[payload.product_id]
    if product["stock_quantity"] < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient product stock")
    
    user_cart = db_carts.setdefault(payload.user_id, [])
    
    existing_item = next((item for item in user_cart if item["product_id"] == payload.product_id), None)
    if existing_item:
        existing_item["quantity"] += payload.quantity
        existing_item["subtotal"] = existing_item["quantity"] * product["price"]
    else:
        new_item = {
            "cart_item_id": str(uuid.uuid4()),
            "user_id": payload.user_id,
            "product_id": payload.product_id,
            "product_title": product["title"],
            "price": product["price"],
            "quantity": payload.quantity,
            "subtotal": payload.quantity * product["price"]
        }
        user_cart.append(new_item)
        
    return user_cart

@app.get("/api/cart/{user_id}", response_model=List[CartItemResponse])
def get_user_cart(user_id: str):
    return db_carts.get(user_id, [])


# --- 4. ORDER CHECKOUT & PROCESSING ---

@app.post("/api/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout_order(payload: OrderCreateRequest):
    user_cart = db_carts.get(payload.user_id, [])
    if not user_cart:
        raise HTTPException(status_code=400, detail="Cart is empty. Add products before checkout.")
    
    # Verify stock & calculate total
    total_amount = 0.0
    for item in user_cart:
        product = db_products.get(item["product_id"])
        if not product or product["stock_quantity"] < item["quantity"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Item '{item['product_title']}' is out of stock for requested quantity."
            )
        total_amount += item["subtotal"]
        
    # Deduct stock atomically and check for low stock alert
    for item in user_cart:
        db_products[item["product_id"]]["stock_quantity"] -= item["quantity"]
        remaining = db_products[item["product_id"]]["stock_quantity"]
        if remaining <= 10:
            send_low_stock_alert(item["product_title"], item["product_id"], remaining)
        
    # Generate Order ID
    order_id = f"MWK-{datetime.datetime.now().year}-{random.randint(1000, 9999)}"
    
    order_record = {
        "order_id": order_id,
        "user_id": payload.user_id,
        "shipping_address": payload.shipping_address,
        "total_amount": round(total_amount, 2),
        "payment_status": PaymentStatus.PAID,
        "order_status": OrderStatus.CONFIRMED,
        "created_at": datetime.datetime.now().isoformat()
    }
    
    db_orders[order_id] = order_record
    
    # Find user email for notification
    user_email = "customer@mewak.com"
    for email, user in db_users.items():
        if user["user_id"] == payload.user_id:
            user_email = email
            break
            
    # Trigger Real-Time Slack Webhook
    send_new_order_alert(
        order_id=order_id,
        user_email=user_email,
        total_amount=round(total_amount, 2),
        shipping_address=payload.shipping_address,
        items_count=len(user_cart)
    )

    # Clear cart after successful order placement
    db_carts[payload.user_id] = []
    
    return order_record

@app.get("/api/orders/user/{user_id}", response_model=List[OrderResponse])
def get_user_orders(user_id: str):
    return [order for order in db_orders.values() if order["user_id"] == user_id]
