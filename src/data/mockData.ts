import type { Disruption, FactorySettings, Machine, Order, ScheduleTask } from '../types'

export const initialOrders: Order[] = [
  { id: 'O-1042', product: 'Hydraulic Valve Housing', quantity: 480, orderDate: '2026-11-03', deadline: '2026-11-09', priority: 'High', machine: 'M01', status: 'In Production', estimatedHours: 16 },
  { id: 'O-1041', product: 'Drive Coupling 42B', quantity: 1200, orderDate: '2026-11-02', deadline: '2026-11-10', priority: 'Medium', machine: 'M03', status: 'In Production', estimatedHours: 22 },
  { id: 'O-1039', product: 'Stainless Mount Plate', quantity: 860, orderDate: '2026-10-31', deadline: '2026-11-08', priority: 'High', machine: 'M02', status: 'Delayed', estimatedHours: 14 },
  { id: 'O-1038', product: 'Servo Bracket Set', quantity: 320, orderDate: '2026-10-30', deadline: '2026-11-07', priority: 'High', machine: 'M04', status: 'Completed', estimatedHours: 8 },
  { id: 'O-1037', product: 'Conveyor Idler Shaft', quantity: 650, orderDate: '2026-10-29', deadline: '2026-11-11', priority: 'Low', machine: 'M05', status: 'Pending', estimatedHours: 18 },
  { id: 'O-1035', product: 'Precision Gear Ring', quantity: 210, orderDate: '2026-10-28', deadline: '2026-11-09', priority: 'Medium', machine: 'M06', status: 'In Production', estimatedHours: 12 },
  { id: 'O-1032', product: 'Control Panel Faceplate', quantity: 540, orderDate: '2026-10-26', deadline: '2026-11-12', priority: 'Low', machine: 'M07', status: 'Pending', estimatedHours: 10 },
  { id: 'O-1030', product: 'Bearing Retainer', quantity: 920, orderDate: '2026-10-25', deadline: '2026-11-08', priority: 'Medium', machine: 'M08', status: 'Completed', estimatedHours: 13 },
]

export const initialMachines: Machine[] = [
  { id: 'M01', name: 'CNC Turning Cell', type: 'CNC Lathe', capacity: 32, utilization: 86, status: 'Running', task: 'O-1042 · Hydraulic Valve Housing', workingHours: '06:00 – 22:00' },
  { id: 'M02', name: 'Vertical Mill 02', type: 'Milling Center', capacity: 28, utilization: 92, status: 'Breakdown', task: 'O-1039 · Stainless Mount Plate', workingHours: '06:00 – 22:00' },
  { id: 'M03', name: 'Horizontal Mill 01', type: 'Milling Center', capacity: 32, utilization: 74, status: 'Running', task: 'O-1041 · Drive Coupling 42B', workingHours: '06:00 – 22:00' },
  { id: 'M04', name: 'CNC Turning Cell 02', type: 'CNC Lathe', capacity: 30, utilization: 48, status: 'Available', task: 'Available for assignment', workingHours: '06:00 – 22:00' },
  { id: 'M05', name: 'Laser Cutter', type: 'Fiber Laser', capacity: 26, utilization: 61, status: 'Running', task: 'O-1037 · Conveyor Idler Shaft', workingHours: '06:00 – 22:00' },
  { id: 'M06', name: 'Grinding Station', type: 'Surface Grinder', capacity: 24, utilization: 69, status: 'Running', task: 'O-1035 · Precision Gear Ring', workingHours: '06:00 – 22:00' },
  { id: 'M07', name: 'Press Brake 01', type: 'Press Brake', capacity: 20, utilization: 38, status: 'Available', task: 'Available for assignment', workingHours: '06:00 – 22:00' },
  { id: 'M08', name: 'Assembly Bench 03', type: 'Assembly', capacity: 18, utilization: 28, status: 'Under Maintenance', task: 'Preventive maintenance · 3h remaining', workingHours: '06:00 – 22:00' },
]

export const initialSchedule: ScheduleTask[] = [
  { id: 'T-01', machineId: 'M01', orderId: 'O-1042', product: 'Hydraulic Valve Housing', date: '2026-11-07', start: '06:00', end: '14:00', quantity: 240, status: 'Ongoing', lane: 0 },
  { id: 'T-02', machineId: 'M01', orderId: 'O-1042', product: 'Hydraulic Valve Housing', date: '2026-11-07', start: '15:00', end: '21:00', quantity: 240, status: 'Scheduled', lane: 1 },
  { id: 'T-03', machineId: 'M02', orderId: 'O-1039', product: 'Stainless Mount Plate', date: '2026-11-07', start: '06:00', end: '16:00', quantity: 430, status: 'Delayed', lane: 0 },
  { id: 'T-04', machineId: 'M03', orderId: 'O-1041', product: 'Drive Coupling 42B', date: '2026-11-07', start: '07:00', end: '15:00', quantity: 600, status: 'Ongoing', lane: 0 },
  { id: 'T-05', machineId: 'M03', orderId: 'O-1041', product: 'Drive Coupling 42B', date: '2026-11-07', start: '16:00', end: '22:00', quantity: 600, status: 'Scheduled', lane: 1 },
  { id: 'T-06', machineId: 'M04', orderId: 'O-1038', product: 'Servo Bracket Set', date: '2026-11-07', start: '06:00', end: '10:00', quantity: 320, status: 'Completed', lane: 0 },
  { id: 'T-07', machineId: 'M05', orderId: 'O-1037', product: 'Conveyor Idler Shaft', date: '2026-11-07', start: '08:00', end: '16:00', quantity: 325, status: 'Scheduled', lane: 0 },
  { id: 'T-08', machineId: 'M06', orderId: 'O-1035', product: 'Precision Gear Ring', date: '2026-11-07', start: '06:00', end: '12:00', quantity: 105, status: 'Ongoing', lane: 0 },
]

export const initialDisruptions: Disruption[] = [
  { id: 'D-0021', type: 'Machine Breakdown', resource: 'M02 · Vertical Mill 02', reported: 'Today, 08:42', severity: 'Critical', status: 'Open', description: 'Spindle vibration above threshold. Maintenance team assigned.', affectedOrders: ['O-1039'], recovery: '4h estimated' },
  { id: 'D-0020', type: 'Material Delay', resource: '4140 Steel Billet', reported: 'Yesterday, 16:15', severity: 'Medium', status: 'Analyzed', description: 'Supplier ETA moved by one working day.', affectedOrders: ['O-1041', 'O-1037'], recovery: 'Tomorrow, 09:00' },
  { id: 'D-0019', type: 'Rush Order', resource: 'O-1042 · Priority uplift', reported: 'Yesterday, 11:20', severity: 'High', status: 'Resolved', description: 'Customer requested an accelerated delivery commitment.', affectedOrders: ['O-1042'], recovery: 'Schedule protected' },
]

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
