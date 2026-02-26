# DelyBot™ X - Production Deployment Guide
## Step-by-Step Cloud Deployment

**Company:** INGENIOUSBLUEPRINTS PRIVATE LIMITED  
**Product:** DelyBot™ X Microservices  
**Version:** 2.0.0

---

## ✅ STEP 1: Microservices Built ✓

**Files Created:**
- ✅ `order_service.py` - Order management API
- ✅ `drone_service.py` - Drone control API
- ✅ `requirements.txt` - Dependencies

**Features:**
- RESTful APIs with FastAPI
- SQLite databases
- Inter-service communication
- Input validation
- Health checks

---

## ✅ STEP 2: Dockerized ✓

**Files Created:**
- ✅ `Dockerfile.order` - Order service container
- ✅ `Dockerfile.drone` - Drone service container
- ✅ `docker-compose.yml` - Orchestration

**Test Locally:**

```bash
# Build and run
docker-compose up --build

# Services will be available at:
# Order Service: http://localhost:8001
# Drone Service: http://localhost:8002
```

---

## 🚀 STEP 3: Deploy to Cloud

### Option A: AWS EC2 Deployment

#### 1. Create EC2 Instance

```bash
# Launch Ubuntu 22.04 LTS instance
# Instance type: t2.medium (2 vCPU, 4GB RAM)
# Storage: 20GB SSD
# Security Group: Allow ports 22, 8001, 8002, 80, 443
```

**Security Group Rules:**
```
Type          Protocol  Port Range  Source
SSH           TCP       22          Your IP
Custom TCP    TCP       8001        0.0.0.0/0
Custom TCP    TCP       8002        0.0.0.0/0
HTTP          TCP       80          0.0.0.0/0
HTTPS         TCP       443         0.0.0.0/0
```

#### 2. Connect to Instance

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y
```

#### 3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker ubuntu

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
exit
```

#### 4. Deploy Application

```bash
# Clone/upload your microservices
mkdir delybot-x
cd delybot-x

# Copy all files:
# - order_service.py
# - drone_service.py
# - requirements.txt
# - Dockerfile.order
# - Dockerfile.drone
# - docker-compose.yml

# Create data directories
mkdir -p data/order data/drone

# Build and start services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 5. Verify Deployment

```bash
# Test Order Service
curl http://your-ec2-ip:8001/

# Test Drone Service
curl http://your-ec2-ip:8002/

