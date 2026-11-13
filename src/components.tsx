import { AnimatePresence, motion } from 'framer-motion'
import { Activity, AlertTriangle, Bell, CalendarDays, ChevronDown, ChevronLeft, ChevronRight, ClipboardList, Clock3, Factory, FileBarChart, Gauge, GitBranch, Layers3, Menu, PanelLeftClose, PanelLeftOpen, Plus, Search, Settings2, ShieldCheck, SlidersHorizontal, Sparkles, Wrench, X, Zap } from 'lucide-react'
import { useState, type ComponentType, type ReactNode } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useApp } from './context/AppContext'
import type { MachineStatus, OrderStatus, Priority, ScheduleTask, TaskStatus } from './types'

export const navItems = [
  { label: 'Overview', path: '/dashboard', icon: Gauge },
  { label: 'Production Schedule', path: '/schedule', icon: CalendarDays },
  { label: 'Orders', path: '/orders', icon: ClipboardList },
  { label: 'Machines', path: '/machines', icon: Wrench },
  { label: 'Disruptions', path: '/disruptions', icon: AlertTriangle },
  { label: 'Rescheduling', path: '/rescheduling', icon: GitBranch },
  { label: 'Analytics', path: '/analytics', icon: Activity },
  { label: 'Reports', path: '/reports', icon: FileBarChart },
  { label: 'Settings', path: '/settings', icon: Settings2 },
]

export function LogoMark({ light = false }: { light?: boolean }) {
  return <div className={`logo-mark ${light ? 'logo-mark-light' : ''}`} aria-label="ReSchedule logo"><span /><span /><span /><span /><span /><span /></div>
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const current = navItems.find((item) => item.path === location.pathname) ?? navItems[0]
  const { toasts, dismissToast, disruptions, disruptionSummary } = useApp()
  const openDisruptions = disruptionSummary
    ? (disruptionSummary.active_machine_breakdowns + disruptionSummary.active_material_delays + disruptionSummary.open_rush_orders)
    : disruptions.filter((item) => item.status === 'Open' || item.status === 'Reported' || item.status === 'Under Repair' || item.status === 'Awaiting Material' || item.status === 'Awaiting Scheduling').length

  return <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
    <aside className="sidebar">
      <div className="sidebar-brand">
        <LogoMark light />
        {!collapsed && <div><div className="brand-wordmark">ReSchedule</div><div className="brand-subtitle">Production Intelligence</div></div>}
        <button className="icon-btn sidebar-toggle" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">{collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}</button>
      </div>
      <div className="sidebar-section-label">{!collapsed && 'Workspace'}</div>
      <nav className="sidebar-nav">
        {navItems.map(({ label, path, icon: Icon }) => <NavLink key={path} to={path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title={collapsed ? label : undefined}><Icon size={17} strokeWidth={1.8} /><span>{!collapsed && label}</span>{label === 'Disruptions' && openDisruptions > 0 && <em>{openDisruptions}</em>}</NavLink>)}
      </nav>
      <div className="sidebar-foot">
        {!collapsed && <div className="factory-mini"><div className="factory-mini-icon"><Factory size={15} /></div><div><strong>Northstar Components</strong><span>Pune · Plant 01</span></div></div>}
        <div className="user-mini"><div className="avatar avatar-dark">AM</div>{!collapsed && <div className="user-details"><strong>Aarav Mehta</strong><span>Operations Manager</span></div>}<button className="icon-btn" title="Profile settings"><Settings2 size={15} /></button></div>
      </div>
    </aside>
    <div className="main-shell">
      <header className="topbar">
        <div className="topbar-left"><button className="mobile-menu icon-btn" onClick={() => setCollapsed(!collapsed)}><Menu size={18} /></button><div><div className="eyebrow">OPERATIONS / {current.label.toUpperCase()}</div><div className="topbar-title">{current.label}</div></div></div>
        <div className="topbar-actions">
          <div className={`global-search ${searchOpen ? 'open' : ''}`}><Search size={15} /><input autoFocus={searchOpen} placeholder="Search orders, machines..." onFocus={() => setSearchOpen(true)} onBlur={() => window.setTimeout(() => setSearchOpen(false), 180)} onKeyDown={(event) => { if (event.key === 'Enter') { setSearchOpen(false); navigate('/orders') } }} /></div>
          <button className="icon-btn notification-button" onClick={() => navigate('/disruptions')} title="Open disruptions"><Bell size={17} /><span className={openDisruptions ? 'notification-dot' : 'notification-dot hidden'} /></button>
          <div className="topbar-date"><CalendarDays size={15} /><span>07 Nov 2026</span></div>
          <div className="avatar">AM</div>
        </div>
      </header>
      <main className="content-area"><Outlet /></main>
    </div>
    <ToastStack toasts={toasts} dismissToast={dismissToast} />
  </div>
}

export function PageHeader({ eyebrow, title, subtitle, actions }: { eyebrow?: string; title: string; subtitle?: string; actions?: ReactNode }) {
  return <div className="page-header"><div><div className="eyebrow">{eyebrow ?? 'WORKSPACE'}</div><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>
}

export function Button({ children, variant = 'primary', icon, onClick, type = 'button', disabled = false, className = '' }: { children: ReactNode; variant?: 'primary' | 'secondary' | 'quiet' | 'danger' | 'outline'; icon?: ReactNode; onClick?: () => void; type?: 'button' | 'submit'; disabled?: boolean; className?: string }) {
  return <button type={type} className={`button button-${variant} ${className}`} onClick={onClick} disabled={disabled}>{icon}{children}</button>
}

export function StatCard({ label, value, detail, icon: Icon, tone = 'teal', trend }: { label: string; value: string; detail: string; icon: ComponentType<{ size?: number }>; tone?: 'teal' | 'amber' | 'brick' | 'blue'; trend?: string }) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={18} /></div><div className="stat-card-main"><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-detail">{trend && <span className="trend">{trend}</span>}{detail}</div></div></div>
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'teal' }) { return <span className={`badge badge-${tone}`}><span className="badge-dot" />{children}</span> }
export function PriorityBadge({ value }: { value: Priority }) { return <Badge tone={value === 'High' ? 'danger' : value === 'Medium' ? 'warning' : 'neutral'}>{value}</Badge> }
export function StatusBadge({ value }: { value: OrderStatus | MachineStatus | TaskStatus | 'Open' | 'Analyzed' | 'Resolved' | 'Critical' | 'Medium' | 'Low' | 'High' }) {
  const tone = ['Completed', 'Available', 'Resolved'].includes(value) ? 'success' : ['Delayed', 'Breakdown', 'Critical', 'Open'].includes(value) ? 'danger' : ['Running', 'In Production', 'Ongoing', 'Analyzed', 'High'].includes(value) ? 'teal' : ['Under Maintenance', 'Scheduled', 'Rescheduled', 'Medium'].includes(value) ? 'warning' : 'neutral'
  return <Badge tone={tone as 'success' | 'warning' | 'danger' | 'teal' | 'neutral'}>{value}</Badge>
}

