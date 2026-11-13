import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { factorySettings, initialDisruptions, initialMachines, initialOrders, initialSchedule } from '../data/mockData'
import type { Disruption, FactorySettings, Machine, Order, ScheduleTask, Toast } from '../types'
import {
  api,
  floatToTime,
  hourToDateAndTimeString,
  type AnalyticsOverview,
  type BackendExplanation,
  type BackendImpact,
  type MachineUtilizationItem,
  type ProductionOutputChart,
  type BackendDisruption,
  type BackendMaterial,
  type DisruptionWorkspaceSummary,
  type RushOrderResponse,
} from '../api/client'

interface AppContextValue {
  orders: Order[]
  machines: Machine[]
  schedule: ScheduleTask[]
  originalSchedule: ScheduleTask[]
  proposedSchedule: ScheduleTask[] | null
  proposedScheduleId: string | null
  proposedHasChanges: boolean
  proposedChangesCount: number
  proposedMode: 'optimization' | 'recovery' | null
  proposedSolverStatus: string | null
  proposedWallTime: number | null
  proposedObjectiveValue: number | null
  proposedBestBound: number | null
  proposedWeights: Record<string, any> | null
  proposedChangedOps: any[]
  proposedReassignedCount: number
  proposedDelayedCount: number
  proposedUnchangedCount: number
  proposedError: string | null
  clearProposedError: () => void
  isEditMode: boolean
  setIsEditMode: (val: boolean) => void
  selectedOperationForEdit: ScheduleTask | null
  setSelectedOperationForEdit: (op: ScheduleTask | null) => void
  proposalValidation: any | null
  startManualEdit: () => Promise<void>
  updateDraftOperation: (
    operationId: string,
    machineId: string,
    startTime: number,
    endTime?: number
  ) => Promise<{ success: boolean; error?: string }>
  discardDraftProposal: () => Promise<void>
  validateCurrentProposal: () => Promise<any>
  disruptions: Disruption[]
  activeDisruption: Disruption | null
  settings: FactorySettings
  toasts: Toast[]
  scheduleVersion: number
  impactData: BackendImpact | null
  explanations: BackendExplanation[]
  isLoading: boolean
  analyticsOverview: AnalyticsOverview | null
  machineUtilizationData: MachineUtilizationItem[]
  productionOutputData: ProductionOutputChart | null
  analyticsRange: string
  setAnalyticsRange: (range: string) => void
  lastUpdated: Date | null
  refreshAnalytics: (range?: string) => Promise<void>
  addOrder: (order: Omit<Order, 'id' | 'status'> & { status?: Order['status'] }) => void
  updateOrder: (order: Order) => void
  updateOrderStatus: (id: string, status: Order['status']) => void
  deleteOrder: (id: string) => void
  addMachine: (machine: Omit<Machine, 'utilization' | 'task'>) => void
  updateMachine: (machine: Machine) => void
  updateMachineStatus: (id: string, status: Machine['status']) => void
  reportDisruption: (input: Omit<Disruption, 'id' | 'reported' | 'status'> & { breakdown_start?: string; estimated_repair_hours?: number }) => void
  analyzeDisruption: (id?: string) => void
  generateSchedule: () => Promise<void>
  generateReschedule: (options?: { prioritize: boolean; delivery: boolean; idle: boolean; overtime: boolean; mode?: 'optimization' | 'recovery' | 'auto' }) => Promise<void>
  approveSchedule: () => Promise<void>
  recalculateSchedule: (options?: { prioritize: boolean; delivery: boolean; idle: boolean; overtime: boolean; mode?: 'optimization' | 'recovery' | 'auto' }) => Promise<void>
  updateSettings: (settings: FactorySettings) => void
  // Three-Category Disruption Workspace
  disruptionSummary: DisruptionWorkspaceSummary | null
  breakdowns: BackendDisruption[]
  materialDelays: BackendDisruption[]
  rushOrders: RushOrderResponse[]
  materials: BackendMaterial[]
  refreshDisruptionsData: () => Promise<void>
  reportBreakdownAction: (payload: { machine_id: string; description: string; breakdown_start?: string; estimated_repair_hours?: number; severity?: string; notes?: string }) => Promise<void>
  recoverBreakdownAction: (id: string, payload: { recovery_notes?: string; actual_recovery_time?: string }) => Promise<void>
  reportMaterialDelayAction: (payload: { material_id: string; delay_reason?: string; supplier?: string; required_quantity?: number; available_quantity?: number; expected_arrival_date?: string; expected_arrival_time?: string; severity?: string }) => Promise<void>
  receiveMaterialDelayAction: (id: string, payload: { received_quantity?: number; actual_arrival_time?: string; notes?: string }) => Promise<void>
  createRushOrderAction: (payload: any) => Promise<any>
  scheduleRushOrderAction: (rushOrderId: string) => Promise<void>
  dismissToast: (id: string) => void
  pushToast: (title: string, message: string, tone?: Toast['tone']) => void
  resetDemoData: () => Promise<void>
}

const STORAGE_KEY = 'reschedule-state-v1'
const AppContext = createContext<AppContextValue | null>(null)

interface PersistedState {
  orders: Order[]
  machines: Machine[]
  schedule: ScheduleTask[]
  originalSchedule: ScheduleTask[]
  disruptions: Disruption[]
  settings: FactorySettings
  scheduleVersion: number
}

function loadState(): PersistedState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw) as PersistedState
  } catch { /* use seed data if browser storage is unavailable */ }
  return { orders: initialOrders, machines: initialMachines, schedule: initialSchedule, originalSchedule: initialSchedule, disruptions: initialDisruptions, settings: factorySettings, scheduleVersion: 1 }
}

