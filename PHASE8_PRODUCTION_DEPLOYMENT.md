# 🚀 Phase 8: Production Deployment - Complete Guide

**Status**: IN PROGRESS
**Date Started**: 2026-03-27
**Duration**: 4 sequential sub-phases

---

## 📋 Phase 8 Overview

Phase 8 consists of 4 sequential deployment phases to take SpectrumIA from development to production:

1. **Phase 8.1**: Supabase Production Setup
2. **Phase 8.2**: Streamlit Cloud Deployment
3. **Phase 8.3**: Docker Containerization
4. **Phase 8.4**: Monitoring & Logging

---

## 🎯 Phase 8.1: Supabase Production Setup

### Objectives
- Create Supabase production project
- Configure PostgreSQL database
- Apply schema migrations
- Setup authentication and RLS policies
- Configure environment variables

### Prerequisites
- Supabase account
- Access to project credentials
- Database schema (migrations.sql ready)

### Key Tasks

#### 1. Create Supabase Project
```bash
# Login to Supabase dashboard
https://app.supabase.com

# Steps:
1. Create new project
2. Select region (closest to users)
3. Configure authentication
4. Save project credentials
```

#### 2. Apply Database Migrations
```bash
# Install Supabase CLI
npm install -g @supabase/cli

# Login to Supabase
supabase login

# Apply migrations to production
supabase migration up --project-id YOUR_PROJECT_ID
```

#### 3. Configure RLS (Row Level Security)
- Enable RLS on all tables
- Create policies for users table
- Create policies for assessments
- Create policies for results

#### 4. Setup Authentication
- Enable email/password authentication
- Configure SMTP for email verification
- Setup JWT expiration (1 week access, 30 days refresh)
- Create authentication hooks

#### 5. Create Environment Variables
```env
# .env.production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://user:password@host/database
```

### Deliverables
- ✅ Supabase project created
- ✅ Database schema applied
- ✅ RLS policies configured
- ✅ Authentication setup
- ✅ .env.production file created

### Estimated Time: 2-3 hours

---

## 🎯 Phase 8.2: Streamlit Cloud Deployment

### Objectives
- Deploy Streamlit app to Streamlit Cloud
- Configure secrets management
- Setup CI/CD for auto-deployment
- Configure domain/custom URL

### Prerequisites
- GitHub account and repository
- Streamlit Cloud account
- Supabase credentials from Phase 8.1

### Key Tasks

#### 1. Prepare for Deployment
```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt

# Create secrets.toml for local testing
mkdir -p ~/.streamlit
cat > ~/.streamlit/secrets.toml << 'EOF'
SUPABASE_URL = "your-url"
SUPABASE_ANON_KEY = "your-key"
EOF
```

#### 2. Deploy to Streamlit Cloud
```
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect GitHub repository
4. Select branch: main
5. Set main file path: app/main.py
6. Click Deploy
```

#### 3. Configure Secrets
In Streamlit Cloud dashboard:
1. Go to Settings
2. Secrets section
3. Add all environment variables:
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - API keys
   - etc.

#### 4. Setup Auto-deployment
- Enable auto-deploy on push to main
- Configure webhook notifications
- Setup GitHub Actions for automated testing before deployment

#### 5. Configure Custom Domain (Optional)
```
1. Buy domain (Namecheap, Google Domains, etc.)
2. In Streamlit Cloud: Settings → Custom domain
3. Add DNS CNAME record pointing to Streamlit
4. Verify and activate
```

### Deployment Command
```bash
# Push to GitHub (triggers auto-deployment)
git add .
git commit -m "feat: prepare for production deployment"
git push origin main

# Streamlit Cloud automatically deploys
```

### Deliverables
- ✅ App deployed to Streamlit Cloud
- ✅ Secrets configured
- ✅ Auto-deployment working
- ✅ Health check passing
- ✅ Custom domain configured (optional)

### Estimated Time: 30 minutes - 1 hour

### Access
```
https://spectrumia.streamlit.app
# or custom domain after Phase 8.4
```

---

## 🎯 Phase 8.3: Docker Containerization

### Objectives
- Create Dockerfile for application
- Create docker-compose for full stack
- Build and test Docker image
- Document containerization

### Prerequisites
- Docker installed locally
- Docker Hub account (optional, for image registry)

### Key Tasks

#### 1. Create Dockerfile
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "app/main.py"]
```

#### 2. Create docker-compose.yml
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_PORT=8501
    env_file:
      - .env.production
    depends_on:
      - postgres
    networks:
      - spectrumia-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./models/migrations.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - spectrumia-network

volumes:
  postgres_data:

networks:
  spectrumia-network:
    driver: bridge
```

#### 3. Build and Test Locally
```bash
# Build image
docker build -t spectrumia:latest .

# Run with docker-compose
docker-compose up

# Test endpoint
curl http://localhost:8501

# View logs
docker-compose logs -f app
```

#### 4. Push to Docker Registry (Optional)
```bash
# Login to Docker Hub
docker login

# Tag image
docker tag spectrumia:latest username/spectrumia:latest

# Push
docker push username/spectrumia:latest
```

### Deliverables
- ✅ Dockerfile created and tested
- ✅ docker-compose.yml configured
- ✅ Image builds successfully
- ✅ Container runs and passes health checks
- ✅ Documentation for Docker usage

### Estimated Time: 1-2 hours

### Run Locally
```bash
docker-compose up -d
# App available at http://localhost:8501
```

---

## 🎯 Phase 8.4: Monitoring & Logging

### Objectives
- Setup application logging
- Configure metrics collection
- Create monitoring dashboards
- Setup alerting system

### Prerequisites
- Monitoring service account
- Logging infrastructure

### Key Tasks