export function Panel({ title, eyebrow, action, children, className = '', id, style }: { title?: string; eyebrow?: string; action?: ReactNode; children: ReactNode; className?: string; id?: string; style?: React.CSSProperties }) {
  return <section id={id} style={style} className={`panel ${className}`}>{(title || eyebrow || action) && <div className="panel-header"> <div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}{title && <h2>{title}</h2>}</div>{action}</div>}{children}</section>
}

export function Modal({ open, title, subtitle, onClose, children, wide = false }: { open: boolean; title: string; subtitle?: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  return <AnimatePresence>{open && <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}><motion.div className={`modal ${wide ? 'modal-wide' : ''}`} initial={{ opacity: 0, y: 14, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 10, scale: .98 }}><div className="modal-header"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-btn" onClick={onClose}><X size={18} /></button></div>{children}</motion.div></motion.div>}</AnimatePresence>
}

export function ToastStack({ toasts, dismissToast }: { toasts: { id: string; title: string; message: string; tone: string }[]; dismissToast: (id: string) => void }) {
  return <div className="toast-stack"><AnimatePresence>{toasts.map((toast) => <motion.div key={toast.id} className={`toast toast-${toast.tone}`} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}><div className="toast-mark">{toast.tone === 'success' ? <ShieldCheck size={16} /> : toast.tone === 'warning' || toast.tone === 'error' ? <AlertTriangle size={16} /> : <Sparkles size={16} />}</div><div><strong>{toast.title}</strong><span>{toast.message}</span></div><button className="toast-close" onClick={() => dismissToast(toast.id)}><X size={14} /></button></motion.div>)}</AnimatePresence></div>
}

export function Toggle({ checked, onChange, label, hint }: { checked: boolean; onChange: (checked: boolean) => void; label: string; hint?: string }) { return <label className="toggle-row"><span><strong>{label}</strong>{hint && <small>{hint}</small>}</span><button type="button" className={`toggle ${checked ? 'checked' : ''}`} onClick={() => onChange(!checked)} aria-pressed={checked}><span /></button></label> }

