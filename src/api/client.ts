/**
 * API client for ReSchedule FastAPI backend.
 * Provides typed methods for Machines, Jobs, Disruptions, Schedules, Impact Analysis, and Explanations.
 */

const API_BASE = 'http://localhost:8000/api'

// Helper: convert float hours (e.g. 0.0, 4.5, 12.25) to "HH:MM"
// Shift base is 06:00 (day start)
export function floatToTime(hoursFromStart: number, baseHour: number = 6): string {
  const hourInDay = baseHour + (hoursFromStart >= 0 ? hoursFromStart % 24 : ((hoursFromStart % 24) + 24) % 24)
  const totalMinutes = Math.round(hourInDay * 60)
  const h = Math.floor(totalMinutes / 60) % 24
  const m = totalMinutes % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

export function hourToDateAndTimeString(hoursFromStart: number, baseDateStr: string = '2026-11-07', baseHour: number = 6) {
  const dayOffset = Math.floor(hoursFromStart / 24)
  const base = new Date(`${baseDateStr}T00:00:00`)
  base.setDate(base.getDate() + dayOffset)
  const yyyy = base.getFullYear()
  const mm = String(base.getMonth() + 1).padStart(2, '0')
  const dd = String(base.getDate()).padStart(2, '0')
  const dateStr = `${yyyy}-${mm}-${dd}`

  const hourInDay = baseHour + (hoursFromStart >= 0 ? hoursFromStart % 24 : ((hoursFromStart % 24) + 24) % 24)
  const totalMinutes = Math.round(hourInDay * 60)
  const h = Math.floor(totalMinutes / 60) % 24
  const m = totalMinutes % 60
  const timeStr = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`

  return { date: dateStr, time: timeStr, hourOfDay: hourInDay }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(errorBody.detail || `HTTP ${res.status}: ${res.statusText}`)
  }

  if (res.status === 204) {
    return {} as T
  }

  return res.json()
}

export interface BackendMachine {
  id: number
  machine_id: string
  name: string
  machine_type: string
  supported_operations: string[]
  available: boolean
  working_start_hour: number
  working_end_hour: number
  maintenance_periods?: any[]
  utilization: number
  current_task?: string
}

export interface BackendOperation {
  id: number
  operation_id: string
  job_id: string
  operation_name: string
  processing_time: number
  eligible_machine_ids: string[]
  sequence_number: number
  status: string
}

export interface BackendJob {
  id: number
  job_id: string
  customer_name: string
  product_name: string
  quantity: number
  priority: 'Low' | 'Medium' | 'High' | 'Urgent'
  order_date: string
  deadline: string
  status: 'Pending' | 'In Production' | 'Completed' | 'Delayed'
  operations: BackendOperation[]
}

export interface BackendDisruption {
  id: number
  disruption_id: string
  disruption_type: 'Machine Breakdown' | 'Rush Order' | 'Material Delay'
  resource: string
  reported_at: string
  severity: 'Critical' | 'High' | 'Medium' | 'Low'
  status: string
  description?: string
  affected_job_ids: string[]
  // Machine Breakdown
  machine_id?: string
  breakdown_start?: string
  estimated_repair_hours?: number
  recovery_notes?: string
  actual_recovery_at?: string
  // Material Delay
  material_id?: string
  supplier?: string
  required_quantity?: number
  available_quantity?: number
  shortage_quantity?: number
  expected_arrival?: string
  actual_arrival?: string
  affected_operation_ids?: string[]
  affected_machine_ids?: string[]
  // Rush Order
  rush_job_id?: string
  deadline?: string
}

export interface BackendMaterial {
  id: number
  material_id: string
  name: string
  category: string
  unit: string
  available_quantity: number
  reserved_quantity: number
  min_stock_level: number
  supplier?: string
  lead_time_days: number
}

export interface BackendMaterialRequirement {
  id: number
  job_id: string
  operation_id?: string
  material_id: string
  required_quantity: number
  allocated_quantity: number
}

export interface DisruptionWorkspaceSummary {
  active_machine_breakdowns: number
  active_material_delays: number
  open_rush_orders: number
  total_affected_orders: number
}

export interface RushOrderResponse {
  rush_order_id: string
  disruption_id?: string
  customer_name: string
  product_name: string
  quantity: number
  order_date?: string
  deadline: string
  priority: string
  status: string
  production_status: string
  operations: Array<{
    operation_id: string
    operation_name: string
    processing_time: number
    eligible_machine_ids: string[]
    sequence_number: number
    status: string
  }>
  required_materials: Array<{
    material_id: string
    required_quantity: number
    allocated_quantity: number
  }>
}

export interface BackendScheduleOp {
  id: number
  schedule_id: string
  job_id: string
  operation_id: string
  machine_id: string
  start_time: number
  end_time: number
  duration: number
  status: string
  frozen: boolean
}

export interface BackendSchedule {
  id: number
  schedule_id: string
  created_at: string
  schedule_type: 'initial' | 'revised'
  status: 'active' | 'superseded'
  makespan_hours?: number
  total_jobs: number
  on_time_count: number
  delayed_count: number
  disruption_id?: string
  solver_status?: string
  operations: BackendScheduleOp[]
}

export interface BackendImpact {
  original_schedule_id?: string
  revised_schedule_id: string
  original_makespan_hours?: number
  revised_makespan_hours?: number
  makespan_change_hours?: number
  original_total_tardiness_hours?: number
  revised_total_tardiness_hours?: number
  tardiness_change_hours?: number
  original_delayed_count?: number
  original_delayed_orders_count?: number
  revised_delayed_count?: number
  reassigned_operations_count?: number
  delayed_operations_count?: number
  unaffected_operations_count?: number
  total_operations: number
  rescheduled_operations_count: number
  rescheduled_operations: Array<{
    operation_id: string
    job_id: string
    original_machine: string
    new_machine: string
    original_start: number
    new_start: number
    time_shift_hours: number
    machine_changed: boolean
  }>
  affected_jobs: string[]
  affected_jobs_count: number
  machine_changes: Array<{
    operation_id: string
    job_id: string
    from_machine: string
    to_machine: string
  }>
  machine_utilization: Record<string, number>
  delayed_jobs: Array<{
    job_id: string
    product_name: string
    deadline: string
    delay_hours: number
  }>
  on_time_count: number
  delayed_count: number
  on_time_delivery_pct: number
  solver_status?: string
}

export interface AnalyticsOverview {
  total_active_orders: number
  completed_orders: number
  total_orders: number
  pending_orders: number
  in_production_orders: number
  delayed_orders: number
  urgent_orders: number
  total_machines: number
  available_machines: number
  broken_machines_count: number
  on_time_delivery_pct: number
  average_scheduled_utilization_pct: number
  current_makespan_hours: number | null
  reporting_window: string
  range_type: string
  open_disruptions_count: number
  total_jobs?: number
  pending_jobs?: number
  in_production_jobs?: number
  completed_jobs?: number
  delayed_jobs?: number
  urgent_jobs?: number
}

export interface MachineUtilizationItem {
  machine_id: string
  name: string
  machine_type: string
  scheduled_hours: number
  breakdown_downtime_hours: number
  maintenance_downtime_hours: number
  net_available_hours: number
  utilization_pct: number
  operational_status: string
  current_task: string
  remaining_capacity_hours: number
  reporting_window: string
}

export interface ProductionOutputChart {
  total_planned_units: number
  total_actual_units: number
  total_target_units: number
  data: Array<{
    date: string
    day: string
    planned_output: number
    actual_output: number
    target: number
    operations_count: number
  }>
  reporting_window: string
}

export interface BackendExplanation {
  type: string
  operation_id?: string
  job_id?: string
  message: string
  from_machine?: string
  to_machine?: string
  shift_hours?: number
  delay_hours?: number
}

export interface RescheduleOptions {
  disruption_id?: string
  mode?: 'optimization' | 'recovery' | 'auto'
  prioritize_urgent?: boolean
  minimize_delay?: boolean
  minimize_idle?: boolean
  minimize_overtime?: boolean
}

export interface RescheduleResult {
  schedule_id: string
  solver_status: string
  status: string
  mode?: 'optimization' | 'recovery'
  operations: any[]
  validation: any
  has_changes: boolean
  changes_count: number
  reassigned_count?: number
  delayed_count?: number
  unchanged_count?: number
  changed_operations: any[]
  disruption_id?: string
  broken_machine?: string
  objective_value?: number
  best_bound?: number
  wall_time_seconds?: number
  weights_used?: Record<string, any>
  impact?: any
  explanations?: BackendExplanation[]
  error?: string
}

export const api = {
  // Machines
  getMachines: () => request<BackendMachine[]>('/machines/'),
  createMachine: (data: Partial<BackendMachine>) => request<BackendMachine>('/machines/', { method: 'POST', body: JSON.stringify(data) }),
  updateMachine: (id: string, data: Partial<BackendMachine>) => request<BackendMachine>(`/machines/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteMachine: (id: string) => request<void>(`/machines/${id}`, { method: 'DELETE' }),
  setMachineAvailability: (id: string, available: boolean) => request<BackendMachine>(`/machines/${id}/availability?available=${available}`, { method: 'PATCH' }),

  // Jobs
  getJobs: () => request<BackendJob[]>('/jobs/'),
  createJob: (data: any) => request<BackendJob>('/jobs/', { method: 'POST', body: JSON.stringify(data) }),
  updateJob: (id: string, data: any) => request<BackendJob>(`/jobs/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteJob: (id: string) => request<void>(`/jobs/${id}`, { method: 'DELETE' }),

  // Disruptions & Multi-Category Disruption Workspace
  getDisruptions: () => request<BackendDisruption[]>('/disruptions/'),
  getDisruptionsSummary: () => request<DisruptionWorkspaceSummary>('/disruptions/summary'),
  createDisruption: (data: Partial<BackendDisruption>) => request<BackendDisruption>('/disruptions/', { method: 'POST', body: JSON.stringify(data) }),
  resolveDisruption: (id: string) => request<BackendDisruption>(`/disruptions/${id}/resolve`, { method: 'PATCH' }),

  // Breakdowns sub-category
  listBreakdowns: () => request<BackendDisruption[]>('/disruptions/breakdowns'),
  reportBreakdown: (payload: {
    machine_id: string
    description: string
    breakdown_start?: string
    estimated_repair_hours?: number
    severity?: string
    notes?: string
  }) => request<BackendDisruption>('/disruptions/breakdowns', { method: 'POST', body: JSON.stringify(payload) }),
  recoverBreakdown: (id: string, payload: { recovery_notes?: string; actual_recovery_time?: string }) =>
    request<BackendDisruption>(`/disruptions/breakdowns/${id}/recover`, { method: 'POST', body: JSON.stringify(payload) }),
  updateBreakdown: (id: string, payload: { estimated_repair_hours?: number; status?: string; notes?: string }) =>
    request<BackendDisruption>(`/disruptions/breakdowns/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),

  // Material Delays sub-category
  listMaterialDelays: () => request<BackendDisruption[]>('/disruptions/material-delays'),
  reportMaterialDelay: (payload: {
    material_id: string
    delay_reason?: string
    supplier?: string
    required_quantity?: number
    available_quantity?: number
    expected_arrival_date?: string
    expected_arrival_time?: string
    severity?: string
  }) => request<BackendDisruption>('/disruptions/material-delays', { method: 'POST', body: JSON.stringify(payload) }),
  receiveMaterialDelay: (id: string, payload: { received_quantity?: number; actual_arrival_time?: string; notes?: string }) =>
    request<BackendDisruption>(`/disruptions/material-delays/${id}/receive`, { method: 'POST', body: JSON.stringify(payload) }),
  updateMaterialDelay: (id: string, payload: { expected_arrival_time?: string; status?: string; notes?: string }) =>
    request<BackendDisruption>(`/disruptions/material-delays/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),

  // Rush Orders
  listRushOrders: () => request<RushOrderResponse[]>('/rush-orders/'),
  createRushOrder: (payload: any) => request<any>('/rush-orders/', { method: 'POST', body: JSON.stringify(payload) }),
  scheduleRushOrder: (rushOrderId: string) => request<RescheduleResult>(`/rush-orders/${rushOrderId}/schedule`, { method: 'POST' }),

  // Materials Inventory
  listMaterials: () => request<BackendMaterial[]>('/materials/'),
  createMaterial: (payload: Partial<BackendMaterial>) => request<BackendMaterial>('/materials/', { method: 'POST', body: JSON.stringify(payload) }),
  getMaterial: (materialId: string) => request<BackendMaterial>(`/materials/${materialId}`),
  updateMaterial: (materialId: string, payload: Partial<BackendMaterial>) => request<BackendMaterial>(`/materials/${materialId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  getMaterialRequirements: (materialId: string) => request<BackendMaterialRequirement[]>(`/materials/${materialId}/requirements`),

  // Scheduling & Rescheduling
  generateSchedule: () => request<{ schedule_id: string; solver_status: string; operations: any[]; validation: any }>('/schedule/generate', { method: 'POST' }),
  getCurrentSchedule: (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams()
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)
    const qs = params.toString() ? `?${params.toString()}` : ''
    return request<BackendSchedule>(`/schedule/current${qs}`)
  },
  getScheduleHistory: () => request<BackendSchedule[]>('/schedule/history'),
  reschedule: (options?: RescheduleOptions) => request<RescheduleResult>(
    '/reschedule',
    {
      method: 'POST',
      body: JSON.stringify({
        disruption_id: options?.disruption_id ?? null,
        mode: options?.mode ?? 'auto',
        prioritize_urgent: options?.prioritize_urgent ?? true,
        minimize_delay: options?.minimize_delay ?? true,
        minimize_idle: options?.minimize_idle ?? false,
        minimize_overtime: options?.minimize_overtime ?? false,
      }),
    }
  ),
  approveSchedule: (scheduleId: string) => request<{
    schedule_id: string
    status: string
    resolved_disruption_id: string | null
    approved_at: string
    total_operations: number
    makespan_hours: number
    solver_status: string
  }>('/schedule/approve', { method: 'POST', body: JSON.stringify({ schedule_id: scheduleId }) }),

  // Impact and Explanations
  getImpact: () => request<BackendImpact>('/reschedule/impact'),
  getExplanations: () => request<BackendExplanation[]>('/reschedule/explanations'),

  // Schedule manual editing & proposals
  createDraftProposal: (baseScheduleId?: string) =>
    request<RescheduleResult>('/schedule/proposals/draft', {
      method: 'POST',
      body: JSON.stringify({ base_schedule_id: baseScheduleId ?? null }),
    }),
  getEligibleMachinesForOp: (proposalId: string, operationId: string) =>
    request<Array<{
      machine_id: string
      name: string
      machine_type: string
      available: boolean
      utilization: number
      current_task: string | null
      is_compatible: boolean
      incompatibility_reason: string | null
    }>>(`/schedule/proposals/${proposalId}/eligible-machines/${operationId}`),
  updateProposalOperation: (
    proposalId: string,
    operationId: string,
    payload: { machine_id: string; start_time: number; end_time?: number }
  ) =>
    request<{
      success: boolean
      message: string
      schedule_id: string
      has_changes: boolean
      changes_count: number
      reassigned_count: number
      delayed_count: number
      unchanged_count: number
      changed_operations: any[]
      operation: any
      operations: any[]
      validation: any
      impact?: BackendImpact
    }>(`/schedule/proposals/${proposalId}/operations/${operationId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  discardProposal: (proposalId: string) =>
    request<{ success: boolean; message: string }>(`/schedule/proposals/${proposalId}/discard`, {
      method: 'DELETE',
    }),
  validateProposal: (proposalId: string) =>
    request<any>(`/schedule/proposals/${proposalId}/validate`, {
      method: 'POST',
    }),

  // Analytics & Validation
  getAnalyticsOverview: (range = 'week', start?: string, end?: string) => {
    const params = new URLSearchParams({ range })
    if (start) params.set('start_date', start)
    if (end) params.set('end_date', end)
    return request<AnalyticsOverview>(`/analytics/overview?${params.toString()}`)
  },
  getMachineUtilization: (range = 'week', start?: string, end?: string) => {
    const params = new URLSearchParams({ range })
    if (start) params.set('start_date', start)
    if (end) params.set('end_date', end)
    return request<MachineUtilizationItem[]>(`/analytics/machine-utilization?${params.toString()}`)
  },
  getProductionOutput: (range = 'week', start?: string, end?: string) => {
    const params = new URLSearchParams({ range })
    if (start) params.set('start_date', start)
    if (end) params.set('end_date', end)
    return request<ProductionOutputChart>(`/analytics/production-output?${params.toString()}`)
  },
  getMachineStatus: (range = 'week') => request<any[]>(`/analytics/machine-status?range=${range}`),
  validateSchedule: (scheduleId: string) => request<any>(`/schedule/${scheduleId}/validate`),
  getDelayedJobs: () => request<any>('/analytics/delayed-jobs'),

  // Admin seed
  seedDatabase: (reset = true) => request<{ message: string }>(`/admin/seed?reset=${reset}`, { method: 'POST' }),
}

