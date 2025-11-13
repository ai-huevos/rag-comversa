/**
 * COMVERSA EXECUTIVE DASHBOARD
 *
 * Dashboard ejecutivo para visualizar inteligencia consolidada de 44 entrevistas
 * Empresas: Los Tajibos, Comversa, Bolivian Foods
 *
 * Fuente de Datos: PostgreSQL + Neo4j (1,743 entidades consolidadas)
 * Brand Colors: #FFD826 (amarillo), #101010 (texto oscuro), #8A8A8A (gris)
 */

import React, { useState } from 'react';
import {
  BarChart3,
  Building2,
  Users,
  Workflow,
  Database,
  AlertTriangle,
  TrendingUp,
  Filter,
  Download,
  RefreshCw,
} from 'lucide-react';

// ============================================================================
// BRAND COLORS & THEME
// ============================================================================
const BRAND = {
  yellow: '#FFD826',
  dark: '#101010',
  gray: '#8A8A8A',
  white: '#FFFFFF',
  lightGray: '#F5F5F5',
  errorRed: '#DC2626',
  successGreen: '#16A34A',
  warningOrange: '#EA580C',
};

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================
interface CompanyData {
  name: string;
  employees: number;
  processes: number;
  systems: number;
  color: string;
}

interface MetricCard {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ElementType;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

interface PainPoint {
  title: string;
  priority: 'Crítica' | 'Alta' | 'Media';
  impact: string;
  timesSaved: string;
}

// ============================================================================
// MOCK DATA (Reemplazar con datos reales de PostgreSQL/Neo4j)
// ============================================================================
const DASHBOARD_DATA = {
  summary: {
    totalEntities: 1743,
    totalProcesses: 170,
    totalSystems: 183,
    totalDataFlows: 137,
    totalEmployees: 17,
    interviewsCompleted: 44,
    lastUpdated: '2025-11-12',
  },

  companies: [
    {
      name: 'Los Tajibos',
      employees: 1,
      processes: 70,
      systems: 65,
      color: '#EA580C', // orange
    },
    {
      name: 'Bolivian Foods',
      employees: 9,
      processes: 58,
      systems: 72,
      color: '#DC2626', // red
    },
    {
      name: 'Comversa',
      employees: 7,
      processes: 42,
      systems: 46,
      color: '#2563EB', // blue
    },
  ] as CompanyData[],

  criticalPainPoints: [
    {
      title: 'Integración SAP-Opera-Simphony-Satcom',
      priority: 'Crítica' as const,
      impact: 'Conciliaciones manuales diarias',
      timesSaved: '2-4 horas/día',
    },
    {
      title: 'Sistema CMMS Integrado (MaintainX ” SAP)',
      priority: 'Crítica' as const,
      impact: 'Doble entrada de datos',
      timesSaved: '40-60% reducción',
    },
    {
      title: 'Automatización de Aprobaciones',
      priority: 'Crítica' as const,
      impact: 'Workflows digitales',
      timesSaved: '50% reducción tiempo',
    },
    {
      title: 'Implementación DATAWAREHOUSE',
      priority: 'Alta' as const,
      impact: 'Centralización de datos',
      timesSaved: '80-90% reducción reportería',
    },
    {
      title: 'CRM Funcional (Bolivian Foods)',
      priority: 'Alta' as const,
      impact: 'Gestión clientes corporativos',
      timesSaved: 'Mejora conversión',
    },
  ] as PainPoint[],

  systemsBreakdown: {
    critical: 3, // SAP, Opera, Simphony
    important: 7, // Excel, MaintainX, Jira, etc.
    support: 30, // Teams, WhatsApp, Office, etc.
    total: 183,
  },

  processFrequency: {
    daily: 102, // ~60%
    weekly: 28,
    monthly: 25,
    annual: 15,
  },
};

// ============================================================================
// STYLED COMPONENTS
// ============================================================================
const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div
    className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}
    style={{ borderColor: BRAND.gray + '40' }}
  >
    {children}
  </div>
);

const MetricCardComponent: React.FC<{ data: MetricCard }> = ({ data }) => {
  const Icon = data.icon;
  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium" style={{ color: BRAND.gray }}>
            {data.title}
          </p>
          <h3
            className="text-3xl font-bold mt-2"
            style={{ color: BRAND.dark }}
          >
            {data.value.toLocaleString('es-ES')}
          </h3>
          <p className="text-xs mt-1" style={{ color: BRAND.gray }}>
            {data.subtitle}
          </p>
          {data.trend && (
            <div
              className="flex items-center gap-1 mt-2 text-xs font-medium"
              style={{
                color: data.trend.isPositive
                  ? BRAND.successGreen
                  : BRAND.errorRed,
              }}
            >
              <TrendingUp size={14} />
              <span>{data.trend.value}% desde última actualización</span>
            </div>
          )}
        </div>
        <div
          className="p-3 rounded-lg"
          style={{ backgroundColor: BRAND.yellow + '20' }}
        >
          <Icon size={24} style={{ color: BRAND.dark }} />
        </div>
      </div>
    </Card>
  );
};

