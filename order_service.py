#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
DelyBot™ X - Order Service Microservice
═══════════════════════════════════════════════════════════════════════════

Microservice for order management

Company: INGENIOUSBLUEPRINTS PRIVATE LIMITED
Port: 8001
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime
import uvicorn
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = "./order_service.db"

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            delivery_lat REAL NOT NULL,
            delivery_lon REAL NOT NULL,
            product_name TEXT NOT NULL,
            product_weight REAL NOT NULL,
            delivery_code TEXT NOT NULL,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL,
            assigned_drone_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class GPSLocation(BaseModel):
    latitude: float
    longitude: float
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class CreateOrderRequest(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: EmailStr
    delivery_address: str
    delivery_location: GPSLocation
    product_name: str
    product_weight: float
    priority: int = 1
    
    @validator('customer_phone')
    def validate_phone(cls, v):
        # Indian phone number validation
        pattern = re.compile(r'^[6-9]\d{9}$')
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not pattern.match(cleaned):
            raise ValueError('Invalid Indian phone number')
        return cleaned
    
    @validator('product_weight')
    def validate_weight(cls, v):
        if v <= 0 or v > 5.0:
            raise ValueError('Weight must be between 0 and 5 kg')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('Priority must be 1 (normal), 2 (high), or 3 (urgent)')
        return v

class OrderResponse(BaseModel):
    order_id: str
    customer_name: str
    customer_phone: str
    customer_email: str
    delivery_address: str
    delivery_lat: float
    delivery_lon: float
    product_name: str
    product_weight: float
    delivery_code: str
    status: str
    priority: int
    assigned_drone_id: Optional[str]
    created_at: str
    updated_at: str

class UpdateOrderStatusRequest(BaseModel):
    status: str
    assigned_drone_id: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="DelyBot™ X - Order Service",
    description="Order management microservice for autonomous drone delivery",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def generate_order_id() -> str:
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random = secrets.token_hex(3).upper()
    return f"ORD{timestamp}{random}"

def generate_delivery_code() -> str:
    """Generate secure 8-character delivery code"""
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return ''.join(secrets.choice(alphabet) for _ in range(8))

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Order Service",
        "version": "2.0.0",
        "company": "INGENIOUSBLUEPRINTS PRIVATE LIMITED",
        "status": "running"
    }

@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order_req: CreateOrderRequest):
    """
    Create new delivery order
    
    - Validates customer information
    - Generates unique order ID
    - Creates secure delivery code
    - Stores in database
    """
    # Generate IDs
    order_id = generate_order_id()
    delivery_code = generate_delivery_code()
    
    # Current timestamp
    now = datetime.now().isoformat()
    
    # Insert into database
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            order_req.customer_name,
            order_req.customer_phone,
            order_req.customer_email,
            order_req.delivery_address,
            order_req.delivery_location.latitude,
            order_req.delivery_location.longitude,
            order_req.product_name,
            order_req.product_weight,
            delivery_code,
            "pending",
            order_req.priority,
            None,
            now,
            now
        ))
        
        conn.commit()
        
        # Return created order
        return OrderResponse(
            order_id=order_id,
            customer_name=order_req.customer_name,
            customer_phone=order_req.customer_phone,
            customer_email=order_req.customer_email,
            delivery_address=order_req.delivery_address,
            delivery_lat=order_req.delivery_location.latitude,
            delivery_lon=order_req.delivery_location.longitude,
            product_name=order_req.product_name,
            product_weight=order_req.product_weight,
            delivery_code=delivery_code,
            status="pending",
            priority=order_req.priority,
            assigned_drone_id=None,
            created_at=now,
            updated_at=now
        )
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    finally:
        conn.close()

@app.get("/orders", response_model=List[OrderResponse])
async def list_orders(status: Optional[str] = None, limit: int = 100):
    """
    List all orders
    
    - Optional filter by status
    - Returns up to 100 orders
    """
    conn = get_db()
    cursor = conn.cursor()
    
    if status:
        cursor.execute(
            "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    orders = []
    for row in rows:
        orders.append(OrderResponse(
            order_id=row['order_id'],
            customer_name=row['customer_name'],
            customer_phone=row['customer_phone'],
            customer_email=row['customer_email'],
            delivery_address=row['delivery_address'],
            delivery_lat=row['delivery_lat'],
            delivery_lon=row['delivery_lon'],
            product_name=row['product_name'],
            product_weight=row['product_weight'],
            delivery_code=row['delivery_code'],
            status=row['status'],
            priority=row['priority'],
            assigned_drone_id=row['assigned_drone_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ))
    
    return orders

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get order by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(
        order_id=row['order_id'],
        customer_name=row['customer_name'],
        customer_phone=row['customer_phone'],
        customer_email=row['customer_email'],
        delivery_address=row['delivery_address'],
        delivery_lat=row['delivery_lat'],
        delivery_lon=row['delivery_lon'],
        product_name=row['product_name'],
        product_weight=row['product_weight'],
        delivery_code=row['delivery_code'],
        status=row['status'],
        priority=row['priority'],
        assigned_drone_id=row['assigned_drone_id'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )

@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, update_req: UpdateOrderStatusRequest):
    """
    Update order status
    
    Used by Drone Service to update order progress
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if order exists
    cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update
    now = datetime.now().isoformat()
    
    if update_req.assigned_drone_id:
        cursor.execute("""
            UPDATE orders 
            SET status = ?, assigned_drone_id = ?, updated_at = ?
            WHERE order_id = ?
        """, (update_req.status, update_req.assigned_drone_id, now, order_id))
    else:
        cursor.execute("""
            UPDATE orders 
            SET status = ?, updated_at = ?
            WHERE order_id = ?
        """, (update_req.status, now, order_id))
    
    conn.commit()
    conn.close()
    
    return {"order_id": order_id, "status": update_req.status, "updated_at": now}

@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel order (soft delete - sets status to cancelled)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT order_id, status FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")
    
    if row['status'] in ['in_transit', 'delivered']:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot cancel order in this status")
    
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE orders SET status = 'cancelled', updated_at = ? WHERE order_id = ?
    """, (now, order_id))
    
    conn.commit()
    conn.close()
    
    return {"order_id": order_id, "status": "cancelled"}

@app.get("/stats")
async def get_stats():
    """Get order statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total orders
    cursor.execute("SELECT COUNT(*) as total FROM orders")
    total = cursor.fetchone()['total']
    
    # By status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM orders 
        GROUP BY status
    """)
    by_status = {row['status']: row['count'] for row in cursor.fetchall()}
    
    # Today's orders
    today = datetime.now().date().isoformat()
    cursor.execute("""
        SELECT COUNT(*) as today_count 
        FROM orders 
        WHERE DATE(created_at) = ?
    """, (today,))
    today_count = cursor.fetchone()['today_count']
    
    conn.close()
    
    return {
        "total_orders": total,
        "orders_by_status": by_status,
        "today_orders": today_count
    }

# ═══════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "order_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
