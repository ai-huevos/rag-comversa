# Comversa Executive Dashboard

## Descripción

Dashboard ejecutivo para visualizar inteligencia consolidada de 44 entrevistas de empleados de Los Tajibos, Comversa y Bolivian Foods.

**Fuente de Datos:** PostgreSQL + Neo4j (1,743 entidades consolidadas)

---

## Brand Guidelines

### Colores
- **Amarillo Principal:** `#FFD826` - Marca, highlights, CTAs
- **Texto Oscuro:** `#101010` - Encabezados, texto principal
- **Gris Secundario:** `#8A8A8A` - Texto secundario, bordes
- **Fondo Claro:** `#F5F5F5` - Background de la aplicación
- **Blanco:** `#FFFFFF` - Cards, contenedores

### Colores de Estado
- **Error/Crítico:** `#DC2626` (rojo)
- **Advertencia/Alta:** `#EA580C` (naranja)
- **Éxito:** `#16A34A` (verde)
- **Medio:** `#8A8A8A` (gris)

---

## Características del Dashboard

### 📊 Métricas Clave
- **1,743** Entidades consolidadas (PostgreSQL + Neo4j)
- **170** Macro procesos identificados
- **183** Sistemas tecnológicos en uso
- **17** Empleados entrevistados (44 entrevistas totales)

### 🏢 Distribución por Empresa
- **Los Tajibos:** 1 empleado | 70 procesos | 65 sistemas
- **Bolivian Foods:** 9 empleados | 58 procesos | 72 sistemas
- **Comversa:** 7 empleados | 42 procesos | 46 sistemas

### 🔥 Pain Points Críticos
1. Integración SAP-Opera-Simphony-Satcom (2-4 horas/día ahorro)
2. Sistema CMMS Integrado (40-60% reducción tiempo)
3. Automatización de Aprobaciones (50% reducción)
4. Implementación DATAWAREHOUSE (80-90% reducción reportería)
5. CRM Funcional (mejora conversión)

### 📈 Análisis de Frecuencia
- **102 procesos** diarios (60%)
- **28 procesos** semanales
- **25 procesos** mensuales
- **15 procesos** anuales

### 🖥️ Sistemas por Criticidad
- **3** Críticos (SAP, Opera, Simphony)
- **7** Importantes (Excel, MaintainX, Jira, etc.)
- **30+** Soporte (Teams, WhatsApp, Office, etc.)

---

## Stack Tecnológico

### Frontend
```json
{
  "framework": "React 18+ con TypeScript",
  "styling": "Tailwind CSS o Styled Components",
  "icons": "lucide-react",
  "charts": "recharts o chart.js",
  "state": "React hooks (useState, useEffect)"
}
```

### Backend (Data Sources)
- **PostgreSQL + pgvector:** Document chunks, embeddings, consolidated entities
- **Neo4j:** Knowledge graph (1,743 entities)
- **SQLite (legacy):** 17 entity tables (durante migración)

---

## Instalación y Setup

### Opción 1: Next.js App (Recomendado)

```bash
# 1. Crear app Next.js con TypeScript
npx create-next-app@latest comversa-dashboard --typescript --tailwind --app

cd comversa-dashboard

# 2. Instalar dependencias
npm install lucide-react recharts

# 3. Copiar el componente
cp .kiro/specs/Growth\ Dashboard/Executive-dashboard.tsx app/page.tsx

# 4. Configurar Tailwind (si no está)
# Ya está configurado en Next.js por defecto

# 5. Ejecutar
npm run dev
# Abrir http://localhost:3000
```

### Opción 2: Vite + React (Más rápido)

```bash
# 1. Crear proyecto Vite
npm create vite@latest comversa-dashboard -- --template react-ts

cd comversa-dashboard

# 2. Instalar dependencias
npm install
npm install lucide-react recharts

# 3. Instalar Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 4. Configurar Tailwind (tailwind.config.js)
# Ver sección "Configuración Tailwind" abajo

# 5. Copiar el componente
cp .kiro/specs/Growth\ Dashboard/Executive-dashboard.tsx src/App.tsx

# 6. Ejecutar
npm run dev
# Abrir http://localhost:5173
```

### Opción 3: Integrar con Streamlit Existente

```bash
# Usar iframe para embeber el dashboard React
# O migrar gradualmente de Streamlit a React
```

---

## Configuración Tailwind CSS

