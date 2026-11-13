export type Priority = 'High' | 'Medium' | 'Low'
export type OrderStatus = 'Pending' | 'In Production' | 'Completed' | 'Delayed'
export type MachineStatus = 'Available' | 'Running' | 'Under Maintenance' | 'Breakdown'
export type TaskStatus = 'Scheduled' | 'Ongoing' | 'Completed' | 'Delayed' | 'Rescheduled'
export type DisruptionType = 'Machine Breakdown' | 'Rush Order' | 'Material Delay'

export interface Order {
  id: string
  product: string
  quantity: number
  orderDate: string
  deadline: string
  priority: Priority
  machine: string
  status: OrderStatus
  estimatedHours: number
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
  status: 'Open' | 'Analyzed' | 'Resolved'
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
