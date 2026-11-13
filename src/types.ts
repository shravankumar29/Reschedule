export type Priority = 'High' | 'Medium' | 'Low'
export type OrderStatus = 'Pending' | 'In Production' | 'Completed' | 'Delayed'
export type MachineStatus = 'Available' | 'Running' | 'Under Maintenance' | 'Breakdown'
export type TaskStatus = 'Scheduled' | 'Ongoing' | 'Completed' | 'Delayed' | 'Rescheduled'
export type DisruptionType = 'Machine Breakdown' | 'Rush Order' | 'Material Delay'

export interface Order {
  id: string
  product: string
  productId?: string
  customerName?: string
  quantity: number
  orderDate: string
  deadline: string
  priority: Priority
  machine: string
  status: OrderStatus
  estimatedHours: number
}

export interface ProductOperation {
  id?: number
  operation_name: string
  sequence_number: number
  processing_time: number
  duration_basis: 'fixed' | 'per_unit' | 'per_batch'
  eligible_machine_ids: string[]
  required_material_id?: string | null
  required_material_qty?: number | null
  notes?: string | null
}

export interface Product {
  id?: number
  product_id: string
  name: string
  description?: string | null
  image_url?: string | null
  category: string
  is_active: boolean
  created_at?: string
  updated_at?: string
  routing_operations: ProductOperation[]
}

export interface OrderRouteOperation {
  operation_id: string
  operation_name: string
  sequence_number: number
  processing_time: number
  duration_basis: string
  eligible_machine_ids: string[]
  assigned_machine: string
  assigned_machine_name?: string
  previous_machine?: string | null
  is_reassigned: boolean
  planned_start?: number | null
  planned_end?: number | null
  status: string
  required_material_id?: string | null
  required_material_qty?: number | null
}

export interface OrderDetailsData {
  job_id: string
  customer_name: string
  product_id?: string | null
  product_name: string
  product_category: string
  product_description?: string | null
  quantity: number
  priority: Priority | 'Urgent'
  order_date: string
  deadline: string
  status: string
  is_rush_order: boolean
  risk_status: string
  progress_pct: number
  total_operations: number
  completed_operations: number
  running_operations: number
  pending_operations: number
  next_machine?: string | null
  expected_completion_hours?: number | null
  routing_operations: OrderRouteOperation[]
}

export interface Machine {
  id: string
  name: string
  type: string
  capacity: number
  utilization: number
  status: MachineStatus
  task: string
  workingHours: string
}

export interface ScheduleTask {
  id: string
  machineId: string
  orderId: string
  product: string
  operationName?: string
  date?: string
  endDate?: string
  start: string
  end: string
  startHour?: number
  endHour?: number
  duration?: number
  quantity: number
  status: TaskStatus
  lane: number
  frozen?: boolean
}

export interface MachineDowntimeInterval {
  machineId: string
  start: string
  end: string
  startHour: number
  endHour: number
  type: 'breakdown' | 'maintenance'
  label: string
  description?: string
}

export interface Disruption {
  id: string
  type: DisruptionType
  resource: string
  reported: string
  severity: 'Critical' | 'High' | 'Medium' | 'Low'
  status:
    | 'Open'
    | 'Analyzed'
    | 'Resolved'
    | 'Reported'
    | 'Under Repair'
    | 'Recovered'
    | 'Awaiting Material'
    | 'Received'
    | 'Awaiting Scheduling'
    | 'Scheduled'
    | 'Cancelled'
    | string
  description: string
  affectedOrders: string[]
  recovery: string
}

export interface Toast {
  id: string
  title: string
  message: string
  tone: 'success' | 'warning' | 'info' | 'error'
}

export interface FactorySettings {
  factoryName: string
  location: string
  workingHours: string
  timezone: string
  shiftPattern: string
  autoReschedule: boolean
  overtimeLimit: string
  emailAlerts: boolean
  disruptionAlerts: boolean
  weeklyDigest: boolean
  managerName: string
  managerRole: string
}
