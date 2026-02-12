# SmartCall AI - Deployment Guide

## 🚀 Quick Start (Development)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
cd smartcall-ai

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Choose option 1 for full setup
```

### Option 2: Manual Setup

#### 1. Start PostgreSQL
```bash
docker run -d \
  --name smartcall-postgres \
  -e POSTGRES_USER=smartcall \
  -e POSTGRES_PASSWORD=smartcall123 \
  -e POSTGRES_DB=smartcall_ai \
  -p 5432:5432 \
  postgres:15-alpine
```

#### 2. Setup Backend
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://smartcall:smartcall123@localhost:5432/smartcall_ai
SECRET_KEY=$(openssl rand -hex 32)
OPENAI_API_KEY=your-key-here  # Optional
EOF

# Initialize database
python -m app.database

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Setup Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

## 🌐 Production Deployment

### AWS EC2 / DigitalOcean / VPS

#### 1. Server Requirements
- Ubuntu 22.04 LTS
- 16GB RAM (minimum 8GB)
- 4 vCPUs (minimum 2)
- 50GB storage
- NVIDIA GPU (optional, for faster transcription)

#### 2. Install Docker & Docker Compose
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### 3. Deploy Application
```bash
# Clone repository
git clone <your-repo>
cd smartcall-ai

# Create production .env
cat > backend/.env << EOF
DATABASE_URL=postgresql://smartcall:$(openssl rand -hex 16)@postgres:5432/smartcall_ai
SECRET_KEY=$(openssl rand -hex 32)
OPENAI_API_KEY=your-production-key
EOF

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### 4. Setup Nginx (Reverse Proxy)
```bash
sudo apt install nginx -y

# Create Nginx config
sudo tee /etc/nginx/sites-available/smartcall << EOF
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/smartcall /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Setup SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### Docker Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: smartcall_ai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - smartcall

  backend:
    build: ./backend
    restart: always
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/smartcall_ai
      SECRET_KEY: ${SECRET_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - postgres
    networks:
      - smartcall

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: https://your-domain.com
    restart: always
    depends_on:
      - backend
    networks:
      - smartcall

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    networks:
      - smartcall

networks:
  smartcall:

volumes:
  postgres_data:
```

## 🔧 Production Optimizations

### 1. Use GPU for Transcription
```python
# In backend/app/services/transcription.py
get_transcription_service(model_size="small", device="cuda")
```

### 2. Enable Redis Caching
```bash
# Add to docker-compose.yml
redis:
  image: redis:7-alpine
  restart: always
```

```python
# In backend, install redis
pip install redis

# Use for caching
import redis
cache = redis.Redis(host='redis', port=6379)
```

### 3. Setup Background Tasks (Celery)
```python
# backend/celery_worker.py
from celery import Celery

celery = Celery('smartcall', broker='redis://redis:6379/0')

@celery.task
def analyze_call_async(call_id):
    # Perform analysis in background
    pass
```

### 4. Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_calls_agent_id ON calls(agent_id);
CREATE INDEX idx_calls_created_at ON calls(created_at);
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_calls_sentiment ON calls(sentiment);
```

### 5. Monitoring Setup
```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
```

## 🔒 Security Checklist

- [ ] Change default database password
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Use environment variables for secrets
- [ ] Enable firewall (UFW)
- [ ] Regular security updates
- [ ] Implement API authentication (JWT)
- [ ] Database backups

## 📊 Performance Tuning

### Backend
- Use Gunicorn with multiple workers: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`
- Enable connection pooling in SQLAlchemy
- Cache frequently accessed data in Redis
- Use async database queries

### Database
- Regular VACUUM operations
- Optimize query plans
- Use read replicas for analytics
- Implement connection pooling

### Frontend
- Build for production: `npm run build`
- Enable gzip compression
- Use CDN for static assets
- Implement lazy loading

## 🔄 Backup Strategy

```bash
# Database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec smartcall-postgres pg_dump -U smartcall smartcall_ai > backup_$DATE.sql
```

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (Nginx, HAProxy)
- Multiple backend instances
- Separate database server
- Redis cluster for caching

### Vertical Scaling
- Increase RAM for AI models
- Add GPU for faster processing
- Increase database storage

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check logs
docker-compose logs backend

# Check database connection
docker-compose exec backend python -c "from app.database import engine; print(engine.connect())"
```

**Model loading errors:**
```bash
# Clear model cache
rm -rf ~/.cache/huggingface

# Reinstall transformers
pip install --upgrade transformers torch
```

**Database connection issues:**
```bash
# Check PostgreSQL
docker-compose exec postgres psql -U smartcall -d smartcall_ai

# Reset database
docker-compose down -v
docker-compose up -d postgres
python -m app.database
```

## 📚 Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- HuggingFace Transformers: https://huggingface.co/docs/transformers
- PostgreSQL Best Practices: https://wiki.postgresql.org/
- Docker Best Practices: https://docs.docker.com/develop/

## 🎯 Next Steps

1. Integrate with Asterisk/FreePBX for real call capture
2. Implement speaker diarization
3. Add fraud detection AI
4. Build mobile apps (React Native)
5. Implement real-time alerts (Slack, email)
6. Add multi-language support
7. Create admin dashboard
8. Implement role-based access control
