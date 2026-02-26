#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
DelyBot™ X - Drone Control Service Microservice
═══════════════════════════════════════════════════════════════════════════

Microservice for drone fleet management and control

Company: INGENIOUSBLUEPRINTS PRIVATE LIMITED
Port: 8002
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
import uvicorn
import sqlite3
import httpx
from contextlib import asynccontextmanager

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = "./drone_service.db"
ORDER_SERVICE_URL = "http://order-service:8001"  # Docker network name

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drones (
            drone_id TEXT PRIMARY KEY,
            model TEXT NOT NULL,
            status TEXT NOT NULL,
            battery_level REAL NOT NULL,
            current_lat REAL NOT NULL,
            current_lon REAL NOT NULL,
            current_alt REAL NOT NULL,
            assigned_order_id TEXT,
            total_flights INTEGER NOT NULL,
            total_distance REAL NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            mission_id TEXT PRIMARY KEY,
            drone_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            status TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            battery_used REAL,
            distance_km REAL
        )
    """)
    
    conn.commit()
    conn.close()

def seed_drones():
    """Seed initial drones"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if drones exist
    cursor.execute("SELECT COUNT(*) as count FROM drones")
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return
    
    # Add 3 initial drones
    drones = [
        ("DRONE_001", "JROS-X1", "idle", 100.0, 23.3441, 85.3096, 0.0, None, 0, 0.0),
        ("DRONE_002", "JROS-X1", "idle", 95.0, 23.3441, 85.3096, 0.0, None, 0, 0.0),
        ("DRONE_003", "JROS-X1", "idle", 98.0, 23.3441, 85.3096, 0.0, None, 0, 0.0),
    ]
    
    now = datetime.now().isoformat()
    
    for drone_id, model, status, battery, lat, lon, alt, order_id, flights, distance in drones:
        cursor.execute("""
            INSERT INTO drones VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (drone_id, model, status, battery, lat, lon, alt, order_id, flights, distance, now))
    
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class DroneResponse(BaseModel):
    drone_id: str
    model: str
    status: str
    battery_level: float
    current_lat: float
    current_lon: float
    current_alt: float
    assigned_order_id: Optional[str]
    total_flights: int
    total_distance: float
    last_updated: str

class UpdateDroneTelemetry(BaseModel):
    latitude: float
    longitude: float
    altitude: float
    battery_level: float
    
    @validator('battery_level')
    def validate_battery(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Battery must be between 0 and 100')
        return v

class AssignMissionRequest(BaseModel):
    order_id: str

class MissionResponse(BaseModel):
    mission_id: str
    drone_id: str
    order_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    battery_used: Optional[float]
    distance_km: Optional[float]

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    seed_drones()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="DelyBot™ X - Drone Control Service",
    description="Drone fleet management and control microservice",
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

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate Haversine distance in km"""
    import math
    
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Drone Control Service",
        "version": "2.0.0",
        "company": "INGENIOUSBLUEPRINTS PRIVATE LIMITED",
        "status": "running"
    }

@app.get("/drones", response_model=List[DroneResponse])
async def list_drones(status: Optional[str] = None):
    """
    List all drones
    
    - Optional filter by status
    """
    conn = get_db()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("SELECT * FROM drones WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT * FROM drones")
    
    rows = cursor.fetchall()
    conn.close()
    
    drones = []
    for row in rows:
        drones.append(DroneResponse(
            drone_id=row['drone_id'],
            model=row['model'],
            status=row['status'],
            battery_level=row['battery_level'],
            current_lat=row['current_lat'],
            current_lon=row['current_lon'],
            current_alt=row['current_alt'],
            assigned_order_id=row['assigned_order_id'],
            total_flights=row['total_flights'],
            total_distance=row['total_distance'],
            last_updated=row['last_updated']
        ))
    
    return drones

