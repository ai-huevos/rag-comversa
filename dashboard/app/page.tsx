'use client';

/**
 * Executive Dashboard Main Page
 *
 * Fetches real data from PostgreSQL backend and displays
 * executive dashboard with company metrics, pain points, and systems analysis.
 */

import React, { useState, useEffect } from 'react';
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
import { getDashboardData, DashboardData } from '@/lib/api';

// Brand colors
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

// Type definitions
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

// Styled Components
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
          <h3 className="text-3xl font-bold mt-2" style={{ color: BRAND.dark }}>
            {data.value.toLocaleString('es-ES')}
          </h3>
          <p className="text-xs mt-1" style={{ color: BRAND.gray }}>
            {data.subtitle}
          </p>
          {data.trend && (
            <div
              className="flex items-center gap-1 mt-2 text-xs font-medium"
              style={{
                color: data.trend.isPositive ? BRAND.successGreen : BRAND.errorRed,
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

const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
  const config = {
    Crítica: { bg: BRAND.errorRed, text: BRAND.white },
    Alta: { bg: BRAND.warningOrange, text: BRAND.white },
    Media: { bg: BRAND.gray, text: BRAND.white },
    Baja: { bg: '#94A3B8', text: BRAND.white },
  };

  const style = config[priority as keyof typeof config] || config.Media;

  return (
    <span
      className="px-2 py-1 rounded text-xs font-semibold"
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      {priority}
    </span>
  );
};

// Main Dashboard Component
export default function ExecutiveDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const dashboardData = await getDashboardData();
        setData(dashboardData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al cargar datos');
        console.error('Error fetching dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: BRAND.lightGray }}
      >
        <div className="text-center">
          <RefreshCw
            size={48}
            className="animate-spin mx-auto mb-4"
            style={{ color: BRAND.yellow }}
          />
          <p style={{ color: BRAND.dark }}>Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: BRAND.lightGray }}
      >
        <Card className="max-w-md">
          <AlertTriangle size={48} className="mx-auto mb-4" style={{ color: BRAND.errorRed }} />
          <h2 className="text-xl font-bold text-center mb-2" style={{ color: BRAND.dark }}>
            Error al cargar datos
          </h2>
          <p className="text-sm text-center" style={{ color: BRAND.gray }}>
            {error}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 w-full px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: BRAND.yellow, color: BRAND.dark }}
          >
            Reintentar
          </button>
        </Card>
      </div>
    );
  }

  if (!data) return null;

  const metrics: MetricCard[] = [
    {
      title: 'Entidades Consolidadas',
      value: data.summary.total_entities,
      subtitle: 'PostgreSQL + Neo4j',
      icon: Database,
      trend: { value: 12, isPositive: true },
    },
    {
      title: 'Macro Procesos',
      value: data.summary.total_processes,
      subtitle: '60% frecuencia diaria',
      icon: Workflow,
    },
    {
      title: 'Sistemas Tecnológicos',
      value: data.summary.total_systems,
      subtitle: `${data.systems_breakdown.critical} críticos | ${data.systems_breakdown.important} importantes`,
      icon: BarChart3,
    },
    {
      title: 'Empleados Entrevistados',
      value: data.summary.total_employees,
      subtitle: `${data.summary.interviews_completed} entrevistas completadas`,
      icon: Users,
    },
  ];

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: BRAND.lightGray }}>
      {/* HEADER */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: BRAND.dark }}>
              Dashboard Ejecutivo
            </h1>
            <p className="text-sm" style={{ color: BRAND.gray }}>
              Análisis consolidado de {data.summary.interviews_completed} entrevistas (Los Tajibos, Comversa, Bolivian Foods)
            </p>
            <p className="text-xs mt-1" style={{ color: BRAND.gray }}>
              Última actualización: {new Date(data.summary.last_updated).toLocaleDateString('es-ES')}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:opacity-90 transition-opacity"
              style={{ backgroundColor: BRAND.yellow, color: BRAND.dark }}
            >
              <Download size={16} />
              Exportar PDF
            </button>
            <button
              onClick={() => window.location.reload()}
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
            <h2 className="text-lg font-semibold" style={{ color: BRAND.dark }}>
              Distribución por Empresa
            </h2>
            <Filter size={18} style={{ color: BRAND.gray }} />
          </div>
          <div className="space-y-4">
            {data.companies.map((company, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span style={{ color: BRAND.dark }} className="font-medium">
                    {company.name}
                  </span>
                  <span style={{ color: BRAND.gray }}>{company.employees} empleados</span>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <div className="h-2 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${(company.processes / data.summary.total_processes) * 100}%`,
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
                          width: `${(company.systems / data.summary.total_systems) * 100}%`,
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
              { label: 'Diarios', value: data.process_frequency.daily, color: BRAND.errorRed },
              { label: 'Semanales', value: data.process_frequency.weekly, color: BRAND.warningOrange },
              { label: 'Mensuales', value: data.process_frequency.monthly, color: BRAND.yellow },
              { label: 'Anuales', value: data.process_frequency.annual, color: BRAND.gray },
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
                      width: `${(item.value / data.summary.total_processes) * 100}%`,
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
              <tr className="border-b" style={{ borderColor: BRAND.gray + '40' }}>
                <th className="text-left py-3 px-4 text-sm font-semibold" style={{ color: BRAND.dark }}>
                  Título
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold" style={{ color: BRAND.dark }}>
                  Prioridad
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold" style={{ color: BRAND.dark }}>
                  Impacto
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold" style={{ color: BRAND.dark }}>
                  Tiempo Ahorrado
                </th>
              </tr>
            </thead>
            <tbody>
              {data.critical_pain_points.map((point, idx) => (
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
                    <span className="text-sm font-semibold" style={{ color: BRAND.successGreen }}>
                      {point.times_saved}
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
              value: data.systems_breakdown.critical,
              description: 'SAP, Opera, Simphony',
              color: BRAND.errorRed,
            },
            {
              label: 'Importantes',
              value: data.systems_breakdown.important,
              description: 'Excel, MaintainX, Jira',
              color: BRAND.warningOrange,
            },
            {
              label: 'Soporte',
              value: data.systems_breakdown.support,
              description: 'Teams, WhatsApp, Office',
              color: BRAND.gray,
            },
            {
              label: 'Total',
              value: data.systems_breakdown.total,
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
}