#### 1. Application Logging Setup
```python
# core/logging_config.py
import logging
import logging.handlers
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler with rotation
    handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )

    # JSON formatter for structured logging
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

#### 2. Metrics Collection
```python
# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
requests_total = Counter(
    'requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration',
    ['endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

calibration_success = Counter(
    'calibration_success_total',
    'Successful calibrations'
)

assessment_completions = Counter(
    'assessment_completions_total',
    'Completed assessments'
)
```

#### 3. Logging Integration in Streamlit
```python
# app/main.py
import logging
from core.logging_config import setup_logging

logger = setup_logging()

def log_event(event_type, data):
    logger.info(
        f"Event: {event_type}",
        extra={
            'event_type': event_type,
            'user_id': data.get('user_id'),
            'timestamp': datetime.utcnow().isoformat(),
            **data
        }
    )

# Usage
log_event('calibration_started', {
    'user_id': user_id,
    'session_id': session_id
})
```

#### 4. Monitoring Dashboard
Setup with popular services:

**Option A: Datadog**
- Send logs to Datadog
- Create dashboards for:
  - Request rates and latency
  - Error rates
  - Active users
  - Assessment metrics
  - System health

**Option B: ELK Stack (Elasticsearch, Logstash, Kibana)**
- Ship logs to Elasticsearch
- Parse with Logstash
- Visualize in Kibana

**Option C: Grafana + Prometheus**
- Expose metrics endpoint
- Scrape with Prometheus
- Visualize in Grafana

#### 5. Alerting Rules
```yaml
# Example Prometheus alerts
groups:
  - name: spectrumia
    rules:
      - alert: HighErrorRate
        expr: rate(requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: High error rate detected

      - alert: HighLatency
        expr: histogram_quantile(0.95, request_duration_seconds) > 1.0
        for: 5m
        annotations:
          summary: Request latency is high

      - alert: LowCalibrationSuccess
        expr: rate(calibration_success_total[1h]) < 0.8
        for: 15m
        annotations:
          summary: Calibration success rate is low
```

#### 6. Health Check Endpoint
```python
# app/pages/health.py
import streamlit as st
from datetime import datetime

def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.1.0',
        'database': check_database_health(),
        'services': {
            'supabase': check_supabase_health(),
            'cache': check_cache_health(),
        }
    }
```

### Deliverables
- ✅ Logging system configured
- ✅ Metrics collection working
- ✅ Dashboard created
- ✅ Alerts configured
- ✅ Health check endpoint active

### Estimated Time: 2-3 hours

---

## 📊 Phase 8 Timeline

```
Phase 8.1: Supabase Setup
├─ Create project               (30 min)
├─ Apply migrations             (30 min)
├─ Configure RLS                (45 min)
├─ Setup authentication         (30 min)
└─ Create .env file             (15 min)
   Total: ~2.5 hours

Phase 8.2: Streamlit Deployment
├─ Prepare for deployment       (15 min)
├─ Deploy to cloud              (20 min)
├─ Configure secrets            (15 min)
└─ Setup auto-deployment        (10 min)
   Total: ~1 hour

Phase 8.3: Docker
├─ Create Dockerfile            (30 min)
├─ Create docker-compose        (30 min)
├─ Build and test               (30 min)
└─ Documentation                (15 min)
   Total: ~1.5 hours

Phase 8.4: Monitoring
├─ Setup logging                (45 min)
├─ Configure metrics            (45 min)
├─ Create dashboards            (45 min)
└─ Setup alerts                 (30 min)
   Total: ~2.5 hours

TOTAL PHASE 8 TIME: ~7-8 hours
```

---

## ✅ Pre-deployment Checklist

Before Phase 8.1:
- [ ] Review all code in main branch
- [ ] Run full test suite: `make test`
- [ ] Check coverage: `make test-coverage`
- [ ] Run quality checks: `make quality-check`
- [ ] Update documentation
- [ ] Verify .env.example matches required vars
- [ ] Test migrations locally

---

## 🚨 Production Safety Guidelines

### Backup Strategy
```bash
# Create database backup before major changes
supabase db push --remote
supabase db pull --remote > backup.sql
```

### Rollback Plan
1. Keep previous version of app available
2. Keep database snapshots
3. Document deployment steps
4. Have rollback procedures documented

### Secrets Management
- Never commit .env files
- Use service for secrets (not hardcoded)
- Rotate keys regularly
- Monitor key usage

### Performance Monitoring
- Monitor response times
- Track database queries
- Watch memory usage
- Monitor disk space

---

## 📚 Documentation to Create

During Phase 8:
1. **Deployment Guide** - Step-by-step deployment instructions
2. **Operations Manual** - Running and maintaining production
3. **Troubleshooting Guide** - Common issues and solutions
4. **Disaster Recovery** - Backup and recovery procedures

---

## 🎯 Success Criteria

Phase 8 is complete when:
- ✅ App accessible via Streamlit Cloud
- ✅ All services communicating properly
- ✅ Database migrations applied
- ✅ Logs being collected
- ✅ Metrics being tracked
- ✅ Docker image builds successfully
- ✅ Health checks passing
- ✅ Documentation complete

---

## 🔗 Reference Files

Will be created during Phase 8:
- `docker-compose.yml`
- `Dockerfile`
- `.env.production` (template)
- `core/logging_config.py`
- `core/metrics.py`
- `DEPLOYMENT_GUIDE.md`
- `OPERATIONS_MANUAL.md`
- `TROUBLESHOOTING.md`

---

## 📞 Support

During deployment:
1. Check GitHub Actions for CI/CD status
2. Monitor Streamlit Cloud dashboard
3. Review application logs
4. Check monitoring dashboards
5. Verify health endpoints

---

**Phase 8: Production Deployment - IN PROGRESS**

Starting with Phase 8.1: Supabase Production Setup

