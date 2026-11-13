import type { Disruption, FactorySettings, Machine, Order, ScheduleTask } from '../types'

export const initialOrders: Order[] = [
  { id: 'J-101', customerName: 'Mahindra Precision', product: 'Hydraulic Valve Housing', productId: 'PROD-001', quantity: 480, orderDate: '2026-11-07', deadline: '2026-11-09', priority: 'High', machine: 'CNC-1', status: 'Pending', estimatedHours: 5 },
  { id: 'J-102', customerName: 'Tata Motors', product: 'Drive Shaft Coupling', productId: 'PROD-002', quantity: 200, orderDate: '2026-11-07', deadline: '2026-11-08', priority: 'High', machine: 'CNC-2', status: 'Pending', estimatedHours: 6.5 },
]

export const initialMachines: Machine[] = [
  { id: 'CNC-1', name: 'CNC Turning Cell 01', type: 'CNC Lathe', capacity: 16, utilization: 0, status: 'Available', task: 'Available for assignment', workingHours: '06:00 – 22:00' },
  { id: 'CNC-2', name: 'CNC Turning Cell 02', type: 'CNC Lathe', capacity: 16, utilization: 0, status: 'Available', task: 'Available for assignment', workingHours: '06:00 – 22:00' },
]

export const initialSchedule: ScheduleTask[] = [
  { id: 'J-101-OP1', machineId: 'CNC-1', orderId: 'J-101', product: 'Hydraulic Valve Housing', operationName: 'Turning', date: '2026-11-07', start: '06:00', end: '09:00', startHour: 6, endHour: 9, duration: 3, quantity: 480, status: 'Scheduled', lane: 0 },
  { id: 'J-101-OP2', machineId: 'CNC-1', orderId: 'J-101', product: 'Hydraulic Valve Housing', operationName: 'Drilling', date: '2026-11-07', start: '09:00', end: '11:00', startHour: 9, endHour: 11, duration: 2, quantity: 480, status: 'Scheduled', lane: 0 },
  { id: 'J-102-OP1', machineId: 'CNC-2', orderId: 'J-102', product: 'Drive Shaft Coupling', operationName: 'Turning', date: '2026-11-07', start: '06:00', end: '10:00', startHour: 6, endHour: 10, duration: 4, quantity: 200, status: 'Scheduled', lane: 0 },
  { id: 'J-102-OP2', machineId: 'CNC-2', orderId: 'J-102', product: 'Drive Shaft Coupling', operationName: 'Boring', date: '2026-11-07', start: '10:00', end: '12:30', startHour: 10, endHour: 12.5, duration: 2.5, quantity: 200, status: 'Scheduled', lane: 0 },
]

export const initialDisruptions: Disruption[] = []

export const factorySettings: FactorySettings = {
  factoryName: 'Northstar Components', location: 'Pune, Maharashtra', workingHours: '06:00 – 22:00', timezone: 'Asia/Kolkata (UTC+05:30)', shiftPattern: '2 shifts · 8 hours', autoReschedule: true, overtimeLimit: '2 hours / day', emailAlerts: true, disruptionAlerts: true, weeklyDigest: false, managerName: 'Aarav Mehta', managerRole: 'Plant Operations Manager',
}

export const productionTrend = [
  { day: 'Mon', output: 1820, target: 1900 }, { day: 'Tue', output: 2140, target: 2000 }, { day: 'Wed', output: 1980, target: 2050 }, { day: 'Thu', output: 2260, target: 2100 }, { day: 'Fri', output: 2075, target: 2150 }, { day: 'Sat', output: 1640, target: 1700 }, { day: 'Sun', output: 1480, target: 1500 },
]

export const monthlyTrend = [
  { day: 'Jun', output: 18400, target: 19000 }, { day: 'Jul', output: 20150, target: 19800 }, { day: 'Aug', output: 21800, target: 21000 }, { day: 'Sep', output: 22450, target: 22000 }, { day: 'Oct', output: 23120, target: 22500 }, { day: 'Nov', output: 10780, target: 12000 },
]

export const delayData = [
  { name: 'Breakdowns', value: 34 }, { name: 'Materials', value: 22 }, { name: 'Rush orders', value: 17 }, { name: 'Quality hold', value: 11 }, { name: 'Other', value: 16 },
]
