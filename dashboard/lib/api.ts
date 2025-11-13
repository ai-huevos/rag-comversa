/**
 * API Client for Comversa Executive Dashboard
 *
 * Fetches data from FastAPI backend running on localhost:8000
 * Preserves Spanish content from database.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DashboardData {
  summary: {
    total_entities: number;
    total_processes: number;
    total_systems: number;
    total_data_flows: number;
    total_employees: number;
    interviews_completed: number;
    last_updated: string;
  };
  companies: Array<{
    name: string;
    employees: number;
    processes: number;
    systems: number;
    color: string;
  }>;
  critical_pain_points: Array<{
    id: string;  // UUID
    title: string;
    priority: 'Crítica' | 'Alta' | 'Media' | 'Baja';
    impact: string;
    times_saved: string;
    company: string;
    department?: string;
  }>;
  systems_breakdown: {
    critical: number;
    important: number;
    support: number;
    total: number;
  };
  process_frequency: {
    daily: number;
    weekly: number;
    monthly: number;
    annual: number;
  };
}

/**
 * Fetch complete dashboard data
 */
export async function getDashboardData(): Promise<DashboardData> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard`);

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard data: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch summary statistics only
 */
export async function getDashboardSummary() {
  const response = await fetch(`${API_BASE_URL}/api/dashboard/summary`);

  if (!response.ok) {
    throw new Error(`Failed to fetch summary: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch entities list with filters
 */
export async function getEntities(params?: {
  entity_type?: string;
  company?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  const queryParams = new URLSearchParams();

  if (params?.entity_type) queryParams.append('entity_type', params.entity_type);
  if (params?.company) queryParams.append('company', params.company);
  if (params?.search) queryParams.append('search', params.search);
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

  const url = `${API_BASE_URL}/api/entities?${queryParams.toString()}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch entities: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch entity detail by ID
 */
export async function getEntityDetail(entityId: number) {
  const response = await fetch(`${API_BASE_URL}/api/entities/${entityId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch entity detail: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get available entity types
 */
export async function getEntityTypes() {
  const response = await fetch(`${API_BASE_URL}/api/entities/types/available`);

  if (!response.ok) {
    throw new Error(`Failed to fetch entity types: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get available companies
 */
export async function getCompanies() {
  const response = await fetch(`${API_BASE_URL}/api/entities/companies/available`);

  if (!response.ok) {
    throw new Error(`Failed to fetch companies: ${response.statusText}`);
  }

  return response.json();
}
