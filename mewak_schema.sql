-- =============================================================================
-- MewaK E-Commerce Platform Database Schema
-- Target: PostgreSQL 14+ / Supabase / Amazon RDS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ENUMS
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'CUSTOMER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE payment_status_enum AS ENUM ('PENDING', 'PAID', 'FAILED', 'REFUNDED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE order_status_enum AS ENUM ('CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role_enum DEFAULT 'CUSTOMER',
    phone VARCHAR(50),
    shipping_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. PRODUCTS CATALOG TABLE
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    discount_price NUMERIC(10, 2) CHECK (discount_price >= 0),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_title ON products(title);

-- 4. SHOPPING CART ITEMS TABLE
CREATE TABLE IF NOT EXISTS cart_items (
    cart_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, product_id)
);

-- 5. ORDERS TABLE
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    shipping_address TEXT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount >= 0),
    payment_status payment_status_enum DEFAULT 'PAID',
    order_status order_status_enum DEFAULT 'CONFIRMED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);

-- 6. ORDER ITEMS TABLE
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    subtotal NUMERIC(10, 2) NOT NULL CHECK (subtotal >= 0)
);

-- SEED INITIAL DATA
INSERT INTO users (user_id, email, password_hash, full_name, role, phone, shipping_address)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'admin@mewak.com', 'admin123', 'Site Owner', 'ADMIN', '+91 9876543210', 'MewaK HQ, Tech Park, India'),
    ('00000000-0000-0000-0000-000000000002', 'buyer@example.com', 'user123', 'Alex Johnson', 'CUSTOMER', '+91 9123456789', '42 Market Street, Bangalore, Karnataka')
ON CONFLICT (email) DO NOTHING;

INSERT INTO products (product_id, title, description, category, price, discount_price, stock_quantity, image_url)
VALUES 
    ('MWK-P001', 'Premium California Almonds (Badam) - 1kg', 'Crisp, crunchy, and packed with nutrients. Direct from California orchards.', 'Dry Fruits & Nuts', 899.00, 1200.00, 45, 'https://images.unsplash.com/photo-1508061253366-f7da158b6d46?w=400'),
    ('MWK-P002', 'Organic Afghan Anjeer (Figs) - 500g', 'Handpicked high-grade figs rich in dietary fiber.', 'Dry Fruits & Nuts', 649.00, 850.00, 30, 'https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=400'),
    ('MWK-P003', 'Whole Jumbo Cashews (Kaju) W240 - 1kg', 'King-sized crunchy cashews, vacuum packed for freshness.', 'Dry Fruits & Nuts', 999.00, 1350.00, 60, 'https://images.unsplash.com/photo-1543332164-6e82f355badc?w=400'),
    ('MWK-P004', 'Wireless Noise Cancelling Headphones', 'Deep bass, active noise cancellation, 30-hour battery life.', 'Electronics', 2499.00, 4999.00, 15, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400')
ON CONFLICT (product_id) DO NOTHING;
