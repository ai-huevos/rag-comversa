# Executive Dashboard - Complete Setup Guide

Complete implementation of the Comversa Executive Dashboard with FastAPI backend and Next.js frontend.

## 📊 What's Implemented

### ✅ Backend (FastAPI)
- **PostgreSQL Integration**: All 1,743 consolidated entities queryable via REST API
- **Dashboard Aggregation**: Complete data pipeline for metrics, companies, pain points, systems
- **Entity Endpoints**: List, filter, search, and detail views for all entities
- **Spanish-First**: All database content preserved in Spanish (never translated)
- **Health Checks**: Database connectivity monitoring
- **CORS Configured**: Frontend can connect from localhost:3000

### ✅ Frontend (Next.js 14)
- **Real-time Data**: Fetches live data from PostgreSQL via API
- **Brand Styling**: Comversa colors (#FFD826 yellow, #101010 dark, #8A8A8A gray)
- **Key Metrics**: Total entities, processes, systems, employees
- **Company Analytics**: Distribution by Los Tajibos, Comversa, Bolivian Foods
- **Pain Points Table**: Critical pain points with priority levels and impact
- **Systems Breakdown**: Categorized by criticality (critical, important, support)
- **Process Frequency**: Daily, weekly, monthly, annual distribution
- **Error Handling**: Loading states, error messages, retry functionality
- **Responsive Design**: Tailwind CSS with mobile support

### ✅ Deployment
- **Docker Compose**: Single-command deployment of all services
- **Local Scripts**: Start API and dashboard separately for development
- **Health Checks**: Automatic service health monitoring
- **Environment Config**: .env file management

---

## 🚀 Quick Start (3 Steps)

### Step 1: Start the API

```bash
cd /Users/tatooine/Documents/Development/Comversa/system0

# Make sure PostgreSQL and Neo4j are running
# Start the FastAPI backend
./scripts/start_api.sh
```

The API will start on **http://localhost:8000**
- API Docs: http://localhost:8000/api/docs
- Dashboard Data: http://localhost:8000/api/dashboard
- Health Check: http://localhost:8000/api/health

### Step 2: Start the Dashboard (New Terminal)

```bash
cd /Users/tatooine/Documents/Development/Comversa/system0

# Start the Next.js dashboard
./scripts/start_dashboard.sh
```

The dashboard will start on **http://localhost:3000**

### Step 3: Open Dashboard

Navigate to **http://localhost:3000** in your browser.

You should see:
- 1,743 total entities
- Distribution across 3 companies
- Critical pain points table
- Systems breakdown (critical, important, support)
- Process frequency charts

---

## 🐳 Alternative: Docker Compose

Start everything with one command:

```bash
# Start all services (PostgreSQL, Neo4j, API, Dashboard)
docker-compose up -d

# View dashboard logs
docker-compose logs -f dashboard

# Stop all services
docker-compose down
```

Services:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Neo4j: http://localhost:7474

---

## 📁 Project Structure

```
system0/
├── api/                              # FastAPI Backend
│   ├── main.py                       # App entry point
│   ├── routers/
│   │   ├── dashboard.py              # Dashboard endpoints
│   │   └── entities.py               # Entity CRUD
│   ├── services/
│   │   └── postgres_service.py       # PostgreSQL queries
│   ├── models/
│   │   └── schemas.py                # Pydantic models
│   └── requirements.txt              # Python dependencies
│
├── dashboard/                         # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx                  # Main dashboard
│   │   ├── layout.tsx                # Root layout
│   │   └── globals.css               # Global styles
│   ├── lib/
│   │   └── api.ts                    # API client
│   ├── package.json                  # Node dependencies
│   └── README.md                     # Dashboard docs
│
├── scripts/
│   ├── start_api.sh                  # Start FastAPI
│   └── start_dashboard.sh            # Start Next.js
│
├── docker-compose.yml                 # Docker orchestration
├── Dockerfile.api                     # API container
└── DASHBOARD_SETUP.md                 # This file
```

---

## 🔌 API Endpoints Reference

### Dashboard Data

```bash
# Complete dashboard data (all metrics, companies, pain points, systems)
curl http://localhost:8000/api/dashboard

# Summary statistics only
curl http://localhost:8000/api/dashboard/summary

# Company distribution only
curl http://localhost:8000/api/dashboard/companies

# Critical pain points (limit 10)
curl http://localhost:8000/api/dashboard/pain-points?limit=10
```

### Entity Queries

```bash
# List all entities (paginated)
curl http://localhost:8000/api/entities?page=1&page_size=50

# Filter by entity type
curl http://localhost:8000/api/entities?entity_type=pain_point

# Filter by company
curl http://localhost:8000/api/entities?company=Los%20Tajibos

# Search by name
curl http://localhost:8000/api/entities?search=SAP

# Combined filters
curl "http://localhost:8000/api/entities?entity_type=process&company=Comversa&page=1"

# Get entity detail
curl http://localhost:8000/api/entities/42

# Get available entity types
curl http://localhost:8000/api/entities/types/available

# Get available companies
curl http://localhost:8000/api/entities/companies/available
```

### Health Check

```bash
# API health status
curl http://localhost:8000/api/health
```

---

## 🎨 Dashboard Features

### Key Metrics Cards
- **Total Entities**: 1,743 consolidated entities
- **Macro Processes**: 170 processes (60% daily frequency)
- **Technology Systems**: 183 systems (3 critical, 7 important)
- **Employees**: 17 interviewed across 44 sessions

### Company Distribution
- **Los Tajibos**: ~70 processes, ~65 systems, 1 employee
- **Bolivian Foods**: ~58 processes, ~72 systems, 9 employees
- **Comversa**: ~42 processes, ~46 systems, 7 employees

### Pain Points Table
- Title, priority (Crítica/Alta/Media), impact, time saved
- Sortable and filterable
- Click-through to entity details (coming soon)

### Systems Breakdown
- **3 Critical**: SAP, Opera, Simphony
- **7 Important**: Excel, MaintainX, Jira
- **30 Support**: Teams, WhatsApp, Office
- **183 Total**

### Process Frequency
- **Daily**: ~60% of processes
- **Weekly**: ~16%
- **Monthly**: ~15%
- **Annual**: ~9%

---

## 🔧 Configuration

### Environment Variables

Create `.env` in project root:

```bash
# PostgreSQL
DATABASE_URL=postgresql://postgres@localhost:5432/comversa_rag
DB_TYPE=postgresql

# Neo4j
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=comversa_neo4j_2025

# Dashboard (optional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Brand Colors

```typescript
BRAND = {
  yellow: '#FFD826',      // Primary accent
  dark: '#101010',        // Text/headers
  gray: '#8A8A8A',        // Secondary text
  lightGray: '#F5F5F5',   // Backgrounds
  errorRed: '#DC2626',    // Critical alerts
  warningOrange: '#EA580C', // Warnings
  successGreen: '#16A34A'   // Success states
}
```

---

## 🐛 Troubleshooting

### Dashboard shows "Error al cargar datos"

1. **Check API is running**:
   ```bash
   curl http://localhost:8000/api/health
   # Should return: {"status":"healthy","database":"connected",...}
   ```

2. **Check database connection**:
   ```bash
   psql -U postgres -d comversa_rag -c "SELECT COUNT(*) FROM consolidated_entities;"
   # Should return: 1743
   ```

3. **Check CORS configuration**:
   - API allows `localhost:3000` by default
   - Check `api/main.py` CORS middleware

4. **View API logs**:
   ```bash
   # If using Docker
   docker-compose logs api
   ```

### Port Conflicts

**API (8000) already in use**:
- Change port in `api/main.py`: `uvicorn.run(..., port=8001)`
- Update `NEXT_PUBLIC_API_URL` in dashboard

**Dashboard (3000) already in use**:
- Change in `package.json`: `"dev": "next dev -p 3001"`

### Database Not Found

```bash
# Create database if it doesn't exist
psql -U postgres -c "CREATE DATABASE comversa_rag;"

# Run migrations
psql -U postgres -d comversa_rag -f scripts/migrations/2025_01_01_pgvector.sql
```

### Missing Dependencies

**API**:
```bash
pip3 install -r api/requirements.txt
```

**Dashboard**:
```bash
cd dashboard
npm install
```

---

## 📈 Next Steps (Future Enhancements)

### Pending Features
- [ ] Neo4j graph visualization (Task 2)
- [ ] Authentication/authorization (Task 4)
- [ ] Export functionality - PDF/CSV/JSON (Task 7)
- [ ] Advanced search and filtering
- [ ] Real-time analytics with WebSockets
- [ ] Recharts integration for interactive charts
- [ ] Mobile app companion

### Implementation Priority
1. **Entity Search Page**: Filterable list with drill-down
2. **Graph Visualization**: Neo4j relationships explorer
3. **Export Features**: PDF reports, CSV exports
4. **Authentication**: Single-user login for now
5. **Real-time Updates**: WebSocket for live data

---

## 🎯 Current Status

### ✅ Completed (Today)
- FastAPI backend with PostgreSQL integration
- Next.js dashboard with real-time data fetching
- Company analytics and distribution charts
- Pain points table with priority levels
- Systems breakdown by criticality
- Process frequency visualization
- Docker Compose deployment configuration
- Local development scripts

### ⏳ Pending
- Neo4j graph query endpoints (backend exists, needs frontend)
- Authentication and authorization
- Export functionality (PDF, CSV, JSON)

### 🎉 Ready to Use
The dashboard is **fully functional** for:
- Viewing consolidated entity metrics
- Exploring company distributions
- Analyzing critical pain points
- Understanding systems landscape
- Tracking process frequencies

---

## 📞 Support

For help:
1. Check API docs: http://localhost:8000/api/docs
2. Review [CLAUDE.md](./CLAUDE.md) for project context
3. Check [dashboard/README.md](./dashboard/README.md) for frontend details
4. Verify database: `psql -U postgres -d comversa_rag`

**Last Updated**: November 13, 2025
**Status**: Production-ready for local deployment