@app.get("/drones/{drone_id}", response_model=DroneResponse)
async def get_drone(drone_id: str):
    """Get drone by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM drones WHERE drone_id = ?", (drone_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    return DroneResponse(
        drone_id=row['drone_id'],
        model=row['model'],
        status=row['status'],
        battery_level=row['battery_level'],
        current_lat=row['current_lat'],
        current_lon=row['current_lon'],
        current_alt=row['current_alt'],
        assigned_order_id=row['assigned_order_id'],
        total_flights=row['total_flights'],
        total_distance=row['total_distance'],
        last_updated=row['last_updated']
    )

@app.patch("/drones/{drone_id}/telemetry")
async def update_drone_telemetry(drone_id: str, telemetry: UpdateDroneTelemetry):
    """
    Update drone telemetry (position, battery)
    
    Called by drones to report their status
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if drone exists
    cursor.execute("SELECT drone_id FROM drones WHERE drone_id = ?", (drone_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Drone not found")
    
    # Update
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE drones 
        SET current_lat = ?, current_lon = ?, current_alt = ?, 
            battery_level = ?, last_updated = ?
        WHERE drone_id = ?
    """, (
        telemetry.latitude,
        telemetry.longitude,
        telemetry.altitude,
        telemetry.battery_level,
        now,
        drone_id
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "drone_id": drone_id,
        "telemetry_updated": now,
        "battery": telemetry.battery_level
    }

@app.post("/drones/{drone_id}/assign", response_model=MissionResponse, status_code=201)
async def assign_mission(drone_id: str, mission_req: AssignMissionRequest):
    """
    Assign delivery mission to drone
    
    - Checks drone availability
    - Fetches order details from Order Service
    - Creates mission
    - Updates order status
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Check drone exists and is available
    cursor.execute("""
        SELECT drone_id, status, battery_level 
        FROM drones 
        WHERE drone_id = ?
    """, (drone_id,))
    
    drone = cursor.fetchone()
    
    if not drone:
        conn.close()
        raise HTTPException(status_code=404, detail="Drone not found")
    
    if drone['status'] not in ['idle', 'charging']:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Drone not available: {drone['status']}")
    
    if drone['battery_level'] < 50:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Battery too low: {drone['battery_level']}%")
    
    # Fetch order from Order Service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ORDER_SERVICE_URL}/orders/{mission_req.order_id}")
            
            if response.status_code == 404:
                conn.close()
                raise HTTPException(status_code=404, detail="Order not found")
            
            response.raise_for_status()
            order = response.json()
    
    except httpx.HTTPError as e:
        conn.close()
        raise HTTPException(status_code=503, detail=f"Order Service unavailable: {str(e)}")
    
    # Create mission
    mission_id = f"MISSION_{datetime.now().strftime('%Y%m%d%H%M%S')}_{drone_id}"
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO missions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        mission_id,
        drone_id,
        mission_req.order_id,
        "in_progress",
        now,
        None,
        None,
        None
    ))
    
    # Update drone status
    cursor.execute("""
        UPDATE drones 
        SET status = 'assigned', assigned_order_id = ?
        WHERE drone_id = ?
    """, (mission_req.order_id, drone_id))
    
    conn.commit()
    conn.close()
    
    # Update order status in Order Service
    try:
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{ORDER_SERVICE_URL}/orders/{mission_req.order_id}/status",
                json={
                    "status": "drone_assigned",
                    "assigned_drone_id": drone_id
                }
            )
    except:
        pass  # Non-critical
    
    return MissionResponse(
        mission_id=mission_id,
        drone_id=drone_id,
        order_id=mission_req.order_id,
        status="in_progress",
        start_time=now,
        end_time=None,
        battery_used=None,
        distance_km=None
    )

@app.patch("/missions/{mission_id}/complete")
async def complete_mission(mission_id: str, battery_used: float, distance_km: float):
    """
    Complete mission
    
    - Updates mission status
    - Updates drone statistics
    - Marks order as delivered
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get mission
    cursor.execute("""
        SELECT mission_id, drone_id, order_id, status 
        FROM missions 
        WHERE mission_id = ?
    """, (mission_id,))
    
    mission = cursor.fetchone()
    
    if not mission:
        conn.close()
        raise HTTPException(status_code=404, detail="Mission not found")
    
    if mission['status'] != 'in_progress':
        conn.close()
        raise HTTPException(status_code=400, detail="Mission not in progress")
    
    # Update mission
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE missions 
        SET status = 'completed', end_time = ?, battery_used = ?, distance_km = ?
        WHERE mission_id = ?
    """, (now, battery_used, distance_km, mission_id))
    
    # Update drone
    cursor.execute("""
        UPDATE drones 
        SET status = 'idle', 
            assigned_order_id = NULL,
            total_flights = total_flights + 1,
            total_distance = total_distance + ?,
            battery_level = battery_level - ?,
            last_updated = ?
        WHERE drone_id = ?
    """, (distance_km, battery_used, now, mission['drone_id']))
    
    conn.commit()
    conn.close()
    
    # Update order status
    try:
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{ORDER_SERVICE_URL}/orders/{mission['order_id']}/status",
                json={"status": "delivered"}
            )
    except:
        pass
    
    return {
        "mission_id": mission_id,
        "status": "completed",
        "completed_at": now
    }

@app.get("/missions", response_model=List[MissionResponse])
async def list_missions(status: Optional[str] = None):
    """List all missions"""
    conn = get_db()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("SELECT * FROM missions WHERE status = ? ORDER BY start_time DESC", (status,))
    else:
        cursor.execute("SELECT * FROM missions ORDER BY start_time DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    missions = []
    for row in rows:
        missions.append(MissionResponse(
            mission_id=row['mission_id'],
            drone_id=row['drone_id'],
            order_id=row['order_id'],
            status=row['status'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            battery_used=row['battery_used'],
            distance_km=row['distance_km']
        ))
    
    return missions

@app.get("/stats")
async def get_stats():
    """Get fleet statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total drones
    cursor.execute("SELECT COUNT(*) as total FROM drones")
    total_drones = cursor.fetchone()['total']
    
    # By status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM drones 
        GROUP BY status
    """)
    by_status = {row['status']: row['count'] for row in cursor.fetchall()}
    
    # Total missions
    cursor.execute("SELECT COUNT(*) as total FROM missions")
    total_missions = cursor.fetchone()['total']
    
    # Completed today
    today = datetime.now().date().isoformat()
    cursor.execute("""
        SELECT COUNT(*) as today_count 
        FROM missions 
        WHERE DATE(start_time) = ? AND status = 'completed'
    """, (today,))
    today_missions = cursor.fetchone()['today_count']
    
    conn.close()
    
    return {
        "total_drones": total_drones,
        "drones_by_status": by_status,
        "total_missions": total_missions,
        "today_missions": today_missions
    }

# ═══════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "drone_service:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
