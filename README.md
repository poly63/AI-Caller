# SmartCall AI - Real-Time Call Intelligence System

## 🚀 Project Overview

SmartCall AI is an advanced call intelligence platform that provides:
- **Real-time call transcription**
- **AI-powered summaries**
- **Sentiment analysis**
- **Automated call scoring**
- **Interactive analytics dashboard**

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (for frontend)
- FFmpeg
- 8GB+ RAM (16GB recommended)
- Optional: NVIDIA GPU for faster processing

## 🛠️ Tech Stack

### Backend
- FastAPI (API framework)
- Faster-Whisper (speech-to-text)
- HuggingFace Transformers (NLP)
- PostgreSQL (database)
- WebSockets (real-time streaming)

### Frontend
- React 18
- Tailwind CSS
- Chart.js
- WebSocket client

### AI Models
- Faster-Whisper (transcription)
- DistilBERT (sentiment analysis)
- GPT-compatible API (summaries)

## 📁 Project Structure

```
smartcall-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # Database models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── database.py          # DB connection
│   │   ├── services/
│   │   │   ├── transcription.py # Whisper integration
│   │   │   ├── sentiment.py     # Sentiment analysis
│   │   │   ├── summary.py       # AI summary
│   │   │   └── scoring.py       # Call scoring
│   │   └── routes/
│   │       ├── calls.py         # Call endpoints
│   │       └── analytics.py     # Analytics endpoints
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔧 Installation

### 1. Clone and Setup

```bash
git clone <your-repo>
cd smartcall-ai
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb smartcall_ai

# Run migrations (or use Alembic)
python -m app.database
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Environment Variables

Create `.env` file in backend/:

```env
DATABASE_URL=postgresql://user:password@localhost/smartcall_ai
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key  # Optional for summaries
```

## 🚀 Running the Application

### Using Docker (Recommended)

```bash
docker-compose up --build
```

### Manual Setup

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm start
```

**Access:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## 🏭 Production Deployment

Production artifacts are available in `infrastructure/`:

- `infrastructure/docker-compose.production.yml`
- `infrastructure/nginx.conf`
- `infrastructure/AZURE_DEPLOYMENT_CHECKLIST.md`
- root `.env.example`

Quick start:

```bash
cp .env.example .env
cd infrastructure
docker compose --env-file ../.env -f docker-compose.production.yml up -d --build
```

## 📊 API Endpoints

### Calls
- `POST /api/calls/start` - Start new call recording
- `WS /api/calls/stream/{call_id}` - WebSocket for live transcription
- `GET /api/calls/{call_id}` - Get call details
- `GET /api/calls/` - List all calls
- `POST /api/calls/{call_id}/analyze` - Trigger AI analysis

### Analytics
- `GET /api/analytics/dashboard` - Dashboard stats
- `GET /api/analytics/agent/{agent_id}` - Agent performance
- `GET /api/analytics/sentiment-trends` - Sentiment over time

## 🎯 Features Implementation Status

- [x] Project structure
- [x] Database models
- [x] FastAPI backend setup
- [x] Real-time transcription service
- [x] Sentiment analysis
- [x] AI summary generation
- [x] Call scoring engine
- [x] WebSocket streaming
- [x] REST API endpoints
- [x] React dashboard
- [x] Analytics charts
- [ ] Speaker diarization
- [ ] Fraud detection
- [ ] Emotion analysis

## 🔐 Security

- JWT authentication
- API key validation
- CORS configuration
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)

## 📈 Performance Tips

1. Use GPU for faster transcription
2. Implement Redis caching
3. Use connection pooling for DB
4. Enable gzip compression
5. Implement rate limiting

## 🐛 Troubleshooting

**Whisper model not loading:**
```bash
pip install --upgrade faster-whisper
```

**Database connection error:**
- Check PostgreSQL is running
- Verify DATABASE_URL in .env

**WebSocket connection fails:**
- Check CORS settings
- Verify backend is running

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue first.

## 📧 Contact

For questions or support, please open an issue.
