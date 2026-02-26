# DelyBot™ X - API Testing Guide

## Base URLs
```
Order Service:  http://YOUR_IP:8001
Drone Service:  http://YOUR_IP:8002
```

Replace `YOUR_IP` with your server IP address.

---

## ORDER SERVICE API

### 1. Health Check
```bash
curl http://YOUR_IP:8001/
```

**Response:**
```json
{
  "service": "Order Service",
  "version": "2.0.0",
  "company": "INGENIOUSBLUEPRINTS PRIVATE LIMITED",
  "status": "running"
}
```

### 2. Create Order
```bash
curl -X POST http://YOUR_IP:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Raj Kumar",
    "customer_phone": "9876543210",
    "customer_email": "raj@example.com",
    "delivery_address": "Main Road, Doranda, Ranchi",
    "delivery_location": {
      "latitude": 23.3540,
      "longitude": 85.3350
    },
    "product_name": "Emergency Medicine",
    "product_weight": 0.5,
    "priority": 3
  }'
```

**Response:**
```json
{
  "order_id": "ORD20250628123456ABC",
  "customer_name": "Raj Kumar",
  "customer_phone": "9876543210",
  "customer_email": "raj@example.com",
  "delivery_address": "Main Road, Doranda, Ranchi",
  "delivery_lat": 23.354,
  "delivery_lon": 85.335,
  "product_name": "Emergency Medicine",
  "product_weight": 0.5,
  "delivery_code": "AB3C7D9F",
  "status": "pending",
  "priority": 3,
  "assigned_drone_id": null,
  "created_at": "2025-06-28T12:34:56",
  "updated_at": "2025-06-28T12:34:56"
}
```

### 3. List All Orders
```bash
curl http://YOUR_IP:8001/orders
```

### 4. List Orders by Status
```bash
# Pending orders
curl http://YOUR_IP:8001/orders?status=pending

# In-transit orders
curl http://YOUR_IP:8001/orders?status=in_transit

# Delivered orders
curl http://YOUR_IP:8001/orders?status=delivered
```

### 5. Get Specific Order
```bash
curl http://YOUR_IP:8001/orders/ORD20250628123456ABC
```

### 6. Update Order Status
```bash
curl -X PATCH http://YOUR_IP:8001/orders/ORD20250628123456ABC/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "drone_assigned",
    "assigned_drone_id": "DRONE_001"
  }'
```

### 7. Cancel Order
```bash
curl -X DELETE http://YOUR_IP:8001/orders/ORD20250628123456ABC
```

### 8. Get Statistics
```bash
curl http://YOUR_IP:8001/stats
```

**Response:**
```json
{
  "total_orders": 25,
  "orders_by_status": {
    "pending": 5,
    "in_transit": 2,
    "delivered": 15,
    "cancelled": 3
  },
  "today_orders": 8
}
```

---

## DRONE SERVICE API

### 1. Health Check
```bash
curl http://YOUR_IP:8002/
```

**Response:**
```json
{
  "service": "Drone Control Service",
  "version": "2.0.0",
  "company": "INGENIOUSBLUEPRINTS PRIVATE LIMITED",
  "status": "running"
}
```

### 2. List All Drones
```bash
curl http://YOUR_IP:8002/drones
```

**Response:**
```json
[
  {
    "drone_id": "DRONE_001",
    "model": "JROS-X1",
    "status": "idle",
    "battery_level": 100.0,
    "current_lat": 23.3441,
    "current_lon": 85.3096,
    "current_alt": 0.0,
    "assigned_order_id": null,
    "total_flights": 0,
    "total_distance": 0.0,
    "last_updated": "2025-06-28T12:00:00"
  }
]
```

### 3. List Drones by Status
```bash
# Available drones
curl http://YOUR_IP:8002/drones?status=idle

# Busy drones
curl http://YOUR_IP:8002/drones?status=assigned
```

### 4. Get Specific Drone
```bash
curl http://YOUR_IP:8002/drones/DRONE_001
```

### 5. Update Drone Telemetry
```bash
curl -X PATCH http://YOUR_IP:8002/drones/DRONE_001/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 23.3500,
    "longitude": 85.3100,
    "altitude": 60.0,
    "battery_level": 85.0
  }'
```

### 6. Assign Mission to Drone
```bash
curl -X POST http://YOUR_IP:8002/drones/DRONE_001/assign \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD20250628123456ABC"
  }'
```

**Response:**
```json
{
  "mission_id": "MISSION_20250628123456_DRONE_001",
  "drone_id": "DRONE_001",
  "order_id": "ORD20250628123456ABC",
  "status": "in_progress",
  "start_time": "2025-06-28T12:35:00",
  "end_time": null,
  "battery_used": null,
  "distance_km": null
}
```