**tailwind.config.js:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          yellow: '#FFD826',
          dark: '#101010',
          gray: '#8A8A8A',
        },
      },
    },
  },
  plugins: [],
}
```

**src/index.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## Integración con Datos Reales

### Paso 1: Crear API Backend

**Ejemplo con FastAPI (Python):**
```python
# api/dashboard.py
from fastapi import FastAPI
from sqlalchemy import create_engine
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/comversa_rag")
engine = create_engine(DATABASE_URL)

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    # Query PostgreSQL para métricas
    query = """
    SELECT
        COUNT(DISTINCT id) as total_entities,
        COUNT(DISTINCT CASE WHEN entity_type = 'Process' THEN id END) as total_processes,
        COUNT(DISTINCT CASE WHEN entity_type = 'System' THEN id END) as total_systems
    FROM consolidated_entities
    WHERE consensus_confidence > 0.8
    """

    with engine.connect() as conn:
        result = conn.execute(query).fetchone()

    return {
        "totalEntities": result[0],
        "totalProcesses": result[1],
        "totalSystems": result[2],
        # ... más datos
    }

@app.get("/api/dashboard/companies")
async def get_companies_distribution():
    # Query Neo4j para distribución por empresa
    # ...
    pass
```

### Paso 2: Conectar Frontend con API

**Modificar Executive-dashboard.tsx:**
```typescript
import { useEffect, useState } from 'react';

const ExecutiveDashboard: React.FC = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/dashboard/summary')
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Cargando...</div>;

  // Usar data real en lugar de DASHBOARD_DATA
  // ...
};
```

### Paso 3: Query Neo4j para Knowledge Graph

```python
from neo4j import GraphDatabase

def get_knowledge_graph_metrics():
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
        auth=("neo4j", os.getenv("NEO4J_PASSWORD"))
    )

    with driver.session() as session:
        result = session.run("""
            MATCH (n:Entity)
            RETURN
                n.entity_type as type,
                count(n) as count,
                n.organization as org
            ORDER BY count DESC
        """)

        return [dict(record) for record in result]
```

---

## Próximos Pasos

### Corto Plazo (1-2 semanas)
- [ ] Configurar proyecto Next.js/Vite
- [ ] Conectar con PostgreSQL para datos reales
- [ ] Implementar filtros por empresa
- [ ] Agregar exportación PDF

### Mediano Plazo (3-4 semanas)
- [ ] Conectar con Neo4j para visualización de grafos
- [ ] Implementar drill-down interactivo
- [ ] Agregar visualizaciones de Recharts/Chart.js
- [ ] Implementar búsqueda y filtros avanzados

### Largo Plazo (2-3 meses)
- [ ] Integrar con RAG agent (cuando esté en Week 3)
- [ ] Implementar chat interface para queries
- [ ] Dashboard en tiempo real con WebSockets
- [ ] Integración con sistema de alertas

---

## Estructura de Archivos Sugerida

```
comversa-dashboard/
├── app/ o src/
│   ├── components/
│   │   ├── MetricCard.tsx
│   │   ├── CompanyDistribution.tsx
│   │   ├── PainPointsTable.tsx
│   │   ├── SystemsBreakdown.tsx
│   │   └── ProcessFrequency.tsx
│   ├── lib/
│   │   ├── api.ts (API client)
│   │   ├── types.ts (TypeScript interfaces)
│   │   └── constants.ts (Brand colors, etc.)
│   ├── hooks/
│   │   ├── useDashboardData.ts
│   │   └── useCompanyFilter.ts
│   └── page.tsx o App.tsx (Main dashboard)
├── public/
│   └── comversa-logo.svg
├── .env.local
├── package.json
└── README.md
```

---

## Referencias

- **Datos Fuente:** [reports/macro_processes_systems_people.md](../../reports/macro_processes_systems_people.md)
- **RAG 2.0 Specs:** [.kiro/specs/rag-2.0-enhancement/](../../.kiro/specs/rag-2.0-enhancement/)
- **Database Schema:** [scripts/migrations/](../../scripts/migrations/)
- **Brand Guidelines:** Ver SVG en mensaje original

---

## Soporte

Para preguntas o issues:
- **Email:** equipo.analisis@comversa.com
- **Slack:** #comversa-dashboard
- **Jira:** Project COMV Dashboard

---

**Última Actualización:** 2025-11-13
**Versión:** 1.0.0
**Autor:** Equipo de Desarrollo Comversa