# Expected response:
{
  "service": "Order Service",
  "version": "2.0.0",
  "company": "INGENIOUSBLUEPRINTS PRIVATE LIMITED",
  "status": "running"
}
```

#### 6. Setup Nginx (Optional)

```bash
# Install Nginx
sudo apt install nginx -y

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/delybot
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/orders {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/drones {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/delybot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Option B: DigitalOcean Deployment

#### 1. Create Droplet

```bash
# Create Ubuntu 22.04 Droplet
# Size: Basic - $12/mo (2GB RAM, 1 vCPU, 50GB SSD)
# Region: Choose closest to your users
# Enable: Monitoring, IPv6
```

#### 2. Connect & Setup

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Create non-root user
adduser delybot
usermod -aG sudo delybot
su - delybot
```

#### 3. Install Docker

```bash
# Same as AWS steps 3
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### 4. Deploy Application

```bash
# Same as AWS step 4
mkdir delybot-x
cd delybot-x

# Upload files via SCP
# From your local machine:
scp -r microservices/* delybot@your-droplet-ip:~/delybot-x/

# On droplet:
docker-compose up -d --build
```

#### 5. Configure Firewall

```bash
# DigitalOcean Firewall (via web UI)
# Or use ufw:
sudo ufw allow 22/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📝 Complete Testing Checklist

### 1. Local Testing

```bash
# Start services
docker-compose up --build

# Test Order Service
curl http://localhost:8001/

# Create order
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "customer_phone": "9876543210",
    "customer_email": "test@example.com",
    "delivery_address": "Test Address, Ranchi",
    "delivery_location": {
      "latitude": 23.3540,
      "longitude": 85.3350
    },
    "product_name": "Test Product",
    "product_weight": 1.5,
    "priority": 1
  }'

# List orders
curl http://localhost:8001/orders

# Test Drone Service
curl http://localhost:8002/drones

# Assign mission
curl -X POST http://localhost:8002/drones/DRONE_001/assign \
  -H "Content-Type: application/json" \
  -d '{"order_id": "YOUR_ORDER_ID"}'

# Check stats
curl http://localhost:8001/stats
curl http://localhost:8002/stats
```

### 2. Cloud Testing

Replace `localhost` with your cloud IP:

```bash
# Order Service
curl http://your-cloud-ip:8001/

# Drone Service  
curl http://your-cloud-ip:8002/

# Create order (same as local)
# Verify inter-service communication works
```

### 3. Load Testing (Optional)

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test Order Service
ab -n 1000 -c 10 http://your-cloud-ip:8001/

# Results should show:
# - Requests per second: >100
# - No failed requests
```

---

## 🔒 Production Hardening

### 1. Environment Variables

Create `.env` file:
```bash
# .env
ORDER_SERVICE_PORT=8001
DRONE_SERVICE_PORT=8002
DATABASE_PATH=/app/data
LOG_LEVEL=INFO
```

Update `docker-compose.yml`:
```yaml
services:
  order-service:
    env_file:
      - .env
```

### 2. SSL/TLS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 3. Monitoring

```bash
# Install Docker stats
docker stats

# Install cAdvisor (container monitoring)
docker run -d \
  --name=cadvisor \
  -p 8080:8080 \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker/:/var/lib/docker:ro \
  google/cadvisor:latest
```

### 4. Logging

```bash
# View logs
docker-compose logs -f order-service
docker-compose logs -f drone-service

# Export logs
docker-compose logs > delybot-logs.txt
```

### 5. Backup

```bash
# Backup databases
docker exec delybot-order-service cp /app/order_service.db /app/backup/
docker exec delybot-drone-service cp /app/drone_service.db /app/backup/

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T order-service cp /app/order_service.db /app/order_$DATE.db
docker-compose exec -T drone-service cp /app/drone_service.db /app/drone_$DATE.db
```

---

## 🎯 Post-Deployment Checklist

- [ ] ✅ Both services running
- [ ] ✅ Health checks passing
- [ ] ✅ APIs accessible from internet
- [ ] ✅ Inter-service communication working
- [ ] ✅ Databases persisting data
- [ ] ✅ Logs accessible
- [ ] ✅ Firewall configured
- [ ] ✅ SSL certificate installed (production)
- [ ] ✅ Monitoring setup
- [ ] ✅ Backup strategy in place

---

## 📊 Costs

### AWS EC2
- **t2.medium**: $0.0464/hour = ~$34/month
- **Data transfer**: ~$5/month
- **Total**: ~$40/month

### DigitalOcean
- **Basic Droplet**: $12/month (2GB RAM)
- **No data transfer charges** (first 1TB free)
- **Total**: ~$12/month

**Recommended for MVP:** DigitalOcean ($12/month)

---

## 🚀 Scaling (Future)

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  order-service:
    deploy:
      replicas: 3
  drone-service:
    deploy:
      replicas: 2
```

### Kubernetes (Production Scale)
```bash
# Convert to Kubernetes
kubectl create deployment order-service --image=delybot/order-service
kubectl expose deployment order-service --port=8001 --type=LoadBalancer

kubectl create deployment drone-service --image=delybot/drone-service
kubectl expose deployment drone-service --port=8002 --type=LoadBalancer
```

---

## 📞 Support

**INGENIOUSBLUEPRINTS PRIVATE LIMITED**  
CIN: U78300JH2025PTC025180  
Email: support@ingeniousblueprints.com

---

## ✅ SUCCESS CRITERIA

You can now claim **"DelyBot™ X in Production"** when:

1. ✅ Both microservices deployed on cloud
2. ✅ Publicly accessible APIs (e.g., http://your-ip:8001)
3. ✅ Inter-service communication working
4. ✅ Can create orders via API
5. ✅ Can assign drones via API
6. ✅ Data persists across restarts

**Next: Share your deployment URL!** 🎉

Example:
```
Order Service: http://3.110.123.45:8001
Drone Service: http://3.110.123.45:8002
```

---

**DelyBot™ X - From Code to Cloud** ✓
