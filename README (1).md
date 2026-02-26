# 🚀 DelyBot™ X - Production Microservices

<div align="center">

**INGENIOUSBLUEPRINTS PRIVATE LIMITED**  
CIN: U78300JH2025PTC025180

**DelyBot™ X - Autonomous Drone Delivery**  
*Microservices Architecture - Version 2.0.0*

---

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Production](https://img.shields.io/badge/Production-Ready-success)](/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](/)

</div>

---

## ✅ What's Included

### **Step 1: Microservices Built** ✓

- ✅ **Order Service** (Port 8001) - Order management API
- ✅ **Drone Service** (Port 8002) - Fleet control API
- ✅ RESTful APIs with FastAPI
- ✅ Input validation (Pydantic)
- ✅ SQLite databases
- ✅ Inter-service communication
- ✅ Health checks
- ✅ API documentation (Swagger)

### **Step 2: Dockerized** ✓

- ✅ Dockerfile for each service
- ✅ docker-compose.yml orchestration
- ✅ Container networking
- ✅ Volume persistence
- ✅ Health checks
- ✅ Auto-restart policies

### **Step 3: Cloud Deployment Guide** ✓

- ✅ AWS EC2 instructions
- ✅ DigitalOcean instructions
- ✅ Automated deployment script
- ✅ SSL/TLS setup
- ✅ Nginx reverse proxy
- ✅ Monitoring & logging
- ✅ Backup strategies

---

## 📂 File Structure

```
microservices/
├── order_service.py          # Order management API
├── drone_service.py           # Drone control API
├── requirements.txt           # Python dependencies
├── Dockerfile.order           # Order service container
├── Dockerfile.drone           # Drone service container
├── docker-compose.yml         # Orchestration
├── deploy.sh                  # Automated deployment script
├── DEPLOYMENT_GUIDE.md        # Complete deployment guide
├── API_TESTING.md             # API test collection
└── README.md                  # This file
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Docker installed
- Docker Compose installed
- Port 8001 and 8002 available

### Run

```bash
# Clone repository
cd microservices/

# Start services
docker-compose up --build

# Services available at:
# Order Service:  http://localhost:8001
# Drone Service:  http://localhost:8002

# API Docs:
# http://localhost:8001/docs
# http://localhost:8002/docs
```

### Test

```bash
# Health check
curl http://localhost:8001/
curl http://localhost:8002/

# Create order
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "customer_phone": "9876543210",
    "customer_email": "test@example.com",
    "delivery_address": "Test Address, Ranchi",
    "delivery_location": {"latitude": 23.3540, "longitude": 85.3350},
    "product_name": "Test Product",
    "product_weight": 1.5,
    "priority": 1
  }'

# List orders
curl http://localhost:8001/orders

# List drones
curl http://localhost:8002/drones
```

---

## ☁️ Deploy to Cloud

### Option 1: Automated Deployment

```bash
# SSH into your cloud server (AWS EC2 / DigitalOcean)
ssh user@your-server-ip

