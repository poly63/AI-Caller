# SmartCall AI - Quick Start Guide

## 🎯 Getting Started in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- 8GB+ RAM
- 10GB free disk space

### Installation

```bash
# 1. Navigate to project
cd smartcall-ai

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Select option 1 (Full setup)
# Wait for services to start...

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! Your SmartCall AI system is now running.

## 🎪 Testing the System

### Option 1: Use the Test Script
```bash
python3 test_api.py
```

### Option 2: Manual Testing via API Docs

1. Open http://localhost:8000/docs
2. Try the following endpoints:

**Create a Call:**
```json
POST /api/calls/start
{
  "agent_id": "AGENT001",
  "agent_name": "John Doe",
  "customer_number": "+1234567890",
  "customer_name": "Jane Smith",
  "direction": "inbound"
}
```

**Add Transcript & Analyze:**
```bash
# Get the call_id from previous response
# Then end the call
POST /api/calls/{call_id}/end

# Analyze it
POST /api/calls/{call_id}/analyze
```

### Option 3: Use the Dashboard

1. Open http://localhost:3000
2. View real-time statistics
3. Browse recent calls
4. See sentiment analysis

## 📊 Understanding the Dashboard

### Main Metrics
- **Total Calls**: All calls in the system
- **Active Calls**: Currently ongoing calls
- **Avg Score**: Average quality score (0-100)
- **Calls Today**: Calls from today

### Sentiment Distribution
- **Positive**: Happy, satisfied customers
- **Neutral**: Standard interactions
- **Negative**: Unhappy customers
- **Angry**: Critical issues requiring attention

### Call Scoring
Each call is scored on:
- Greeting Quality (10 points)
- Compliance (20 points)
- Customer Satisfaction (30 points)
- Call Clarity (20 points)
- Resolution (20 points)

## 🔌 Integrating with Your Phone System

### Asterisk Integration Example

```bash
# In your Asterisk dialplan
exten => _X.,1,Answer()
    same => n,MixMonitor(/tmp/call_${UNIQUEID}.wav)
    same => n,AGI(smartcall-agi.py,${CALLERID(num)})
    same => n,Dial(SIP/${EXTEN})
    same => n,Hangup()
```

### Python AGI Script (smartcall-agi.py)
```python
#!/usr/bin/env python3
import requests
import sys

API_URL = "http://localhost:8000/api"

# Get caller info
caller_id = sys.argv[1] if len(sys.argv) > 1 else "unknown"

# Start call in SmartCall AI
response = requests.post(f"{API_URL}/calls/start", json={
    "agent_id": "AUTO",
    "customer_number": caller_id,
    "direction": "inbound"
})

call_id = response.json()['id']
print(f"SmartCall Call ID: {call_id}")

# After call, send audio for transcription
# (Implementation depends on your setup)
```

### MicroSIP + Asterisk Auto Bridge (from zip watcher flow)

If your calls are being recorded by Asterisk in `/var/spool/asterisk/monitor`, run this bridge:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python scripts/asterisk_bridge.py
```

Optional env vars:

```bash
export ASTERISK_MONITOR_DIR=/var/spool/asterisk/monitor
export SMARTCALL_API_BASE=http://127.0.0.1:8000/api
export SMARTCALL_TARGET_LANG=hi
```

What it does:
- detects new `.wav` recordings
- waits for file completion
- converts to 16k mono
- transcribes with faster-whisper
- pushes transcript to SmartCall API
- auto ends/analyzes the call

## 🚀 Next Steps

### 1. Customize Scoring Rules
Edit `backend/app/services/scoring.py` to adjust:
- Greeting phrases
- Compliance keywords
- Scoring weights

### 2. Add Custom Sentiment Model
Update `backend/app/services/sentiment.py`:
```python
analyzer = SentimentAnalyzer(
    model_name="your-custom-model"
)
```

### 3. Configure AI Summary
Add OpenAI API key in `backend/.env`:
```env
OPENAI_API_KEY=sk-your-key-here
```

### 4. Enable GPU Acceleration
In `backend/app/main.py`:
```python
get_transcription_service(model_size="small", device="cuda")
```

## 🔧 Common Tasks

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Restart Services
```bash
docker-compose restart
```

### Stop Everything
```bash
docker-compose down
```

### Reset Database
```bash
docker-compose down -v
docker-compose up -d postgres
cd backend && python -m app.database
```

### Update Code
```bash
git pull
docker-compose up -d --build
```

## 📱 API Examples

### Python
```python
import requests

API_URL = "http://localhost:8000/api"

# Create call
response = requests.post(f"{API_URL}/calls/start", json={
    "agent_id": "AGENT001",
    "customer_number": "+1234567890"
})
call = response.json()

# Get dashboard stats
stats = requests.get(f"{API_URL}/analytics/dashboard").json()
print(f"Total calls: {stats['total_calls']}")
```

### JavaScript
```javascript
const API_URL = 'http://localhost:8000/api';

// Create call
const response = await fetch(`${API_URL}/calls/start`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_id: 'AGENT001',
    customer_number: '+1234567890'
  })
});
const call = await response.json();

// Get dashboard stats
const stats = await fetch(`${API_URL}/analytics/dashboard`).then(r => r.json());
console.log('Total calls:', stats.total_calls);
```

### cURL
```bash
# Create call
curl -X POST http://localhost:8000/api/calls/start \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGENT001",
    "customer_number": "+1234567890"
  }'

# Get dashboard stats
curl http://localhost:8000/api/analytics/dashboard
```

## 🎓 Learning Resources

### Understanding the Stack
- **FastAPI**: Modern Python web framework - [docs](https://fastapi.tiangolo.com/)
- **Whisper**: Speech recognition - [paper](https://arxiv.org/abs/2212.04356)
- **Transformers**: NLP library - [docs](https://huggingface.co/docs/transformers)
- **React**: Frontend framework - [docs](https://react.dev/)

### Extending the System
1. **Add new AI features**: Edit files in `backend/app/services/`
2. **Customize UI**: Edit files in `frontend/src/`
3. **Add new endpoints**: Edit `backend/app/main.py`
4. **Modify database**: Edit `backend/app/models.py`

## ❓ FAQ

**Q: Can I use this for production?**
A: Yes, but follow the production deployment guide in DEPLOYMENT.md

**Q: Do I need an OpenAI API key?**
A: No, the system works without it using rule-based summaries

**Q: Can I use a different database?**
A: Yes, modify DATABASE_URL in backend/.env

**Q: How do I add more AI models?**
A: Install via pip and import in the services files

**Q: Can I customize the scoring algorithm?**
A: Yes, edit backend/app/services/scoring.py

## 🆘 Getting Help

- Check logs: `docker-compose logs -f`
- Run tests: `python3 test_api.py`
- Review API docs: http://localhost:8000/docs
- See full docs: README.md and DEPLOYMENT.md

## 🎉 You're Ready!

Your SmartCall AI system is now operational. Start creating calls, analyzing conversations, and gaining insights from your call data!

For advanced features and production deployment, see DEPLOYMENT.md