export function EmptyState({ icon: Icon = Layers3, title, description }: { icon?: typeof Layers3; title: string; description: string }) { return <div className="empty-state"><div className="empty-icon"><Icon size={21} /></div><strong>{title}</strong><span>{description}</span></div> }

export function FilterBar({ children }: { children: ReactNode }) { return <div className="filter-bar"><div className="filter-content">{children}</div><SlidersHorizontal size={16} className="filter-symbol" /></div> }

const JOB_PALETTE = [
  { bg: '#234e52', border: '#1d4043', text: '#ffffff' }, // deep teal
  { bg: '#2b6cb0', border: '#2c5282', text: '#ffffff' }, // slate blue
  { bg: '#4a5568', border: '#2d3748', text: '#ffffff' }, // neutral dark
  { bg: '#744210', border: '#5f370e', text: '#ffffff' }, // warm bronze
  { bg: '#2c7a7b', border: '#285e61', text: '#ffffff' }, // cyan teal
  { bg: '#44337a', border: '#322659', text: '#ffffff' }, // royal purple
  { bg: '#702459', border: '#521b41', text: '#ffffff' }, // berry
  { bg: '#365c55', border: '#284640', text: '#ffffff' }, // sage dark
  { bg: '#742a2a', border: '#63171b', text: '#ffffff' }, // brick
  { bg: '#3182ce', border: '#2b6cb0', text: '#ffffff' }, // sky blue
]

function getJobColor(jobId: string) {
  let h = 0
  for (let i = 0; i < jobId.length; i++) h = (h << 5) - h + jobId.charCodeAt(i)
  return JOB_PALETTE[Math.abs(h) % JOB_PALETTE.length]
}