# Upload files
scp -r microservices/* user@your-server-ip:~/delybot/

# Run deployment script
cd delybot
chmod +x deploy.sh
./deploy.sh

# ✓ Done! Services will be running at:
# http://your-server-ip:8001
# http://your-server-ip:8002
```

### Option 2: Manual Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions for:
- AWS EC2
- DigitalOcean
- SSL/TLS setup
- Nginx configuration
- Production hardening

---

## 📊 API Overview

### Order Service API (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/orders` | GET | List all orders |
| `/orders` | POST | Create new order |
| `/orders/{id}` | GET | Get order details |
| `/orders/{id}/status` | PATCH | Update order status |
| `/orders/{id}` | DELETE | Cancel order |
| `/stats` | GET | Get statistics |
| `/docs` | GET | API documentation |

### Drone Service API (Port 8002)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/drones` | GET | List all drones |
| `/drones/{id}` | GET | Get drone details |
| `/drones/{id}/telemetry` | PATCH | Update drone position |
| `/drones/{id}/assign` | POST | Assign mission |
| `/missions` | GET | List all missions |
| `/missions/{id}/complete` | PATCH | Complete mission |
| `/stats` | GET | Get fleet statistics |
| `/docs` | GET | API documentation |

**Full API documentation:** [API_TESTING.md](API_TESTING.md)

---

## 🔌 Inter-Service Communication

Services communicate via HTTP:

```python
# Drone Service calls Order Service
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"http://order-service:8001/orders/{order_id}"
    )
    order = response.json()
```

Docker Compose networking ensures services can reach each other by name.

---

## 💾 Data Persistence

- Each service has its own SQLite database
- Databases stored in `/app/` inside containers
- Mounted as volumes for persistence
- Survives container restarts

```yaml
volumes:
  - ./data/order:/app
  - ./data/drone:/app
```

---

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale services
docker-compose up --scale order-service=3 --scale drone-service=2
```

### Load Balancing

Add nginx as load balancer:

```nginx
upstream order_backend {
    server order-service-1:8001;
    server order-service-2:8001;
    server order-service-3:8001;
}

server {
    location /api/orders {
        proxy_pass http://order_backend;
    }
}
```

---

## 🔒 Security

### Production Checklist

- [ ] Enable SSL/TLS (Let's Encrypt)
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Enable CORS properly
- [ ] Add authentication (JWT)
- [ ] Setup firewall rules
- [ ] Regular backups
- [ ] Log monitoring

### Example: Add Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/orders", dependencies=[Security(security)])
async def list_orders():
    # Protected endpoint
    pass
```

---

## 📊 Monitoring

### Container Stats

```bash
# Real-time stats
docker stats

# Service logs
docker-compose logs -f order-service
docker-compose logs -f drone-service
```

### Health Checks

Both services have built-in health checks:

```bash
# Check health
curl http://your-ip:8001/
curl http://your-ip:8002/

# Get statistics
curl http://your-ip:8001/stats
curl http://your-ip:8002/stats
```

---

## 🐛 Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose down
docker-compose up --build
```

### Port already in use

```bash
# Find process using port
sudo lsof -i :8001
sudo lsof -i :8002

# Kill process or change port in docker-compose.yml
```

### Can't connect from outside

```bash
# Check firewall
sudo ufw status
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp

# Check if services are listening
netstat -tlnp | grep 800
```

### Database errors

```bash
# Reset databases
docker-compose down
rm -rf data/
docker-compose up
```

---

## 📚 Documentation

- **API Testing**: [API_TESTING.md](API_TESTING.md)
- **Deployment**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **API Docs**: `/docs` endpoint on each service
- **Architecture**: [DELYBOT_X_ARCHITECTURE.md](../DELYBOT_X_ARCHITECTURE.md)

---

## 🎯 Production Deployment Checklist

- [ ] ✅ Code tested locally
- [ ] ✅ Docker images built
- [ ] ✅ docker-compose.yml configured
- [ ] ✅ Cloud server provisioned
- [ ] ✅ Docker installed on server
- [ ] ✅ Files uploaded to server
- [ ] ✅ Services started
- [ ] ✅ Health checks passing
- [ ] ✅ APIs accessible from internet
- [ ] ✅ Inter-service communication working
- [ ] ✅ Firewall configured
- [ ] ✅ SSL certificate installed (optional)
- [ ] ✅ Monitoring setup
- [ ] ✅ Backup strategy in place

---

## 💰 Deployment Costs

### AWS EC2
- **Instance**: t2.medium ($34/month)
- **Storage**: 20GB ($2/month)
- **Data Transfer**: ~$5/month
- **Total**: ~$40/month

### DigitalOcean
- **Droplet**: Basic 2GB ($12/month)
- **Backups**: $1.20/month (optional)
- **Total**: ~$12/month

**Recommendation**: DigitalOcean for MVP

---

## 🚀 Next Steps

1. **Deploy to Cloud**
   ```bash
   ./deploy.sh
   ```

2. **Test APIs**
   - Use curl or Postman
   - Follow [API_TESTING.md](API_TESTING.md)

3. **Share Your Deployment**
   ```
   Order Service: http://your-ip:8001
   Drone Service: http://your-ip:8002
   ```

4. **Add More Services**
   - Weather Service
   - Code Management Service
   - Analytics Service

---

## 📞 Support

**INGENIOUSBLUEPRINTS PRIVATE LIMITED**  
CIN: U78300JH2025PTC025180  
Email: support@ingeniousblueprints.com  
Location: Ranchi, Jharkhand, India

---

## 📝 License

Proprietary - INGENIOUSBLUEPRINTS PRIVATE LIMITED © 2025

---

<div align="center">

**DelyBot™ X - From Code to Cloud** ✓

*Built with FastAPI • Powered by Docker • Deployed on Cloud*

**Ready for Production** 🚀

</div>