### 7. Complete Mission
```bash
curl -X PATCH "http://YOUR_IP:8002/missions/MISSION_20250628123456_DRONE_001/complete?battery_used=15.5&distance_km=8.5" \
  -H "Content-Type: application/json"
```

### 8. List All Missions
```bash
# All missions
curl http://YOUR_IP:8002/missions

# In-progress missions
curl http://YOUR_IP:8002/missions?status=in_progress

# Completed missions
curl http://YOUR_IP:8002/missions?status=completed
```

### 9. Get Fleet Statistics
```bash
curl http://YOUR_IP:8002/stats
```

**Response:**
```json
{
  "total_drones": 3,
  "drones_by_status": {
    "idle": 2,
    "assigned": 1
  },
  "total_missions": 42,
  "today_missions": 8
}
```

---

## COMPLETE WORKFLOW TEST

### End-to-End Delivery Flow

```bash
# 1. Create order
ORDER_RESPONSE=$(curl -s -X POST http://YOUR_IP:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "customer_phone": "9876543210",
    "customer_email": "test@example.com",
    "delivery_address": "Test Address, Ranchi",
    "delivery_location": {"latitude": 23.3540, "longitude": 85.3350},
    "product_name": "Test Product",
    "product_weight": 1.5,
    "priority": 1
  }')

ORDER_ID=$(echo $ORDER_RESPONSE | grep -o '"order_id":"[^"]*' | cut -d'"' -f4)
echo "Order created: $ORDER_ID"

# 2. Assign drone
MISSION_RESPONSE=$(curl -s -X POST http://YOUR_IP:8002/drones/DRONE_001/assign \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$ORDER_ID\"}")

MISSION_ID=$(echo $MISSION_RESPONSE | grep -o '"mission_id":"[^"]*' | cut -d'"' -f4)
echo "Mission assigned: $MISSION_ID"

# 3. Simulate flight (update telemetry)
curl -s -X PATCH http://YOUR_IP:8002/drones/DRONE_001/telemetry \
  -H "Content-Type: application/json" \
  -d '{"latitude": 23.3520, "longitude": 85.3250, "altitude": 60.0, "battery_level": 90.0}'

echo "Drone in flight..."

# 4. Complete mission
curl -s -X PATCH "http://YOUR_IP:8002/missions/$MISSION_ID/complete?battery_used=15.0&distance_km=8.5"

echo "Mission completed!"

# 5. Verify order status
curl -s http://YOUR_IP:8001/orders/$ORDER_ID | grep -o '"status":"[^"]*'

echo "✓ End-to-end test complete!"
```

---

## POSTMAN COLLECTION

Import this JSON into Postman:

```json
{
  "info": {
    "name": "DelyBot X Microservices",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url_order",
      "value": "http://YOUR_IP:8001"
    },
    {
      "key": "base_url_drone",
      "value": "http://YOUR_IP:8002"
    }
  ],
  "item": [
    {
      "name": "Order Service",
      "item": [
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "url": "{{base_url_order}}/"
          }
        },
        {
          "name": "Create Order",
          "request": {
            "method": "POST",
            "url": "{{base_url_order}}/orders",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"customer_name\": \"Test Customer\",\n  \"customer_phone\": \"9876543210\",\n  \"customer_email\": \"test@example.com\",\n  \"delivery_address\": \"Test Address\",\n  \"delivery_location\": {\"latitude\": 23.3540, \"longitude\": 85.3350},\n  \"product_name\": \"Test Product\",\n  \"product_weight\": 1.5,\n  \"priority\": 1\n}"
            }
          }
        },
        {
          "name": "List Orders",
          "request": {
            "method": "GET",
            "url": "{{base_url_order}}/orders"
          }
        },
        {
          "name": "Get Stats",
          "request": {
            "method": "GET",
            "url": "{{base_url_order}}/stats"
          }
        }
      ]
    },
    {
      "name": "Drone Service",
      "item": [
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "url": "{{base_url_drone}}/"
          }
        },
        {
          "name": "List Drones",
          "request": {
            "method": "GET",
            "url": "{{base_url_drone}}/drones"
          }
        },
        {
          "name": "Assign Mission",
          "request": {
            "method": "POST",
            "url": "{{base_url_drone}}/drones/DRONE_001/assign",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"order_id\": \"YOUR_ORDER_ID\"\n}"
            }
          }
        },
        {
          "name": "Get Stats",
          "request": {
            "method": "GET",
            "url": "{{base_url_drone}}/stats"
          }
        }
      ]
    }
  ]
}
```

---

## TROUBLESHOOTING

### Services not responding
```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs order-service
docker-compose logs drone-service

# Restart services
docker-compose restart
```

### Cannot connect from outside
```bash
# Check firewall
sudo ufw status

# Allow ports
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp
```

### Database errors
```bash
# Reset databases
docker-compose down
rm -f data/order/order_service.db data/drone/drone_service.db
docker-compose up -d
```

---

**Ready to test your deployment!** 🚀