export function GanttTimeline({
  tasks,
  machines,
  downtimes,
  onSelect,
  highlightChanges = false,
  view = 'Daily',
  currentDate,
  weekDays,
}: {
  tasks: ScheduleTask[]
  machines: { id: string; name: string; status: string; workingHours?: string }[]
  downtimes?: { machineId: string; start: string; end: string; startHour: number; endHour: number; type?: 'breakdown' | 'maintenance'; label?: string; date?: string }[]
  onSelect?: (task: ScheduleTask) => void
  highlightChanges?: boolean
  view?: 'Daily' | 'Weekly'
  currentDate?: string
  weekDays?: Array<{ dateStr: string; label: string; dayName: string; shortDate: string }>
}) {
  const { disruptions } = useApp()
  const [hoveredTask, setHoveredTask] = useState<ScheduleTask | null>(null)
  const [hoveredDowntime, setHoveredDowntime] = useState<any | null>(null)

  const hours = ['06', '08', '10', '12', '14', '16', '18', '20', '22']
  const totalHours = 16

  const parseRelHour = (timeStr: string) => {
    if (!timeStr) return 0
    const [h, m] = timeStr.split(':').map(Number)
    const validH = isNaN(h) ? 6 : h
    const validM = isNaN(m) ? 0 : m
    return (validH < 6 ? validH + 24 : validH) + validM / 60 - 6
  }

  const getPosition = (startStr: string) => {
    const relH = parseRelHour(startStr)
    return Math.max(0, Math.min(100, (relH / totalHours) * 100))
  }

  const getWidth = (startStr: string, endStr: string) => {
    const s = parseRelHour(startStr)
    const e = parseRelHour(endStr)
    const dur = Math.max(0.6, e - s)
    return Math.max(5, Math.min(100, (dur / totalHours) * 100))
  }

  // Derive breakdown downtime from props or from disruptions context
  const activeDowntimes = downtimes || disruptions
    .filter((d) => d.type === 'Machine Breakdown' && d.status !== 'Resolved')
    .map((d) => {
      const match = d.description.match(/(\d{1,2}:\d{2})/g)
      const start = match && match[0] ? match[0] : '10:00'
      const durMatch = d.recovery.match(/(\d+(\.\d+)?)h/)
      const dur = durMatch ? parseFloat(durMatch[1]) : 3.0
      const [sh, sm] = start.split(':').map(Number)
      const startH = (sh || 10) + (sm || 0) / 60
      const endH = startH + dur
      const eh = Math.floor(endH)
      const em = Math.round((endH - eh) * 60)
      const end = `${String(eh).padStart(2, '0')}:${String(em).padStart(2, '0')}`
      return {
        machineId: d.resource.split(' · ')[0],
        start,
        end,
        startHour: startH - 6,
        endHour: endH - 6,
        type: 'breakdown' as const,
        label: `BREAKDOWN (${start} – ${end})`,
        date: '2026-11-07',
      }
    })

  return (
    <div className="gantt-scroll-container">
      <div className="gantt gantt-timeline-wrapper">
        <div className="gantt-head">
          <div className="gantt-label">{view === 'Weekly' ? 'MACHINE / 7-DAY HORIZON' : 'MACHINE / 16H HORIZON'}</div>
          {view === 'Weekly' && weekDays ? (
            <div className="gantt-days">
              {weekDays.map((d) => (
                <div key={d.dateStr} className={`gantt-day-header ${d.dateStr === currentDate ? 'today' : ''}`}>
                  <strong>{d.dayName}</strong>
                  <span>{d.shortDate}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="gantt-hours">
              {hours.map((hour) => (
                <span key={hour}>{hour}:00</span>
              ))}
            </div>
          )}
        </div>
        <div className="gantt-body">
          {machines.map((machine) => {
            const machineTasks = tasks.filter((task) => task.machineId === machine.id)
            const machineDowntimes = activeDowntimes.filter((dt) => dt.machineId === machine.id)

            return (
              <div className="gantt-row" key={machine.id}>
                <div className="machine-lane">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <strong>{machine.id}</strong>
                    <StatusBadge value={machine.status as any} />
                  </div>
                  <span>{machine.name}</span>
                </div>
                <div className="timeline-lane">
                  {view === 'Weekly' && weekDays ? (
                    <div className="timeline-grid weekly-grid">
                      {weekDays.map((d) => (
                        <i key={d.dateStr} className={d.dateStr === currentDate ? 'today-col' : ''} />
                      ))}
                    </div>
                  ) : (
                    <div className="timeline-grid">
                      {hours.map((hour) => (
                        <i key={hour} />
                      ))}
                    </div>
                  )}

                  {/* Render Breakdown / Downtime Shaded Region */}
                  {machineDowntimes.map((dt, idx) => {
                    let leftPct = 0
                    let widthPct = 0
                    if (view === 'Weekly' && weekDays) {
                      const dtDate = dt.date || '2026-11-07'
                      const dayIdx = weekDays.findIndex((d) => d.dateStr === dtDate)
                      if (dayIdx === -1) return null
                      leftPct = (dayIdx / 7) * 100 + (Math.max(0, dt.startHour) / totalHours) * (100 / 7)
                      widthPct = Math.max(2.5, ((dt.endHour - dt.startHour) / totalHours) * (100 / 7))
                    } else {
                      leftPct = Math.max(0, (dt.startHour / totalHours) * 100)
                      widthPct = Math.max(5, ((dt.endHour - dt.startHour) / totalHours) * 100)
                    }

                    return (
                      <div
                        key={`dt-${idx}`}
                        className={`downtime-block ${dt.type || 'breakdown'}`}
                        style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                        onMouseEnter={() => setHoveredDowntime(dt)}
                        onMouseLeave={() => setHoveredDowntime(null)}
                      >
                        <span className="downtime-tag">
                          <AlertTriangle size={11} /> {dt.label || 'BREAKDOWN'}
                        </span>
                        {hoveredDowntime === dt && (
                          <div className="gantt-tooltip-card">
                            <strong style={{ color: '#ef4444' }}>⚠ Machine Breakdown & Downtime</strong>
                            <div><strong>Machine:</strong> {dt.machineId}</div>
                            {dt.date && <div><strong>Date:</strong> {dt.date}</div>}
                            <div><strong>Downtime Window:</strong> {dt.start} – {dt.end} ({(dt.endHour - dt.startHour).toFixed(1)} hrs)</div>
                            <div><strong>Solver Constraint:</strong> Operations strictly blocked & reassigned</div>
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {/* Render Scheduled / Rescheduled Operation Bars */}
                  {machineTasks.map((task, idx) => {
                    const colors = getJobColor(task.orderId)
                    let left = 0
                    let width = 0

                    if (view === 'Weekly' && weekDays) {
                      const taskDate = task.date || '2026-11-07'
                      let dayIdx = weekDays.findIndex((d) => d.dateStr === taskDate)
                      if (dayIdx === -1) {
                        if (task.date && task.endDate && task.date < weekDays[0].dateStr && task.endDate >= weekDays[0].dateStr) {
                          dayIdx = 0
                        }
                      }
                      if (dayIdx === -1) return null
                      const relH = Math.max(0, Math.min(16, parseRelHour(task.start)))
                      const relEnd = Math.max(relH + 0.6, Math.min(16, parseRelHour(task.end)))
                      const dur = relEnd - relH
                      left = (dayIdx / 7) * 100 + (relH / totalHours) * (100 / 7)
                      width = Math.max(2.8, Math.min(100 / 7, (dur / totalHours) * (100 / 7)))
                    } else {
                      left = getPosition(task.start)
                      width = getWidth(task.start, task.end)
                    }

                    const top = `${(task.lane % 2) * 32 + 6}px`
                    const isRescheduled = task.status === 'Rescheduled'
                    const isCompleted = task.status === 'Completed' || task.frozen

                    return (
                      <div
                        key={task.id || idx}
                        className={`gantt-bar-item ${isRescheduled ? 'gantt-bar-rescheduled' : ''}`}
                        style={{
                          left: `${left}%`,
                          width: `${width}%`,
                          top,
                          backgroundColor: colors.bg,
                          borderLeft: `4px solid ${isRescheduled ? '#60a5fa' : colors.border}`,
                          color: colors.text,
                        }}
                        onClick={() => onSelect?.(task)}
                        onMouseEnter={() => setHoveredTask(task)}
                        onMouseLeave={() => setHoveredTask(null)}
                      >
                        <b style={{ letterSpacing: '0.02em' }}>{task.orderId}</b>
                        <span style={{ fontSize: '9px', opacity: 0.9 }}>
                          {task.operationName || task.product.split(' ')[0]}
                        </span>
                        {isRescheduled && <span className="gantt-badge-new">NEW</span>}
                        {isCompleted && <span style={{ fontSize: '9px', opacity: 0.8 }}>✓</span>}

                        {/* Interactive Rich Tooltip */}
                        {hoveredTask?.id === task.id && (
                          <div className="gantt-tooltip-card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
                              <strong style={{ color: '#a7f3d0' }}>{task.orderId} · {task.product}</strong>
                              <span style={{ color: isRescheduled ? '#93c5fd' : '#cbd5e1' }}>{task.status}</span>
                            </div>
                            <div><strong>Operation:</strong> {task.operationName || 'Machining & Production'}</div>
                            <div><strong>Assigned Machine:</strong> {task.machineId}</div>
                            {task.date && <div><strong>Date:</strong> {task.date}{task.endDate && task.endDate !== task.date ? ` to ${task.endDate}` : ''}</div>}
                            <div><strong>Schedule Window:</strong> {task.start} – {task.end} {task.duration ? `(${task.duration.toFixed(1)} hrs)` : ''}</div>
                            <div><strong>Quantity:</strong> {task.quantity.toLocaleString()} units</div>
                            {task.frozen && <div style={{ color: '#6ee7b7' }}>🔒 Frozen Operation (Preserved)</div>}
                            {isRescheduled && <div style={{ color: '#93c5fd' }}>⚡ Reassigned / Shifted by CP-SAT recovery</div>}
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {machineTasks.length === 0 && machineDowntimes.length === 0 && (
                    <span className="timeline-empty">Available · No tasks scheduled</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export function MiniBar({ value, tone = 'teal' }: { value: number; tone?: 'teal' | 'amber' | 'brick' }) { return <div className="mini-bar"><span className={`mini-bar-fill ${tone}`} style={{ width: `${Math.min(100, value)}%` }} /></div> }

export function SelectField({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) { return <label className="field"><span>{label}</span><div className="select-wrap"><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{option}</option>)}</select><ChevronDown size={14} /></div></label> }
export function TextField({ label, value, onChange, type = 'text', placeholder }: { label: string; value: string | number; onChange: (value: string) => void; type?: string; placeholder?: string }) { return <label className="field"><span>{label}</span><input type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} /></label> }

export function ConfirmLine({ icon: Icon = Zap, title, description, action }: { icon?: typeof Zap; title: string; description: string; action: ReactNode }) { return <div className="confirm-line"><div className="confirm-icon"><Icon size={16} /></div><div><strong>{title}</strong><span>{description}</span></div><div className="confirm-action">{action}</div></div> }

export function Pagination({ page, pages, onChange }: { page: number; pages: number; onChange: (page: number) => void }) { return <div className="pagination"><span>Showing page {page} of {pages}</span><div><button className="icon-btn" disabled={page <= 1} onClick={() => onChange(page - 1)}><ChevronLeft size={15} /></button><button className="icon-btn" disabled={page >= pages} onClick={() => onChange(page + 1)}><ChevronRight size={15} /></button></div></div> }

export function QuickAction({ icon: Icon, label, description, onClick }: { icon: typeof Plus; label: string; description: string; onClick: () => void }) { return <button className="quick-action" onClick={onClick}><div className="quick-action-icon"><Icon size={18} /></div><div><strong>{label}</strong><span>{description}</span></div><ChevronRight size={16} /></button> }

export function SectionDivider({ children }: { children: ReactNode }) { return <div className="section-divider"><span>{children}</span></div> }
