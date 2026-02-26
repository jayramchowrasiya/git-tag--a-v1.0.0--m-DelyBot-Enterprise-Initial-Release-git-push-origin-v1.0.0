#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
DelyBot™ - Enterprise Autonomous Drone Delivery System
═══════════════════════════════════════════════════════════════════════════

Product: DelyBot™
Company: INGENIOUSBLUEPRINTS PRIVATE LIMITED
CIN: U78300JH2025PTC025180
Address: H-129, PATEL NAGAR, HECI DHURWA, Ranchi - 834004, Jharkhand, India

Enterprise Features:
- Persistent storage (SQLite + Redis)
- Rate limiting per IP
- Real weather API integration
- Telemetry heartbeat monitoring
- Code lifecycle management
- Complete audit trail

Version: 1.0.0 Enterprise
Classification: Commercial Production System
"""

import asyncio
import logging
import time
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import aiohttp
from collections import defaultdict

# Company information
COMPANY_INFO = {
    'name': 'INGENIOUSBLUEPRINTS PRIVATE LIMITED',
    'cin': 'U78300JH2025PTC025180',
    'pan': 'AAICI2880F',
    'tan': 'RCHI01139F',
    'address': 'H-129, PATEL NAGAR, HECI DHURWA, Dhurwa, Ranchi - 834004, Jharkhand',
    'incorporation_date': '2025-06-28',
    'product_name': 'DelyBot™',
    'tagline': 'Autonomous Delivery, Engineered Excellence',
    'website': 'www.ingeniousblueprints.com',
    'email': 'support@ingeniousblueprints.com',
    'phone': '+91-651-XXXXXXX'
}

# Configure logging with company branding
logging.basicConfig(
    level=logging.INFO,
    format='[DelyBot™] %(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('DelyBot')


# ═══════════════════════════════════════════════════════════════════════════
# ENTERPRISE IMPROVEMENT #1: CODE LIFECYCLE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class EnterpriseCodeManager:
    """
    Enhanced code manager with complete lifecycle management
    
    Improvements:
    - Successful codes deleted after delivery
    - Failed codes archived
    - Audit trail maintained
    - Cleanup background task
    """
    
    def __init__(self, db_path: str = "./delybot_data/codes.db"):
        self.db_path = db_path
        Path("./delybot_data").mkdir(exist_ok=True)
        self._init_database()
        self.cleanup_task = None
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Active codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_codes (
                code TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                max_attempts INTEGER NOT NULL,
                attempts_used INTEGER NOT NULL,
                is_locked INTEGER NOT NULL,
                last_attempt TEXT
            )
        """)
        
        # Code history/audit table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_history (
                code TEXT NOT NULL,
                order_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT,
                ip_address TEXT
            )
        """)
        
        # Archived codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS archived_codes (
                code TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                total_attempts INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("[CodeManager] Database initialized")
    
    def generate_code(self, order_id: str) -> dict:
        """Generate and store code"""
        from drone_validation_safety import SecureCodeGenerator
        
        code_obj = SecureCodeGenerator.create_delivery_code(order_id)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO active_codes VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code_obj.code,
            code_obj.order_id,
            code_obj.created_at.isoformat(),
            code_obj.expires_at.isoformat(),
            code_obj.max_attempts,
            code_obj.attempts_used,
            int(code_obj.is_locked),
            None
        ))
        
        # Audit log
        cursor.execute("""
            INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
        """, (
            code_obj.code,
            order_id,
            'GENERATED',
            datetime.now().isoformat(),
            'Code generated successfully',
            None
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"[CodeManager] Code {code_obj.code} generated for order {order_id}")
        
        return asdict(code_obj)
    
    def verify_code(
        self,
        code: str,
        order_id: str,
        drone_id: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Verify code with audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get code
        cursor.execute("SELECT * FROM active_codes WHERE code = ?", (code,))
        row = cursor.fetchone()
        
        if not row:
            # Audit log
            cursor.execute("""
                INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code,
                order_id,
                'VERIFY_FAILED',
                datetime.now().isoformat(),
                'Invalid code',
                ip_address
            ))
            conn.commit()
            conn.close()
            
            logger.warning(f"[CodeManager] Invalid code attempt: {code}")
            return False, "Invalid code"
        
        # Parse row
        (code_str, stored_order_id, created_at, expires_at,
         max_attempts, attempts_used, is_locked, last_attempt) = row
        
        # Check expiry
        if datetime.fromisoformat(expires_at) <= datetime.now():
            cursor.execute("""
                INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code,
                order_id,
                'VERIFY_FAILED',
                datetime.now().isoformat(),
                'Code expired',
                ip_address
            ))
            conn.commit()
            conn.close()
            
            logger.warning(f"[CodeManager] Expired code: {code}")
            return False, "Code expired"
        
        # Check lock
        if is_locked:
            cursor.execute("""
                INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code,
                order_id,
                'VERIFY_FAILED',
                datetime.now().isoformat(),
                'Code locked',
                ip_address
            ))
            conn.commit()
            conn.close()
            
            logger.warning(f"[CodeManager] Locked code: {code}")
            return False, "Code locked due to too many attempts"
        
        # Check attempts
        if attempts_used >= max_attempts:
            # Lock code
            cursor.execute("""
                UPDATE active_codes SET is_locked = 1 WHERE code = ?
            """, (code,))
            
            cursor.execute("""
                INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code,
                order_id,
                'LOCKED',
                datetime.now().isoformat(),
                'Max attempts exceeded',
                ip_address
            ))
            conn.commit()
            conn.close()
            
            logger.warning(f"[CodeManager] Max attempts exceeded: {code}")
            return False, "Maximum attempts exceeded"
        
        # Check order match
        if stored_order_id != order_id:
            # Increment attempts
            cursor.execute("""
                UPDATE active_codes 
                SET attempts_used = attempts_used + 1,
                    last_attempt = ?
                WHERE code = ?
            """, (datetime.now().isoformat(), code))
            
            cursor.execute("""
                INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code,
                order_id,
                'VERIFY_FAILED',
                datetime.now().isoformat(),
                'Order ID mismatch',
                ip_address
            ))
            conn.commit()
            conn.close()
            
            logger.warning(f"[CodeManager] Order mismatch for code: {code}")
            return False, "Code does not match order"
        
        # SUCCESS - Increment and log
        cursor.execute("""
            UPDATE active_codes 
            SET attempts_used = attempts_used + 1,
                last_attempt = ?
            WHERE code = ?
        """, (datetime.now().isoformat(), code))
        
        cursor.execute("""
            INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
        """, (
            code,
            order_id,
            'VERIFIED',
            datetime.now().isoformat(),
            f'Successfully verified by drone {drone_id}',
            ip_address
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"[CodeManager] ✓ Code {code} verified successfully")
        
        return True, None
    
    def complete_delivery(self, code: str, success: bool = True):
        """
        IMPROVEMENT #1: Delete/archive code after delivery
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get code details
        cursor.execute("SELECT * FROM active_codes WHERE code = ?", (code,))
        row = cursor.fetchone()
        
        if row:
            (code_str, order_id, created_at, expires_at,
             max_attempts, attempts_used, is_locked, last_attempt) = row
            
            # Archive code
            cursor.execute("""
                INSERT INTO archived_codes VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code,
                order_id,
                'SUCCESS' if success else 'FAILED',
                created_at,
                datetime.now().isoformat(),
                attempts_used
            ))
            
            # Delete from active
            cursor.execute("DELETE FROM active_codes WHERE code = ?", (code,))
            
            # Audit log
            cursor.execute("""
                INSERT INTO code_history VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code,
                order_id,
                'COMPLETED',
                datetime.now().isoformat(),
                f'Delivery {"successful" if success else "failed"}',
                None
            ))
            
            conn.commit()
            
            logger.info(f"[CodeManager] ✓ Code {code} archived after delivery")
        
        conn.close()
    
    async def start_cleanup_task(self):
        """Background task to cleanup expired codes"""
        logger.info("[CodeManager] Starting cleanup task...")
        
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Find expired codes
                cursor.execute("""
                    SELECT code, order_id, created_at, attempts_used
                    FROM active_codes
                    WHERE datetime(expires_at) <= datetime('now')
                """)
                
                expired = cursor.fetchall()
                
                if expired:
                    for code, order_id, created_at, attempts in expired:
                        # Archive
                        cursor.execute("""
                            INSERT INTO archived_codes VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            code,
                            order_id,
                            'EXPIRED',
                            created_at,
                            datetime.now().isoformat(),
                            attempts
                        ))
                        
                        # Delete
                        cursor.execute("DELETE FROM active_codes WHERE code = ?", (code,))
                    
                    conn.commit()
                    logger.info(f"[CodeManager] Cleaned up {len(expired)} expired codes")
                
                conn.close()
                
            except Exception as e:
                logger.error(f"[CodeManager] Cleanup task error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# ENTERPRISE IMPROVEMENT #2: RATE LIMITING PER IP
# ═══════════════════════════════════════════════════════════════════════════

class IPRateLimiter:
    """
    Rate limiter per IP address
    
    Prevents abuse when exposed via API
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 500,
        ban_threshold: int = 1000
    ):
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.ban_threshold = ban_threshold
        
        # Tracking
        self.minute_requests: Dict[str, List[float]] = defaultdict(list)
        self.hour_requests: Dict[str, List[float]] = defaultdict(list)
        self.banned_ips: Dict[str, float] = {}  # IP -> ban_until
    
    def is_allowed(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """Check if IP is allowed to make request"""
        now = time.time()
        
        # Check ban
        if ip_address in self.banned_ips:
            ban_until = self.banned_ips[ip_address]
            if now < ban_until:
                remaining = int(ban_until - now)
                return False, f"IP banned for {remaining}s due to abuse"
            else:
                del self.banned_ips[ip_address]
        
        # Cleanup old requests
        minute_ago = now - 60
        hour_ago = now - 3600
        
        self.minute_requests[ip_address] = [
            t for t in self.minute_requests[ip_address] if t > minute_ago
        ]
        self.hour_requests[ip_address] = [
            t for t in self.hour_requests[ip_address] if t > hour_ago
        ]
        
        # Check limits
        minute_count = len(self.minute_requests[ip_address])
        hour_count = len(self.hour_requests[ip_address])
        
        if minute_count >= self.rpm:
            return False, f"Rate limit: {self.rpm} requests/minute exceeded"
        
        if hour_count >= self.rph:
            return False, f"Rate limit: {self.rph} requests/hour exceeded"
        
        # Check abuse (ban if too many requests)
        if hour_count >= self.ban_threshold:
            # Ban for 1 hour
            self.banned_ips[ip_address] = now + 3600
            logger.warning(f"[RateLimit] IP {ip_address} BANNED for 1 hour (abuse detected)")
            return False, "IP banned due to excessive requests"
        
        return True, None
    
    def record_request(self, ip_address: str):
        """Record a request"""
        now = time.time()
        self.minute_requests[ip_address].append(now)
        self.hour_requests[ip_address].append(now)


# ═══════════════════════════════════════════════════════════════════════════
# ENTERPRISE IMPROVEMENT #3: PERSISTENT STORAGE
# ═══════════════════════════════════════════════════════════════════════════

class PersistentStorage:
    """
    Persistent storage for orders, drones, deliveries
    
    Replaces RAM-only storage
    """
    
    def __init__(self, db_path: str = "./delybot_data/main.db"):
        self.db_path = db_path
        Path("./delybot_data").mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize all tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                delivery_lat REAL NOT NULL,
                delivery_lon REAL NOT NULL,
                products TEXT NOT NULL,
                total_weight REAL NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                delivery_code TEXT,
                assigned_drone_id TEXT,
                order_time TEXT NOT NULL,
                delivery_time TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Drones table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drones (
                drone_id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                battery_level REAL NOT NULL,
                current_lat REAL NOT NULL,
                current_lon REAL NOT NULL,
                current_alt REAL NOT NULL,
                total_flights INTEGER NOT NULL,
                total_distance REAL NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        # Deliveries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deliveries (
                delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                drone_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL,
                battery_used REAL,
                distance_km REAL,
                success INTEGER NOT NULL
            )
        """)
        
        # Telemetry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drone_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                alt REAL NOT NULL,
                battery REAL NOT NULL,
                status TEXT NOT NULL,
                speed REAL,
                heading REAL
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("[Storage] Database initialized with persistent storage")
    
    def save_order(self, order: dict):
        """Save order to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO orders VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order['order_id'],
            order['customer']['customer_id'],
            order['customer']['name'],
            order['customer']['phone'],
            order['customer']['email'],
            str(order['delivery_location']),
            order['delivery_location']['coordinates']['latitude'],
            order['delivery_location']['coordinates']['longitude'],
            json.dumps([p for p in order['products']]),
            order['total_weight'],
            order['status'],
            order['priority'],
            order.get('delivery_code'),
            order.get('assigned_drone_id'),
            order['order_time'].isoformat(),
            order.get('actual_delivery_time', {}).isoformat() if order.get('actual_delivery_time') else None,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()


# Continue in next file...
