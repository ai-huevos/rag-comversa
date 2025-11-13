# Comversa Executive Dashboard

Executive dashboard for visualizing consolidated intelligence from 44 manager interviews across Los Tajibos, Comversa, and Bolivian Foods.

## Features

- **Real-time Metrics**: 1,743 consolidated entities from PostgreSQL + Neo4j
- **Company Analytics**: Distribution by company with process and system breakdowns
- **Pain Points**: Critical pain points with priority levels and impact analysis
- **Systems Tracking**: Technology systems categorized by criticality
- **Process Frequency**: Distribution of daily, weekly, monthly, and annual processes
- **Spanish-First**: All content preserved in Spanish from database

## Tech Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.9), PostgreSQL 15 + pgvector, Neo4j 5.16
- **Icons**: Lucide React
- **Charts**: Recharts (coming soon)

## Quick Start

### Local Development (Without Docker)

1. **Start PostgreSQL and Neo4j**
   ```bash
   # Make sure PostgreSQL is running on port 5432
   # Make sure Neo4j is running on ports 7474/7687
   ```

2. **Start the API**
   ```bash
   ./scripts/start_api.sh
   # API will run on http://localhost:8000
   # Docs available at http://localhost:8000/api/docs
   ```

3. **Start the Dashboard** (in a new terminal)
   ```bash
   ./scripts/start_dashboard.sh
   # Dashboard will run on http://localhost:3000
   ```

4. **Open Dashboard**
   - Navigate to http://localhost:3000
   - Dashboard will automatically fetch data from the API

### Using Docker Compose

```bash
# Start all services (PostgreSQL, Neo4j, API, Dashboard)
docker-compose up -d

# View logs
docker-compose logs -f dashboard

# Stop all services
docker-compose down
```

## Project Structure

```
dashboard/
├── app/
│   ├── layout.tsx          # Root layout with Spanish i18n
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Global styles with brand colors
├── lib/
│   └── api.ts              # API client for backend
├── components/             # Reusable components (future)
├── public/                 # Static assets
└── package.json            # Dependencies

api/
├── main.py                 # FastAPI app entry point
├── models/
│   └── schemas.py          # Pydantic models
├── routers/
│   ├── dashboard.py        # Dashboard data endpoints
│   └── entities.py         # Entity CRUD endpoints
└── services/
    └── postgres_service.py # PostgreSQL queries
```

## API Endpoints

### Dashboard Data
- `GET /api/dashboard` - Complete dashboard data
- `GET /api/dashboard/summary` - Summary statistics only
- `GET /api/dashboard/companies` - Company distribution
- `GET /api/dashboard/pain-points?limit=10` - Critical pain points

### Entities
- `GET /api/entities` - List entities with filters
  - Query params: `entity_type`, `company`, `search`, `page`, `page_size`
- `GET /api/entities/{id}` - Entity details
- `GET /api/entities/types/available` - Available entity types
- `GET /api/entities/companies/available` - Available companies

### Health
- `GET /api/health` - API health check

## Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://postgres@localhost:5432/comversa_rag
DB_TYPE=postgresql

# Neo4j
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=comversa_neo4j_2025

# Dashboard (optional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Brand Colors

```typescript
const BRAND = {
  yellow: '#FFD826',      // Primary brand color
  dark: '#101010',        // Text and headers
  gray: '#8A8A8A',        // Secondary text
  white: '#FFFFFF',       // Backgrounds
  lightGray: '#F5F5F5',   // Page background
  errorRed: '#DC2626',    // Critical alerts
  successGreen: '#16A34A', // Success indicators
  warningOrange: '#EA580C' // Warnings
};
```

## Development

### Install Dependencies

```bash
cd dashboard
npm install
```

### Run Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
npm start
```

### Lint Code

```bash
npm run lint
```

## Future Enhancements

- [ ] Add Neo4j graph visualization
- [ ] Implement real-time analytics with WebSockets
- [ ] Add authentication (OAuth/JWT)
- [ ] Export functionality (PDF, CSV, JSON)
- [ ] Advanced filtering and search
- [ ] Recharts integration for advanced visualizations
- [ ] Mobile responsive optimizations
- [ ] Dark mode toggle

## Troubleshooting

### API Connection Issues

If dashboard shows "Error al cargar datos":

1. **Check API is running**: http://localhost:8000/api/health
2. **Check database connection**: `psql -U postgres -d comversa_rag -c "SELECT COUNT(*) FROM consolidated_entities;"`
3. **Check CORS**: API allows localhost:3000 by default
4. **Check logs**: `docker-compose logs api`

### Port Conflicts

If ports are already in use:

- API (8000): Change in `api/main.py` and update `NEXT_PUBLIC_API_URL`
- Dashboard (3000): Change in `package.json` dev script
- PostgreSQL (5432): Change `DATABASE_URL` in `.env`
- Neo4j (7474, 7687): Change Neo4j config

## Support

For issues or questions about the dashboard:

- Review [CLAUDE.md](../CLAUDE.md) for project overview
- Check FastAPI docs: http://localhost:8000/api/docs
- Verify database status in PostgreSQL and Neo4j
- Check project structure in [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