const PriorityBadge: React.FC<{ priority: PainPoint['priority'] }> = ({
  priority,
}) => {
  const config = {
    Crítica: { bg: BRAND.errorRed, text: BRAND.white },
    Alta: { bg: BRAND.warningOrange, text: BRAND.white },
    Media: { bg: BRAND.gray, text: BRAND.white },
  };

  const style = config[priority];

  return (
    <span
      className="px-2 py-1 rounded text-xs font-semibold"
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      {priority}
    </span>
  );
};

// ============================================================================
// MAIN DASHBOARD COMPONENT
// ============================================================================
const ExecutiveDashboard: React.FC = () => {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState('últimos 30 días');

  const metrics: MetricCard[] = [
    {
      title: 'Entidades Consolidadas',
      value: DASHBOARD_DATA.summary.totalEntities,
      subtitle: 'PostgreSQL + Neo4j',
      icon: Database,
      trend: { value: 12, isPositive: true },
    },
    {
      title: 'Macro Procesos',
      value: DASHBOARD_DATA.summary.totalProcesses,
      subtitle: '60% frecuencia diaria',
      icon: Workflow,
    },
    {
      title: 'Sistemas Tecnológicos',
      value: DASHBOARD_DATA.summary.totalSystems,
      subtitle: '3 críticos | 7 importantes',
      icon: BarChart3,
    },
    {
      title: 'Empleados Entrevistados',
      value: DASHBOARD_DATA.summary.totalEmployees,
      subtitle: '44 entrevistas completadas',
      icon: Users,
    },
  ];

  return (
    <div
      className="min-h-screen p-6"
      style={{ backgroundColor: BRAND.lightGray }}
    >
      {/* HEADER */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1
              className="text-3xl font-bold mb-2"
              style={{ color: BRAND.dark }}
            >
              Dashboard Ejecutivo
            </h1>
            <p className="text-sm" style={{ color: BRAND.gray }}>
              Análisis consolidado de 44 entrevistas (Los Tajibos, Comversa,
              Bolivian Foods)
            </p>
            <p className="text-xs mt-1" style={{ color: BRAND.gray }}>
              Última actualización: {DASHBOARD_DATA.summary.lastUpdated}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:opacity-90 transition-opacity"
              style={{
                backgroundColor: BRAND.yellow,
                color: BRAND.dark,
              }}
            >
              <Download size={16} />
              Exportar PDF
            </button>
            <button
              className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 border hover:bg-gray-50 transition-colors"
              style={{
                backgroundColor: BRAND.white,
                borderColor: BRAND.gray + '40',
                color: BRAND.dark,
              }}
            >
              <RefreshCw size={16} />
              Actualizar
            </button>
          </div>
        </div>
      </header>

      {/* KEY METRICS GRID */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metrics.map((metric, idx) => (
          <MetricCardComponent key={idx} data={metric} />
        ))}
      </section>

      {/* COMPANY DISTRIBUTION & PROCESS BREAKDOWN */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Company Distribution */}
        <Card>
          <div className="flex items-center justify-between mb-6">
            <h2
              className="text-lg font-semibold"
              style={{ color: BRAND.dark }}
            >
              Distribución por Empresa
            </h2>
            <Filter size={18} style={{ color: BRAND.gray }} />
          </div>
          <div className="space-y-4">
            {DASHBOARD_DATA.companies.map((company, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span style={{ color: BRAND.dark }} className="font-medium">
                    {company.name}
                  </span>
                  <span style={{ color: BRAND.gray }}>
                    {company.employees} empleados
                  </span>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <div className="h-2 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${(company.processes / DASHBOARD_DATA.summary.totalProcesses) * 100}%`,
                          backgroundColor: company.color,
                        }}
                      />
                    </div>
                    <p className="text-xs mt-1" style={{ color: BRAND.gray }}>
                      {company.processes} procesos
                    </p>
                  </div>
                  <div className="flex-1">
                    <div className="h-2 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${(company.systems / DASHBOARD_DATA.summary.totalSystems) * 100}%`,
                          backgroundColor: company.color,
                          opacity: 0.7,
                        }}
                      />
                    </div>
                    <p className="text-xs mt-1" style={{ color: BRAND.gray }}>
                      {company.systems} sistemas
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Process Frequency Breakdown */}
        <Card>
          <h2 className="text-lg font-semibold mb-6" style={{ color: BRAND.dark }}>
            Frecuencia de Procesos
          </h2>
          <div className="space-y-4">
            {[
              {
                label: 'Diarios',
                value: DASHBOARD_DATA.processFrequency.daily,
                color: BRAND.errorRed,
              },
              {
                label: 'Semanales',
                value: DASHBOARD_DATA.processFrequency.weekly,
                color: BRAND.warningOrange,
              },
              {
                label: 'Mensuales',
                value: DASHBOARD_DATA.processFrequency.monthly,
                color: BRAND.yellow,
              },
              {
                label: 'Anuales',
                value: DASHBOARD_DATA.processFrequency.annual,
                color: BRAND.gray,
              },
            ].map((item, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium" style={{ color: BRAND.dark }}>
                    {item.label}
                  </span>
                  <span className="text-sm font-bold" style={{ color: BRAND.dark }}>
                    {item.value}
                  </span>
                </div>
                <div className="h-3 rounded-full bg-gray-200">
                  <div
                    className="h-3 rounded-full transition-all"
                    style={{
                      width: `${(item.value / DASHBOARD_DATA.summary.totalProcesses) * 100}%`,
                      backgroundColor: item.color,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* PAIN POINTS & OPPORTUNITIES */}
      <Card className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <AlertTriangle size={24} style={{ color: BRAND.errorRed }} />
          <h2 className="text-lg font-semibold" style={{ color: BRAND.dark }}>
            Pain Points Críticos y Oportunidades
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr
                className="border-b"
                style={{ borderColor: BRAND.gray + '40' }}
              >
                <th
                  className="text-left py-3 px-4 text-sm font-semibold"
                  style={{ color: BRAND.dark }}
                >
                  Título
                </th>
                <th
                  className="text-left py-3 px-4 text-sm font-semibold"
                  style={{ color: BRAND.dark }}
                >
                  Prioridad
                </th>
                <th
                  className="text-left py-3 px-4 text-sm font-semibold"
                  style={{ color: BRAND.dark }}
                >
                  Impacto
                </th>
                <th
                  className="text-left py-3 px-4 text-sm font-semibold"
                  style={{ color: BRAND.dark }}
                >
                  Tiempo Ahorrado
                </th>
              </tr>
            </thead>
            <tbody>
              {DASHBOARD_DATA.criticalPainPoints.map((point, idx) => (
                <tr
                  key={idx}
                  className="border-b hover:bg-gray-50 transition-colors"
                  style={{ borderColor: BRAND.gray + '20' }}
                >
                  <td className="py-3 px-4">
                    <span className="text-sm font-medium" style={{ color: BRAND.dark }}>
                      {point.title}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <PriorityBadge priority={point.priority} />
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm" style={{ color: BRAND.gray }}>
                      {point.impact}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className="text-sm font-semibold"
                      style={{ color: BRAND.successGreen }}
                    >
                      {point.timesSaved}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* SYSTEMS BREAKDOWN */}
      <Card>
        <h2 className="text-lg font-semibold mb-6" style={{ color: BRAND.dark }}>
          Análisis de Sistemas Tecnológicos
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            {
              label: 'Críticos',
              value: DASHBOARD_DATA.systemsBreakdown.critical,
              description: 'SAP, Opera, Simphony',
              color: BRAND.errorRed,
            },
            {
              label: 'Importantes',
              value: DASHBOARD_DATA.systemsBreakdown.important,
              description: 'Excel, MaintainX, Jira',
              color: BRAND.warningOrange,
            },
            {
              label: 'Soporte',
              value: DASHBOARD_DATA.systemsBreakdown.support,
              description: 'Teams, WhatsApp, Office',
              color: BRAND.gray,
            },
            {
              label: 'Total',
              value: DASHBOARD_DATA.systemsBreakdown.total,
              description: 'Todos los sistemas',
              color: BRAND.yellow,
            },
          ].map((sys, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg border"
              style={{
                borderColor: sys.color + '40',
                backgroundColor: sys.color + '10',
              }}
            >
              <div className="text-3xl font-bold mb-2" style={{ color: sys.color }}>
                {sys.value}
              </div>
              <div className="text-sm font-semibold mb-1" style={{ color: BRAND.dark }}>
                {sys.label}
              </div>
              <div className="text-xs" style={{ color: BRAND.gray }}>
                {sys.description}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* FOOTER */}
      <footer className="mt-8 text-center">
        <p className="text-xs" style={{ color: BRAND.gray }}>
          Documento generado automáticamente por sistema RAG-Comversa
        </p>
        <p className="text-xs mt-1" style={{ color: BRAND.gray }}>
          Para consultas sobre este análisis contactar a: Equipo de Análisis
        </p>
      </footer>
    </div>
  );
};

export default ExecutiveDashboard;