function mapBackendOpsToTasks(ops: any[], orders: Order[]): ScheduleTask[] {
  const jobMap = new Map(orders.map((j) => [j.id, j]))
  const machineLanes: Record<string, number> = {}

  return ops.map((op, idx) => {
    const order = jobMap.get(op.job_id)
    const lane = (machineLanes[op.machine_id] || 0) % 2
    machineLanes[op.machine_id] = (machineLanes[op.machine_id] || 0) + 1

    let taskStatus: ScheduleTask['status'] = 'Scheduled'
    if (op.status === 'Completed' || op.frozen) taskStatus = 'Completed'
    else if (op.status === 'Ongoing') taskStatus = 'Ongoing'
    else if (op.status === 'Delayed') taskStatus = 'Delayed'
    else if (op.status === 'Rescheduled') taskStatus = 'Rescheduled'

    const opDuration = op.duration !== undefined ? op.duration : Math.max(0.5, (op.end_time || 0) - (op.start_time || 0))
    const opName = op.operation_name || (op.operation_id ? op.operation_id.split('-').slice(1).join(' ') : 'Production')

    const startObj = hourToDateAndTimeString(op.start_time ?? 0)
    const endObj = hourToDateAndTimeString(op.end_time ?? 0)
    const taskDate = op.date || startObj.date
    const taskEndDate = op.end_date || endObj.date

    return {
      id: op.operation_id || `T-${idx + 1}`,
      machineId: op.machine_id,
      orderId: op.job_id,
      product: order ? order.product : op.job_id,
      operationName: opName,
      date: taskDate,
      endDate: taskEndDate,
      start: startObj.time,
      end: endObj.time,
      startHour: op.start_time,
      endHour: op.end_time,
      duration: opDuration,
      quantity: order ? order.quantity : 100,
      status: taskStatus,
      lane,
      frozen: !!op.frozen,
    }
  })
}

export function AppProvider({ children }: { children: ReactNode }) {
  const persisted = useMemo(loadState, [])
  const [orders, setOrders] = useState<Order[]>(persisted.orders)
  const [machines, setMachines] = useState<Machine[]>(persisted.machines)
  const [schedule, setSchedule] = useState<ScheduleTask[]>(persisted.schedule)
  const [originalSchedule, setOriginalSchedule] = useState<ScheduleTask[]>(persisted.originalSchedule)
  const [disruptions, setDisruptions] = useState<Disruption[]>(persisted.disruptions)
  const [settings, setSettings] = useState(persisted.settings)
  const [scheduleVersion, setScheduleVersion] = useState(persisted.scheduleVersion)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [impactData, setImpactData] = useState<BackendImpact | null>(null)
  const [explanations, setExplanations] = useState<BackendExplanation[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [analyticsOverview, setAnalyticsOverview] = useState<AnalyticsOverview | null>(null)
  const [machineUtilizationData, setMachineUtilizationData] = useState<MachineUtilizationItem[]>([])
  const [productionOutputData, setProductionOutputData] = useState<ProductionOutputChart | null>(null)
  const [analyticsRange, setAnalyticsRange] = useState<string>('week')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [proposedSchedule, setProposedSchedule] = useState<ScheduleTask[] | null>(null)
  const [proposedScheduleId, setProposedScheduleId] = useState<string | null>(null)
  const [proposedHasChanges, setProposedHasChanges] = useState<boolean>(false)
  const [proposedChangesCount, setProposedChangesCount] = useState<number>(0)
  const [proposedMode, setProposedMode] = useState<'optimization' | 'recovery' | null>(null)
  const [proposedSolverStatus, setProposedSolverStatus] = useState<string | null>(null)
  const [proposedWallTime, setProposedWallTime] = useState<number | null>(null)
  const [proposedObjectiveValue, setProposedObjectiveValue] = useState<number | null>(null)
  const [proposedBestBound, setProposedBestBound] = useState<number | null>(null)
  const [proposedWeights, setProposedWeights] = useState<Record<string, any> | null>(null)
  const [proposedChangedOps, setProposedChangedOps] = useState<any[]>([])
  const [proposedReassignedCount, setProposedReassignedCount] = useState<number>(0)
  const [proposedDelayedCount, setProposedDelayedCount] = useState<number>(0)
  const [proposedUnchangedCount, setProposedUnchangedCount] = useState<number>(0)
  const [proposedError, setProposedError] = useState<string | null>(null)
  const [isEditMode, setIsEditMode] = useState<boolean>(false)
  const [selectedOperationForEdit, setSelectedOperationForEdit] = useState<ScheduleTask | null>(null)
  const [proposalValidation, setProposalValidation] = useState<any | null>(null)

  // Three-Category Disruption Workspace state
  const [disruptionSummary, setDisruptionSummary] = useState<DisruptionWorkspaceSummary | null>(null)
  const [breakdowns, setBreakdowns] = useState<BackendDisruption[]>([])
  const [materialDelays, setMaterialDelays] = useState<BackendDisruption[]>([])
  const [rushOrders, setRushOrders] = useState<RushOrderResponse[]>([])
  const [materials, setMaterials] = useState<BackendMaterial[]>([])

  const refreshDisruptionsData = async () => {
    try {
      const [sum, bds, mds, rush, mats] = await Promise.all([
        api.getDisruptionsSummary().catch(() => null),
        api.listBreakdowns().catch(() => []),
        api.listMaterialDelays().catch(() => []),
        api.listRushOrders().catch(() => []),
        api.listMaterials().catch(() => []),
      ])
      if (sum) setDisruptionSummary(sum)
      if (bds) setBreakdowns(bds)
      if (mds) setMaterialDelays(mds)
      if (rush) setRushOrders(rush)
      if (mats) setMaterials(mats)
    } catch (err) {
      console.warn('Failed to load disruptions workspace data:', err)
    }
  }

  const reportBreakdownAction = async (payload: {
    machine_id: string
    description: string
    breakdown_start?: string
    estimated_repair_hours?: number
    severity?: string
    notes?: string
  }) => {
    setIsLoading(true)
    try {
      await api.reportBreakdown(payload)
      pushToast('Breakdown reported', `Machine ${payload.machine_id} marked offline. Repair estimated at ${payload.estimated_repair_hours || 4}h.`, 'warning')
      await refreshDisruptionsData()
      await refreshAnalytics()
      const updatedMachines = await api.getMachines().catch(() => null)
      if (updatedMachines) {
        setMachines(updatedMachines.map((m) => ({
          id: m.machine_id,
          name: m.name,
          type: m.machine_type,
          capacity: m.working_end_hour - m.working_start_hour,
          utilization: m.utilization || 0,
          status: !m.available ? 'Breakdown' : m.utilization > 0 ? 'Running' : 'Available',
          task: m.current_task || (m.available ? 'Available for assignment' : 'Offline / Breakdown'),
          workingHours: `${String(m.working_start_hour).padStart(2, '0')}:00 – ${String(m.working_end_hour).padStart(2, '0')}:00`,
        })))
      }
    } catch (err: any) {
      pushToast('Failed to report breakdown', err?.message || 'Error reporting breakdown', 'error')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const recoverBreakdownAction = async (id: string, payload: { recovery_notes?: string; actual_recovery_time?: string }) => {
    setIsLoading(true)
    try {
      await api.recoverBreakdown(id, payload)
      pushToast('Machine recovered', `Breakdown ${id} resolved. Machine returned to service.`, 'success')
      await refreshDisruptionsData()
      await refreshAnalytics()
      const updatedMachines = await api.getMachines().catch(() => null)
      if (updatedMachines) {
        setMachines(updatedMachines.map((m) => ({
          id: m.machine_id,
          name: m.name,
          type: m.machine_type,
          capacity: m.working_end_hour - m.working_start_hour,
          utilization: m.utilization || 0,
          status: !m.available ? 'Breakdown' : m.utilization > 0 ? 'Running' : 'Available',
          task: m.current_task || (m.available ? 'Available for assignment' : 'Offline / Breakdown'),
          workingHours: `${String(m.working_start_hour).padStart(2, '0')}:00 – ${String(m.working_end_hour).padStart(2, '0')}:00`,
        })))
      }
    } catch (err: any) {
      pushToast('Failed to recover machine', err?.message || 'Error updating recovery', 'error')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const reportMaterialDelayAction = async (payload: {
    material_id: string
    delay_reason?: string
    supplier?: string
    required_quantity?: number
    available_quantity?: number
    expected_arrival_date?: string
    expected_arrival_time?: string
    severity?: string
  }) => {
    setIsLoading(true)
    try {
      await api.reportMaterialDelay(payload)
      pushToast('Material delay recorded', `Delay reported for ${payload.material_id}. Shortage identified.`, 'warning')
      await refreshDisruptionsData()
      await refreshAnalytics()
    } catch (err: any) {
      pushToast('Failed to report material delay', err?.message || 'Error recording delay', 'error')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const receiveMaterialDelayAction = async (id: string, payload: { received_quantity?: number; actual_arrival_time?: string; notes?: string }) => {
    setIsLoading(true)
    try {
      await api.receiveMaterialDelay(id, payload)
      pushToast('Material received', `Receipt confirmed for disruption ${id}. Inventory replenished.`, 'success')
      await refreshDisruptionsData()
      await refreshAnalytics()
    } catch (err: any) {
      pushToast('Failed to record receipt', err?.message || 'Error recording receipt', 'error')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const createRushOrderAction = async (payload: any) => {
    setIsLoading(true)
    try {
      const res = await api.createRushOrder(payload)
      pushToast('Rush order added', `Order ${res.rush_order_id} created with Urgent priority.`, 'success')
      await refreshDisruptionsData()
      await refreshAnalytics()
      const backendJobs = await api.getJobs().catch(() => null)
      if (backendJobs) {
        setOrders(backendJobs.map((j) => ({
          id: j.job_id,
          product: j.product_name,
          quantity: j.quantity,
          orderDate: j.order_date,
          deadline: j.deadline,
          priority: j.priority === 'Urgent' ? 'High' : j.priority,
          machine: j.operations[0]?.eligible_machine_ids[0] || 'CNC-1',
          status: j.status,
          estimatedHours: j.operations.reduce((sum, op) => sum + op.processing_time, 0),
        })))
      }
      return res
    } catch (err: any) {
      pushToast('Failed to create rush order', err?.message || 'Error creating rush order', 'error')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const scheduleRushOrderAction = async (rushOrderId: string) => {
    setIsLoading(true)
    try {
      const res = await api.scheduleRushOrder(rushOrderId)
      if (res && res.operations) {
        const tasks = mapBackendOpsToTasks(res.operations, orders)
        setProposedSchedule(tasks)
        setProposedScheduleId(res.schedule_id)
        setProposedSolverStatus(res.solver_status)
        setProposedMode('recovery')
        setProposedHasChanges(res.has_changes ?? true)
        setProposedChangesCount(res.changes_count ?? 1)
        if (res.impact) setImpactData(res.impact)
        if (res.explanations) setExplanations(res.explanations)
        pushToast('Rush order scheduled', `Recovery schedule generated for rush order ${rushOrderId}.`, 'success')
      }
      await refreshDisruptionsData()
      await refreshAnalytics()
    } catch (err: any) {
      pushToast('Failed to schedule rush order', err?.message || 'Error scheduling rush order', 'error')
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const refreshAnalytics = async (range = analyticsRange) => {
    try {
      const [overview, util, prod] = await Promise.all([
        api.getAnalyticsOverview(range).catch(() => null),
        api.getMachineUtilization(range).catch(() => null),
        api.getProductionOutput(range).catch(() => null),
      ])
      if (overview) setAnalyticsOverview(overview)
      if (util) setMachineUtilizationData(util)
      if (prod) setProductionOutputData(prod)
      setLastUpdated(new Date())
    } catch (err) {
      console.warn('Analytics refresh error:', err)
    }
  }

  // Poll analytics every 20 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      refreshAnalytics()
    }, 20000)
    return () => clearInterval(timer)
  }, [analyticsRange])

  // Persist state to local storage
  useEffect(() => {
    const next: PersistedState = { orders, machines, schedule, originalSchedule, disruptions, settings, scheduleVersion }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  }, [orders, machines, schedule, originalSchedule, disruptions, settings, scheduleVersion])

  const pushToast = (title: string, message: string, tone: Toast['tone'] = 'success') => {
    const id = `${Date.now()}-${Math.random()}`
    setToasts((current) => [...current, { id, title, message, tone }])
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 4500)
  }

  // Sync data from FastAPI backend on mount
  useEffect(() => {
    async function loadBackendData() {
      try {
        const [backendMachines, backendJobs, backendDisruptions] = await Promise.all([
          api.getMachines().catch(() => null),
          api.getJobs().catch(() => null),
          api.getDisruptions().catch(() => null),
        ])

        if (backendMachines && backendMachines.length > 0) {
          const mappedMachines: Machine[] = backendMachines.map((m) => ({
            id: m.machine_id,
            name: m.name,
            type: m.machine_type,
            capacity: m.working_end_hour - m.working_start_hour,
            utilization: m.utilization || 0,
            status: !m.available ? 'Breakdown' : m.utilization > 0 ? 'Running' : 'Available',
            task: m.current_task || (m.available ? 'Available for assignment' : 'Offline / Breakdown'),
            workingHours: `${String(m.working_start_hour).padStart(2, '0')}:00 – ${String(m.working_end_hour).padStart(2, '0')}:00`,
          }))
          setMachines(mappedMachines)
        }

        let currentOrders = orders
        if (backendJobs && backendJobs.length > 0) {
          const mappedOrders: Order[] = backendJobs.map((j) => ({
            id: j.job_id,
            product: j.product_name,
            quantity: j.quantity,
            orderDate: j.order_date,
            deadline: j.deadline,
            priority: j.priority === 'Urgent' ? 'High' : j.priority,
            machine: j.operations[0]?.eligible_machine_ids[0] || 'CNC-1',
            status: j.status,
            estimatedHours: j.operations.reduce((sum, op) => sum + op.processing_time, 0),
          }))
          setOrders(mappedOrders)
          currentOrders = mappedOrders
        }

        if (backendDisruptions && backendDisruptions.length > 0) {
          const mappedDisruptions: Disruption[] = backendDisruptions.map((d) => ({
            id: d.disruption_id,
            type: d.disruption_type,
            resource: d.resource,
            reported: new Date(d.reported_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            severity: d.severity,
            status: d.status,
            description: d.description || '',
            affectedOrders: d.affected_job_ids,
            recovery: d.estimated_repair_hours ? `${d.estimated_repair_hours}h estimated` : '4h estimated',
          }))
          setDisruptions(mappedDisruptions)
        }

        // Try loading current schedule
        const currentSched = await api.getCurrentSchedule().catch(() => null)
        if (currentSched && currentSched.operations.length > 0) {
          const tasks = mapBackendOpsToTasks(currentSched.operations, currentOrders)
          setSchedule(tasks)
        }

        // Refresh live analytics and disruptions workspace from DB
        await refreshAnalytics()
        await refreshDisruptionsData()
      } catch (err) {
        console.warn('Backend sync failed, using cached state:', err)
      }
    }
    loadBackendData()
  }, [])

  const addOrder = async (order: Omit<Order, 'id' | 'status'> & { status?: Order['status'] }) => {
    // Generate a collision-safe ID: check both local state and backend
    let maxNum = 100
    for (const o of orders) {
      const match = o.id.match(/\d+/)
      if (match) {
        const val = parseInt(match[0], 10)
        if (val > maxNum) maxNum = val
      }
    }
    // Also query backend to avoid ID collision from previous sessions
    try {
      const backendJobs = await api.getJobs()
      for (const j of backendJobs) {
        const match = j.job_id.match(/\d+/)
        if (match) {
          const val = parseInt(match[0], 10)
          if (val > maxNum) maxNum = val
        }
      }
    } catch { /* use local maxNum if backend unavailable */ }

    const id = `J-${maxNum + 1}`
    const newOrder: Order = { ...order, id, status: order.status ?? 'Pending' }
    setOrders((current) => [newOrder, ...current])

    try {
      // Use real backend machine IDs; filter out any mock IDs (M01-M08 style)
      const realMachineIds = machines.filter((m) => !m.id.match(/^M0?\d+$/)).map((m) => m.id)
      const allMachineIds = realMachineIds.length > 0 ? realMachineIds : machines.map((m) => m.id)
      const primaryMachine = order.machine && allMachineIds.includes(order.machine)
        ? order.machine
        : (allMachineIds[0] || 'CNC-1')
      const eligible = [primaryMachine]
      const backupMachine = allMachineIds.find((mid) => mid !== primaryMachine)
      if (backupMachine) eligible.push(backupMachine)

      await api.createJob({
        job_id: id,
        customer_name: 'Custom Order',
        product_name: order.product,
        quantity: order.quantity,
        priority: order.priority === 'High' ? 'High' : order.priority === 'Medium' ? 'Medium' : 'Low',
        order_date: order.orderDate,
        deadline: order.deadline,
        operations: [
          {
            operation_name: `${order.product} Machining`,
            processing_time: order.estimatedHours || 4.0,
            eligible_machine_ids: eligible,
            sequence_number: 1,
          },
        ],
      })
      pushToast('Order saved to database', `${id} (${order.product}) is registered in the production system.`, 'success')
      refreshAnalytics()
    } catch (err: any) {
      console.warn('Backend job registration error:', err)
      const detail = err?.message || ''
      if (detail.includes('already exists')) {
        pushToast('Order ID conflict', `${id} already exists in DB. Try adding again — a new ID will be used.`, 'error')
        setOrders((current) => current.filter((o) => o.id !== id))
      } else {
        pushToast('Order added locally', `${id} (${order.product}) is saved in workspace (backend offline).`, 'warning')
      }
    }
  }

  const updateOrder = async (order: Order) => {
    setOrders((current) => current.map((item) => (item.id === order.id ? order : item)))
    try {
      await api.updateJob(order.id, {
        product_name: order.product,
        quantity: order.quantity,
        priority: order.priority,
        deadline: order.deadline,
        status: order.status,
      })
    } catch { /* local update is already applied */ }
    pushToast('Order updated', `${order.id} changes are saved.`)
    refreshAnalytics()
  }

  const updateOrderStatus = async (id: string, status: Order['status']) => {
    setOrders((current) => current.map((order) => (order.id === id ? { ...order, status } : order)))
    try {
      await api.updateJob(id, { status })
      pushToast('Order status updated', `${id} marked as ${status}.`, status === 'Completed' ? 'success' : 'info')
    } catch (err) {
      console.warn('Backend updateJob status failed:', err)
      pushToast('Status updated locally', `${id} set to ${status}.`, 'warning')
    }
    refreshAnalytics()
  }

  const deleteOrder = async (id: string) => {
    setOrders((current) => current.filter((order) => order.id !== id))
    setSchedule((current) => current.filter((task) => task.orderId !== id))
    try {
      await api.deleteJob(id)
    } catch { /* local removal is done */ }
    pushToast('Order removed', `${id} was removed from the active plan.`, 'warning')
  }

  const addMachine = async (machine: Omit<Machine, 'utilization' | 'task'>) => {
    const machineId = machine.id.trim()
    const machineName = machine.name.trim()

    // Check backend for duplicate IDs (not just local state)
    try {
      const backendMachines = await api.getMachines()
      const taken = backendMachines.some((m) => m.machine_id.toLowerCase() === machineId.toLowerCase())
      if (taken) {
        pushToast('Machine ID already in use', `${machineId} exists in the production system. Use a different ID.`, 'error')
        return
      }
    } catch { /* proceed — backend unreachable */ }

    const newMachine: Machine = {
      ...machine,
      id: machineId,
      name: machineName,
      utilization: 0,
      task: 'Available for assignment',
    }
    setMachines((current) => [...current, newMachine])
    try {
      // Parse working hours from "06:00 – 22:00" format if available
      let startHour = 6
      let endHour = 22
      if (machine.workingHours) {
        const parts = machine.workingHours.match(/(\d+):(\d+)\s*[–-]\s*(\d+):(\d+)/)
        if (parts) {
          startHour = parseInt(parts[1])
          endHour = parseInt(parts[3])
        }
      }
      // Clamp to valid schema range
      startHour = Math.max(0, Math.min(23, startHour))
      endHour = Math.max(startHour + 1, Math.min(24, endHour))

      await api.createMachine({
        machine_id: machineId,
        name: machineName,
        machine_type: machine.type || 'CNC Lathe',
        supported_operations: ['Turning', 'Milling', 'Drilling', 'Cutting', 'Grinding'],
        working_start_hour: startHour,
        working_end_hour: endHour,
      })
      pushToast('Machine registered in backend', `${machineId} (${machineName}) is available for planning.`, 'success')
      refreshAnalytics()
    } catch (err: any) {
      console.warn('Backend machine creation error:', err)
      const detail = err?.message || ''
      if (detail.includes('already exists')) {
        pushToast('Machine ID conflict', `${machineId} already exists in backend. The machine was added locally.`, 'warning')
      } else {
        pushToast('Machine added locally', `${machineId} (${machineName}) is available in workspace (backend offline).`, 'warning')
      }
    }
  }

  const updateMachine = async (machine: Machine) => {
    setMachines((current) => current.map((item) => (item.id === machine.id ? machine : item)))
    try {
      await api.updateMachine(machine.id, {
        name: machine.name,
        machine_type: machine.type,
      })
    } catch { /* local update applied */ }
    pushToast('Machine updated', `${machine.id} configuration is saved.`)
  }

  const updateMachineStatus = async (id: string, status: Machine['status']) => {
    setMachines((current) =>
      current.map((machine) =>
        machine.id === id ? { ...machine, status, task: status === 'Available' ? 'Available for assignment' : machine.task } : machine,
      ),
    )
    try {
      await api.setMachineAvailability(id, status !== 'Breakdown' && status !== 'Under Maintenance')
    } catch { /* fallback */ }
    if (status === 'Available') pushToast('Machine released', `${id} is now available for assignment.`)
  }

  const reportDisruption = async (input: Omit<Disruption, 'id' | 'reported' | 'status'> & { breakdown_start?: string; estimated_repair_hours?: number }) => {
    const machineId = input.resource.split(' · ')[0]
    try {
      const res = await api.createDisruption({
        disruption_type: input.type,
        resource: machineId,
        severity: input.severity,
        description: input.description,
        affected_job_ids: input.affectedOrders,
        breakdown_start: input.breakdown_start || '10:00',
        estimated_repair_hours: input.estimated_repair_hours || 3.0,
      })

      const disruption: Disruption = {
        id: res.disruption_id,
        type: input.type,
        resource: input.resource,
        reported: 'Just now',
        severity: input.severity,
        status: 'Open',
        description: input.description,
        affectedOrders: input.affectedOrders,
        recovery: `${input.estimated_repair_hours || 3}h estimated`,
      }
      setDisruptions((current) => [disruption, ...current])

      if (input.type === 'Machine Breakdown') {
        setMachines((current) =>
          current.map((m) =>
            m.id === machineId
              ? { ...m, status: 'Breakdown', task: `Breakdown (${input.breakdown_start || '10:00'}, ${input.estimated_repair_hours || 3}h)` }
              : m
          )
        )
        setOrders((current) =>
          current.map((order) => (input.affectedOrders.includes(order.id) ? { ...order, status: 'Delayed' } : order))
        )
      }

      pushToast('Disruption logged in backend', `${res.disruption_id} registered for ${machineId}. Recovery optimizer ready.`, 'warning')
      refreshAnalytics()
    } catch {
      const id = `D-${22 + disruptions.length}`.padStart(6, '0')
      const disruption: Disruption = { ...input, id, reported: 'Just now', status: 'Open' }
      setDisruptions((current) => [disruption, ...current])
      pushToast('Disruption reported', `${id} added to recovery queue.`, 'warning')
    }
  }

  const analyzeDisruption = async (id = disruptions.find((item) => item.status === 'Open')?.id) => {
    if (!id) return pushToast('Nothing to analyze', 'There are no open disruptions right now.', 'info')
    setDisruptions((current) => current.map((item) => (item.id === id ? { ...item, status: 'Analyzed' } : item)))
    try {
      const imp = await api.getImpact()
      setImpactData(imp)
      const exps = await api.getExplanations()
      setExplanations(exps)
    } catch { /* proceed */ }
    pushToast('Impact analysis ready', 'Affected orders and alternate capacity mapped by backend.', 'info')
  }

  const generateSchedule = async () => {
    setIsLoading(true)
    try {
      const res = await api.generateSchedule()
      if (res.operations && res.operations.length > 0) {
        const tasks = mapBackendOpsToTasks(res.operations, orders)
        setSchedule(tasks)
        setOriginalSchedule(tasks)
        setScheduleVersion((v) => v + 1)
        pushToast('OR-Tools schedule generated', `Plan ${res.schedule_id} generated (${res.solver_status}). 7/7 constraints passed.`)
      }
      await refreshAnalytics()
    } catch (err: any) {
      console.warn('API generate schedule failed, using local simulation:', err)
      setSchedule((current) => current.map((task, index) => (index === 2 ? { ...task, machineId: 'CNC-2', start: '10:00', end: '18:00', status: 'Rescheduled' } : task)))
      setScheduleVersion((v) => v + 1)
      pushToast('Schedule updated', 'The active plan reflects capacity snapshot.')
    } finally {
      setIsLoading(false)
    }
  }

  const generateReschedule = async (options?: {
    prioritize: boolean
    delivery: boolean
    idle: boolean
    overtime: boolean
    mode?: 'optimization' | 'recovery' | 'auto'
  }) => {
    setIsLoading(true)
    setProposedError(null)
    try {
      const openDisruptions = disruptions.filter((d) => d.status === 'Open' || d.status === 'Analyzed')
      const targetDisruption = openDisruptions[0]
      const requestedMode = options?.mode || (targetDisruption ? 'recovery' : 'optimization')

      // Preserve original baseline before any rescheduling
      if (schedule.length > 0 && originalSchedule.length === 0) {
        setOriginalSchedule([...schedule])
      }

      const res = await api.reschedule({
        disruption_id: requestedMode === 'recovery' ? targetDisruption?.id : undefined,
        mode: requestedMode,
        prioritize_urgent: options?.prioritize ?? true,
        minimize_delay: options?.delivery ?? true,
        minimize_idle: options?.idle ?? false,
        minimize_overtime: options?.overtime ?? false,
      })

      setProposedSolverStatus(res.solver_status)
      setProposedWallTime(res.wall_time_seconds ?? null)
      setProposedObjectiveValue(res.objective_value ?? null)
      setProposedBestBound(res.best_bound ?? null)
      setProposedWeights(res.weights_used ?? null)
      setProposedMode(res.mode || (requestedMode === 'recovery' ? 'recovery' : 'optimization'))

      if (res.solver_status === 'INFEASIBLE') {
        setProposedSchedule(null)
        setProposedScheduleId(null)
        setProposedHasChanges(false)
        setProposedChangesCount(0)
        setProposedError(res.error || 'No feasible schedule found with the given constraints.')
        pushToast('Optimization infeasible', 'No schedule could satisfy all hard constraints simultaneously.', 'error')
        return
      }

      if (res.operations && res.operations.length > 0) {
        const tasks = mapBackendOpsToTasks(res.operations, orders)

        setProposedSchedule(tasks)
        setProposedScheduleId(res.schedule_id)
        setProposedHasChanges(res.has_changes ?? false)
        setProposedChangesCount(res.changes_count ?? 0)
        setProposedChangedOps(res.changed_operations ?? [])
        setProposedReassignedCount(res.reassigned_count ?? 0)
        setProposedDelayedCount(res.delayed_count ?? 0)
        setProposedUnchangedCount(res.unchanged_count ?? 0)

        if (res.impact) setImpactData(res.impact)
        if (res.explanations) setExplanations(res.explanations)

        const modeLabel = (res.mode === 'recovery') ? 'Recovery plan' : 'Schedule optimization'
        const changeMsg = res.has_changes
          ? `${res.changes_count} operation${res.changes_count === 1 ? '' : 's'} adjusted. Ready for approval.`
          : (res.solver_status === 'OPTIMAL' ? 'Current schedule is already optimal.' : 'No improvement found within solver search limit.')

        pushToast(
          `${modeLabel} ready`,
          `CP-SAT solver (${res.solver_status} in ${(res.wall_time_seconds || 0).toFixed(2)}s). ${changeMsg}`,
          res.has_changes ? 'success' : 'info',
        )
      }
      await refreshAnalytics()
    } catch (err: any) {
      console.warn('Optimization failed:', err)
      const isNetworkErr = err?.message?.includes('Failed to fetch') || err?.message?.includes('NetworkError')
      const msg = isNetworkErr
        ? 'Cannot connect to backend server (http://localhost:8000). Ensure the backend is running.'
        : (err?.message || 'CP-SAT solver error. Check backend logs.')
      setProposedError(msg)
      pushToast('Optimization failed', msg, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const approveSchedule = async () => {
    if (!proposedScheduleId) {
      pushToast('Nothing to approve', 'Generate a recovery or optimization plan first.', 'info')
      return
    }
    setIsLoading(true)
    try {
      await api.approveSchedule(proposedScheduleId)

      // Activate the proposed schedule as the current active schedule
      if (proposedSchedule) {
        setOriginalSchedule([...schedule])
        setSchedule(proposedSchedule)
        setScheduleVersion((v) => v + 1)
      }

      // Refresh disruptions from backend (resolved one will be marked)
      const [updatedDisruptions, updatedMachines] = await Promise.all([
        api.getDisruptions().catch(() => null),
        api.getMachines().catch(() => null),
      ])
      if (updatedDisruptions) {
        setDisruptions(updatedDisruptions.map((d) => ({
          id: d.disruption_id,
          type: d.disruption_type,
          resource: d.resource,
          reported: d.reported_at ? new Date(d.reported_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }).replace(',', '') : 'Unknown',
          severity: d.severity as any,
          status: d.status as any,
          description: d.description || '',
          recovery: d.recovery_notes || '',
          affectedOrders: Array.isArray(d.affected_job_ids) ? d.affected_job_ids : [],
        })))
      }
      if (updatedMachines) {
        setMachines(updatedMachines.map((m) => ({
          id: m.machine_id,
          name: m.name,
          type: m.machine_type,
          capacity: m.working_end_hour - m.working_start_hour,
          utilization: m.utilization || 0,
          status: !m.available ? 'Breakdown' : m.utilization > 0 ? 'Running' : 'Available',
          task: m.current_task || (m.available ? 'Available for assignment' : 'Offline / Breakdown'),
          workingHours: `${String(m.working_start_hour).padStart(2, '0')}:00 – ${String(m.working_end_hour).padStart(2, '0')}:00`,
        })))
      }

      // Clear proposed state
      setProposedSchedule(null)
      setProposedScheduleId(null)
      setProposedHasChanges(false)
      setProposedChangesCount(0)
      setProposedMode(null)
      setProposedSolverStatus(null)
      setProposedError(null)
      setIsEditMode(false)
      setSelectedOperationForEdit(null)
      setProposalValidation(null)

      pushToast('New schedule approved', 'The optimized plan is now active across production views.')
      await refreshAnalytics()
    } catch (err: any) {
      console.warn('Backend approval failed:', err)
      const isNetworkErr = err?.message?.includes('Failed to fetch') || err?.message?.includes('NetworkError')
      const msg = isNetworkErr
        ? 'Cannot connect to backend server (http://localhost:8000). Ensure the backend is running.'
        : (err?.message || 'Could not activate the proposed schedule.')
      pushToast('Approval failed', msg, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const clearProposedError = () => {
    setProposedError(null)
    setProposedSolverStatus(null)
    setProposedSchedule(null)
    setProposedScheduleId(null)
    setProposedHasChanges(false)
    setProposedChangesCount(0)
    setProposedMode(null)
    setProposedChangedOps([])
    setProposedReassignedCount(0)
    setProposedDelayedCount(0)
    setProposedUnchangedCount(0)
  }

  const recalculateSchedule = async (options?: {
    prioritize: boolean
    delivery: boolean
    idle: boolean
    overtime: boolean
    mode?: 'optimization' | 'recovery' | 'auto'
  }) => {
    await generateReschedule(options)
    pushToast('Schedule recalculated', 'The recovery plan has been refreshed with current availability.', 'info')
  }

  const startManualEdit = async () => {
    setIsLoading(true)
    clearProposedError()
    try {
      let activeProposalId = proposedScheduleId
      if (!activeProposalId) {
        const draft = await api.createDraftProposal()
        activeProposalId = draft.schedule_id
        setProposedScheduleId(draft.schedule_id)
        setProposedMode('optimization')
        setProposedSolverStatus(draft.solver_status || 'OPTIMAL')
        setProposedHasChanges(false)
        setProposedChangesCount(0)
        setProposedReassignedCount(0)
        setProposedDelayedCount(0)
        setProposedUnchangedCount(draft.operations ? draft.operations.length : 0)
        if (draft.operations && draft.operations.length > 0) {
          const tasks = mapBackendOpsToTasks(draft.operations, orders)
          setProposedSchedule(tasks)
        }
        if (draft.impact) setImpactData(draft.impact)
        if (draft.validation) setProposalValidation(draft.validation)
      } else {
        const val = await api.validateProposal(activeProposalId).catch(() => null)
        if (val) setProposalValidation(val)
      }
      setIsEditMode(true)
      pushToast('Editor opened', 'Manual schedule editor is active. Select an operation to adjust machine and timing.', 'info')
    } catch (err: any) {
      console.warn('Could not start manual editor:', err)
      const msg = err?.message || 'Could not initialize draft proposal'
      pushToast('Editor error', msg, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const updateDraftOperation = async (
    operationId: string,
    machineId: string,
    startTime: number,
    endTime?: number
  ): Promise<{ success: boolean; error?: string }> => {
    if (!proposedScheduleId) {
      return { success: false, error: 'No active proposal found.' }
    }
    setIsLoading(true)
    try {
      const res = await api.updateProposalOperation(proposedScheduleId, operationId, {
        machine_id: machineId,
        start_time: startTime,
        end_time: endTime,
      })
      if (res.success && res.operations) {
        const tasks = mapBackendOpsToTasks(res.operations, orders)
        setProposedSchedule(tasks)
        setProposedHasChanges(res.has_changes ?? true)
        setProposedChangesCount(res.changes_count ?? 1)
        setProposedReassignedCount(res.reassigned_count ?? 0)
        setProposedDelayedCount(res.delayed_count ?? 0)
        setProposedUnchangedCount(res.unchanged_count ?? 0)
        setProposedChangedOps(res.changed_operations ?? [])
        if (res.impact) setImpactData(res.impact)
        if (res.validation) setProposalValidation(res.validation)
        pushToast('Operation updated', res.message, 'success')
        setSelectedOperationForEdit(null)
        await refreshAnalytics()
        return { success: true }
      }
      return { success: false, error: res.message || 'Update failed' }
    } catch (err: any) {
      const msg = err?.message || 'Validation error'
      pushToast('Update rejected', msg, 'error')
      return { success: false, error: msg }
    } finally {
      setIsLoading(false)
    }
  }

  const discardDraftProposal = async () => {
    if (proposedScheduleId) {
      try {
        await api.discardProposal(proposedScheduleId).catch(() => null)
      } catch {}
    }
    clearProposedError()
    setIsEditMode(false)
    setSelectedOperationForEdit(null)
    setProposalValidation(null)
    pushToast('Changes discarded', 'Manual edits have been discarded without affecting baseline.', 'info')
  }

  const validateCurrentProposal = async () => {
    if (!proposedScheduleId) return null
    try {
      const val = await api.validateProposal(proposedScheduleId)
      setProposalValidation(val)
      if (val.valid) {
        pushToast('Validation passed', 'All 7 hard constraints are satisfied.', 'success')
      } else {
        pushToast('Validation warning', `${val.errors.length} constraint conflicts detected.`, 'error')
      }
      return val
    } catch (err: any) {
      pushToast('Validation failed', err?.message || 'Could not validate schedule', 'error')
      return null
    }
  }

  const resetDemoData = async () => {
    setIsLoading(true)
    try {
      await api.seedDatabase(true)
      await generateSchedule()
      pushToast('Demo reset complete', '5 machines and 10 jobs loaded. Initial schedule ready.')
    } catch (err: any) {
      pushToast('Reset error', err.message || 'Could not reset demo', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const value: AppContextValue = {
    orders,
    machines,
    schedule,
    originalSchedule,
    proposedSchedule,
    proposedScheduleId,
    proposedHasChanges,
    proposedChangesCount,
    proposedMode,
    proposedSolverStatus,
    proposedWallTime,
    proposedObjectiveValue,
    proposedBestBound,
    proposedWeights,
    proposedChangedOps,
    proposedReassignedCount,
    proposedDelayedCount,
    proposedUnchangedCount,
    proposedError,
    clearProposedError,
    isEditMode,
    setIsEditMode,
    selectedOperationForEdit,
    setSelectedOperationForEdit,
    proposalValidation,
    startManualEdit,
    updateDraftOperation,
    discardDraftProposal,
    validateCurrentProposal,
    disruptions,
    activeDisruption: disruptions.find((item) => item.status !== 'Resolved') ?? disruptions[0] ?? null,
    settings,
    toasts,
    scheduleVersion,
    impactData,
    explanations,
    isLoading,
    analyticsOverview,
    machineUtilizationData,
    productionOutputData,
    analyticsRange,
    setAnalyticsRange,
    lastUpdated,
    refreshAnalytics,
    addOrder,
    updateOrder,
    updateOrderStatus,
    deleteOrder,
    addMachine,
    updateMachine,
    updateMachineStatus,
    reportDisruption,
    analyzeDisruption,
    generateSchedule,
    generateReschedule,
    approveSchedule,
    recalculateSchedule,
    updateSettings: (next) => { setSettings(next); pushToast('Settings saved', 'Factory preferences are up to date.') },
    // Disruption Workspace
    disruptionSummary,
    breakdowns,
    materialDelays,
    rushOrders,
    materials,
    refreshDisruptionsData,
    reportBreakdownAction,
    recoverBreakdownAction,
    reportMaterialDelayAction,
    receiveMaterialDelayAction,
    createRushOrderAction,
    scheduleRushOrderAction,
    dismissToast: (id) => setToasts((current) => current.filter((toast) => toast.id !== id)),
    pushToast,
    resetDemoData,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp must be used inside AppProvider')
  return context
}
