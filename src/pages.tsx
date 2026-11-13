import { useEffect, useMemo, useState, type ComponentType, type FormEvent, type ReactNode } from 'react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Activity, AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, BellRing, Boxes, CalendarClock, CheckCircle2, ChevronLeft, ChevronRight, CircleDollarSign, ClipboardList, Clock3, CloudCog, Download, Factory, FileDown, FileText, Gauge, GitBranch, HardHat, Layers3, MoreHorizontal, PackageCheck, Pencil, Plus, Printer, RefreshCw, Search, ShieldCheck, Sparkles, TimerReset, Trash2, TrendingUp, UserRound, Wrench, X, Zap } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Badge, Button, ConfirmLine, EmptyState, FilterBar, GanttTimeline, LogoMark, MiniBar, Modal, PageHeader, Panel, PriorityBadge, QuickAction, SelectField, SectionDivider, StatCard, StatusBadge, TextField, Toggle } from './components'
import { OperationEditorModal } from './components/OperationEditorModal'
import { useApp } from './context/AppContext'
import { delayData, monthlyTrend, productionTrend } from './data/mockData'
import type { DisruptionType, FactorySettings, Machine, Order, Priority, ScheduleTask } from './types'

const chartTooltip = { contentStyle: { border: '1px solid #e1e6e3', borderRadius: 8, boxShadow: '0 10px 25px rgba(37,52,59,.08)', fontSize: 12 }, labelStyle: { color: '#25343b', fontWeight: 700 } }
const today = '2026-11-07'
const shortDate = (value: string) => new Date(`${value}T00:00:00`).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })

export function LandingPage() {
  const navigate = useNavigate()
  const [showLandingNav, setShowLandingNav] = useState(true)
  useEffect(() => {
    let lastScrollY = window.scrollY
    const handleScroll = () => {
      const currentScrollY = window.scrollY
      if (currentScrollY < 24 || currentScrollY < lastScrollY) setShowLandingNav(true)
      else if (currentScrollY > lastScrollY + 4) setShowLandingNav(false)
      lastScrollY = currentScrollY
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])
  const goToLogin = () => navigate('/login')
  return <div className="landing-page">
    <header className={`landing-nav ${showLandingNav ? '' : 'nav-hidden'}`}><a className="landing-brand" href="#home"><LogoMark /><span><strong>ReSchedule</strong><small>Production Intelligence</small></span></a><nav className="landing-links"><a href="#features">Features</a><a href="#how-it-works">How It Works</a><a href="#about">About</a></nav><Button className="landing-cta" onClick={goToLogin} icon={<ArrowRight size={14} />}>Get started</Button></header>
    <main>
      <section className="landing-hero" id="home"><div className="hero-copy"><div className="landing-kicker"><span className="kicker-dot" /> SMART MANUFACTURING <i /> INTELLIGENT AUTOMATION</div><h1>Production Never Stops.<br /><em>Neither Should You.</em></h1><p>Unexpected disruptions shouldn't bring your factory to a standstill. ReSchedule intelligently adapts your production plans, recovers lost time and keeps your operations moving.</p><div className="hero-actions"><Button onClick={goToLogin} icon={<ArrowRight size={15} />}>Explore ReSchedule</Button><a className="text-action" href="#how-it-works">Discover how it works <ChevronRight size={15} /></a></div><div className="hero-proof"><div className="proof-avatars"><span>AM</span><span>RK</span><span>PS</span></div><span><strong>Built for the moments</strong> when production plans change.</span></div></div><div className="hero-visual"><div className="hero-visual-label"><span className="pulse-dot" /> LIVE PRODUCTION MODEL <strong>01 / 03</strong></div><FactoryIllustration /><div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" /></div></section>
      <section className="trust-strip" aria-label="ReSchedule capabilities"><div><Gauge size={16} /><span>Adaptive production planning</span></div><div><AlertTriangle size={16} /><span>Intelligent disruption recovery</span></div><div><Wrench size={16} /><span>Optimized machine utilization</span></div><div><PackageCheck size={16} /><span>On-time delivery focus</span></div></section>
      <section className="landing-section features-section" id="features"><div className="section-heading"><div><div className="landing-kicker">THE CONTROL LAYER FOR CHANGE</div><h2>One disruption.<br /><em>A smarter way forward.</em></h2></div><p>Everything your factory needs to stay productive when plans change — without adding another layer of complexity.</p></div><div className="feature-grid"><FeatureCard number="01" icon={<CalendarClock size={21} />} title="Smart Production Scheduling" text="Generate efficient production schedules based on machine capacity, order priorities and delivery deadlines." art={<ScheduleFeatureArt />} /><FeatureCard number="02" icon={<AlertTriangle size={21} />} title="Disruption Recovery" text="Respond to machine breakdowns, urgent orders and material delays without starting your planning process from scratch." art={<DisruptionFeatureArt />} /><FeatureCard number="03" icon={<GitBranch size={21} />} title="Intelligent Rescheduling" text="Automatically reorganize production activities to reduce delays and make better use of available resources." art={<RescheduleFeatureArt />} /></div></section>
      <section className="landing-section workflow-section" id="how-it-works"><div className="section-heading centered"><div><div className="landing-kicker">A CLEARER OPERATING RHYTHM</div><h2>From disruption to recovery<br /><em>in three steps.</em></h2></div><p>Make the next decision visible. Keep the context intact. Move with confidence.</p></div><div className="workflow-steps"><WorkflowStep number="01" icon={<AlertTriangle size={19} />} title="Detect Disruption" text="Identify machine breakdowns, rush orders or material delays." /><div className="workflow-connector"><span /><ArrowRight size={15} /></div><WorkflowStep number="02" icon={<Activity size={19} />} title="Analyze Impact" text="Understand affected tasks, delivery deadlines and available resources." /><div className="workflow-connector"><span /><ArrowRight size={15} /></div><WorkflowStep number="03" icon={<Sparkles size={19} />} title="Reschedule Production" text="Generate an updated plan and recover operations efficiently." /></div></section>
      <section className="landing-section showcase-section" id="about"><div className="showcase-copy"><div className="landing-kicker">A BETTER VIEW OF THE FACTORY</div><h2>Plans change.<br /><em>Your visibility shouldn't.</em></h2><p>ReSchedule brings orders, machines and recovery decisions into one calm operating picture — so every team knows what moved and why.</p><div className="showcase-list"><div><CheckCircle2 size={15} /><span>One shared view of production capacity</span></div><div><CheckCircle2 size={15} /><span>Explainable recovery decisions, not black boxes</span></div><div><CheckCircle2 size={15} /><span>Operational continuity from floor to deadline</span></div></div><Button variant="outline" onClick={goToLogin} icon={<ArrowRight size={14} />}>See the workspace</Button></div><DashboardPreview /></section>
      <section className="landing-cta-section"><div className="cta-grid-line" /><div className="landing-kicker light-eyebrow">THE NEXT SHIFT STARTS HERE</div><h2>Keep Your Production<br /><em>Moving.</em></h2><p>Turn unexpected disruptions into manageable decisions with intelligent production recovery.</p><Button onClick={goToLogin} icon={<ArrowRight size={15} />}>Enter ReSchedule</Button></section>
    </main>
    <footer className="landing-footer"><div className="footer-brand"><LogoMark /><div><strong>ReSchedule</strong><span>Production Intelligence</span><p>Planning clarity for factories that cannot stop.</p></div></div><div className="footer-links"><div><b>Explore</b><a href="#features">Features</a><a href="#how-it-works">How it works</a><a href="#about">About</a></div><div><b>Workspace</b><button onClick={goToLogin}>Get started</button><button onClick={goToLogin}>Sign in</button></div></div><div className="footer-bottom"><span>© ReSchedule | Innovasia 2026</span><span>Production systems, made calmer.</span></div></footer>
  </div>
}

function FactoryIllustration() { return <svg className="factory-illustration" viewBox="0 0 660 530" role="img" aria-label="Isometric smart manufacturing facility with scheduling indicators"><defs><linearGradient id="factoryFloor" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#eaf0eb" /><stop offset="1" stopColor="#d4e2da" /></linearGradient><linearGradient id="machineBody" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#6d8980" /><stop offset="1" stopColor="#365c55" /></linearGradient><filter id="softShadow"><feGaussianBlur stdDeviation="8" /></filter></defs><ellipse cx="351" cy="449" rx="248" ry="35" fill="#b5c5bb" opacity=".25" filter="url(#softShadow)" /><path d="M93 355 342 197l260 150-245 151Z" fill="url(#factoryFloor)" stroke="#aec0b5" strokeWidth="1.5" /><path d="m342 197 0-58 260 148v60Z" fill="#cbdad1" stroke="#aec0b5" strokeWidth="1.5" /><path d="m93 355 0-56 249-160v58Z" fill="#dde8e0" stroke="#aec0b5" strokeWidth="1.5" /><path d="m153 328 189-121 185 107-191 121Z" fill="#f7faf6" stroke="#cfddd3" /><path d="m175 316 164-104 153 89-168 106Z" fill="#dce8df" /><path d="m218 311 118-75 110 63-121 77Z" fill="#a8b8a7" opacity=".32" /><path d="m224 284 72-46 45 26-72 46Z" fill="#46685f" opacity=".72" /><path d="m328 220 80 44-1 61-78-44Z" fill="url(#machineBody)" /><path d="m407 264 54-32 1 60-54 33Z" fill="#2f5049" /><path d="m330 280 47 27v28l-47-26Z" fill="#a6beb0" /><circle cx="350" cy="290" r="14" fill="#1f3b36" stroke="#b9d3c5" strokeWidth="4" /><circle cx="350" cy="290" r="5" fill="#91b69e"><animate attributeName="opacity" values=".35;1;.35" dur="2.8s" repeatCount="indefinite" /></circle><path d="m477 288 59-36 1 59-59 37Z" fill="#53766b" /><path d="m536 252 35 20v59l-34 19Z" fill="#2d4d45" /><path d="m478 302 36 20v27l-36-20Z" fill="#9fb9aa" /><path d="m198 342 38-24 40 23-40 24Z" fill="#f4f8f4" stroke="#c7d7cc" /><path d="m198 342 0 32 38 22v-31Z" fill="#d9e6dd" /><path d="m236 365 40-24v32l-40 23Z" fill="#b5c9bc" /><path d="M116 372h350" stroke="#73958a" strokeWidth="4" strokeDasharray="1 11" strokeLinecap="round" opacity=".85"><animate attributeName="stroke-dashoffset" from="0" to="-24" dur="2s" repeatCount="indefinite" /></path><circle cx="128" cy="372" r="7" fill="#365c55" /><circle cx="467" cy="372" r="7" fill="#365c55" /><path d="m525 176 52-30" stroke="#6d8980" strokeWidth="2" strokeDasharray="4 6" /><path d="m575 146 17 3-10 13" fill="none" stroke="#6d8980" strokeWidth="2" /><path d="m124 246 49-30" stroke="#6d8980" strokeWidth="2" strokeDasharray="4 6" /><path d="m173 216-4-14 13 8" fill="none" stroke="#6d8980" strokeWidth="2" /><g className="art-lights"><circle cx="300" cy="190" r="4" fill="#709c81"><animate attributeName="opacity" values=".3;1;.3" dur="1.8s" repeatCount="indefinite" /></circle><circle cx="316" cy="180" r="3" fill="#b58443"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite" /></circle><circle cx="332" cy="170" r="3" fill="#557a91"><animate attributeName="opacity" values=".25;1;.25" dur="2.1s" repeatCount="indefinite" /></circle></g></svg> }

function FeatureCard({ number, icon, title, text, art }: { number: string; icon: ReactNode; title: string; text: string; art: ReactNode }) { return <article className="feature-card"><div className="feature-card-top"><span className="feature-number">{number}</span><span className="feature-icon">{icon}</span></div><div className="feature-art">{art}</div><h3>{title}</h3><p>{text}</p><a href="#how-it-works">Learn more <ArrowRight size={13} /></a></article> }
function ScheduleFeatureArt() { return <div className="feature-schedule-art"><div className="schedule-art-head"><span /> <span /> <span /></div><div className="schedule-art-row"><b>M01</b><i /><i className="long" /><i /></div><div className="schedule-art-row"><b>M02</b><i className="late" /><i className="mid" /></div><div className="schedule-art-row"><b>M03</b><i className="short" /><i className="long blue" /></div><div className="schedule-art-rail" /></div> }
function DisruptionFeatureArt() { return <div className="feature-disruption-art"><div className="disruption-ring"><AlertTriangle size={21} /></div><div className="disruption-signal signal-one" /><div className="disruption-signal signal-two" /><div className="disruption-line line-one" /><div className="disruption-line line-two" /><span className="disruption-label">M02 OFFLINE</span><span className="disruption-time">08:42</span></div> }
function RescheduleFeatureArt() { return <div className="feature-reschedule-art"><div className="route route-a" /><div className="route route-b" /><div className="route route-c" /><span className="route-node node-start" /><span className="route-node node-end" /><span className="route-node node-alt" /><div className="route-card"><span>NEW PLAN</span><strong>M04</strong><i /></div></div> }
function WorkflowStep({ number, icon, title, text }: { number: string; icon: ReactNode; title: string; text: string }) { return <div className="workflow-step"><div className="workflow-step-top"><span>{number}</span><div>{icon}</div></div><h3>{title}</h3><p>{text}</p></div> }
function DashboardPreview() { return <div className="dashboard-preview"><div className="preview-browser-bar"><div className="preview-dots"><i /><i /><i /></div><span>reschedule / production overview</span><div className="preview-browser-status"><span /> LIVE</div></div><div className="preview-body"><aside><div className="preview-logo"><LogoMark light /><b>ReSchedule</b></div><div className="preview-nav active"><Gauge size={11} /> Overview</div><div className="preview-nav"><CalendarClock size={11} /> Schedule</div><div className="preview-nav"><Boxes size={11} /> Orders</div><div className="preview-nav"><Wrench size={11} /> Machines</div><div className="preview-nav"><AlertTriangle size={11} /> Disruptions <em>1</em></div></aside><div className="preview-main"><div className="preview-main-head"><div><span>WORKSPACE / OVERVIEW</span><h4>Production Overview</h4></div><div className="preview-user">AM</div></div><div className="preview-kpis"><PreviewKpi label="Active orders" value="24" tone="green" /><PreviewKpi label="Machines online" value="8/10" tone="sage" /><PreviewKpi label="Delayed orders" value="3" tone="amber" /></div><div className="preview-grid"><div className="preview-panel chart"><div className="preview-panel-head"><span>Production output</span><b>WEEKLY</b></div><div className="preview-chart"><i /><i /><i /><i /><svg viewBox="0 0 330 115" preserveAspectRatio="none"><path d="M0 98 C34 91 42 79 70 85 S106 53 133 63 S170 40 194 51 S220 78 247 51 S291 58 330 18" fill="none" stroke="#365c55" strokeWidth="3" /><path d="M0 100 C34 96 42 90 70 88 S106 67 133 70 S170 56 194 64 S220 83 247 70 S291 75 330 51" fill="none" stroke="#b2c3b7" strokeWidth="2" strokeDasharray="5 6" /></svg></div></div><div className="preview-panel preview-machine"><div className="preview-panel-head"><span>Machine status</span><b>8 / 10</b></div><PreviewMachine name="CNC Turning Cell" id="M01" value="86%" /><PreviewMachine name="Vertical Mill 02" id="M02" value="—" alert /><PreviewMachine name="Horizontal Mill" id="M03" value="74%" /></div></div><div className="preview-alert"><div className="preview-alert-icon"><AlertTriangle size={13} /></div><div><b>Recovery plan ready</b><span>O-1039 moved to M04 · deadline protected</span></div><ArrowRight size={13} /></div></div></div></div> }
function PreviewKpi({ label, value, tone }: { label: string; value: string; tone: string }) { return <div className="preview-kpi"><span className={tone} /><small>{label}</small><strong>{value}</strong></div> }
function PreviewMachine({ name, id, value, alert = false }: { name: string; id: string; value: string; alert?: boolean }) { return <div className="preview-machine-row"><span className={`preview-machine-dot ${alert ? 'alert' : ''}`} /><div><b>{name}</b><small>{id}</small></div><strong>{value}</strong></div> }

export function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('aarav@northstarcomponents.in')
  const [password, setPassword] = useState('reschedule-demo')
  return <div className="login-page"><div className="login-visual"><div className="login-brand"><LogoBadge /><div><span>ReSchedule</span><small>Production Intelligence</small></div></div><div className="login-visual-copy"><div className="eyebrow light-eyebrow">INNOVASIA 2026 · SMART AUTOMATION</div><h1>Keep production<br /><em>moving.</em></h1><p>Make better commitments when the unexpected happens on the factory floor.</p></div><div className="login-flow"><div className="flow-line" /><div className="flow-node node-a"><span>01</span><strong>Order</strong></div><div className="flow-node node-b"><span>02</span><strong>Plan</strong></div><div className="flow-node node-c"><span>03</span><strong>Recover</strong></div><div className="flow-note">A calmer way to protect delivery promises.</div></div><div className="login-visual-foot"><span>Built for MSME manufacturers</span><span>v0.8.4 prototype</span></div></div><div className="login-form-panel"><div className="login-form-inner"><div className="mobile-login-mark"><LogoBadge /></div><div className="eyebrow">FACTORY OPERATIONS PLATFORM</div><h2>Sign in to your workspace</h2><p className="login-intro">See what needs attention and what can move next.</p><form onSubmit={(event) => { event.preventDefault(); onLogin() }}><TextField label="Work email" value={email} onChange={setEmail} type="email" /><TextField label="Password" value={password} onChange={setPassword} type="password" /><div className="form-meta"><label className="check-label"><input type="checkbox" defaultChecked /> <span>Remember me</span></label><button type="button" className="link-button">Forgot password?</button></div><Button type="submit" className="full-width" icon={<ArrowRight size={16} />}>Sign in to ReSchedule</Button></form><div className="login-divider"><span>or</span></div><Button variant="outline" className="full-width" icon={<Sparkles size={15} />} onClick={onLogin}>Continue with demo workspace</Button><div className="login-footnote"><ShieldCheck size={14} /> Frontend prototype · No real credentials required</div></div></div></div>
}
function LogoBadge() { return <div className="login-logo-mark"><span /><span /><span /><span /><span /><span /></div> }

export function DashboardPage() {
  const {
    orders,
    machines,
    disruptions,
    generateSchedule,
    analyticsOverview,
    machineUtilizationData,
    productionOutputData,
    analyticsRange,
    setAnalyticsRange,
    lastUpdated,
  } = useApp()
  const navigate = useNavigate()

  const activeOrders = analyticsOverview?.total_active_orders ?? orders.filter((item) => item.status !== 'Completed').length
  const completedOrders = analyticsOverview?.completed_orders ?? orders.filter((item) => item.status === 'Completed').length
  const delayedOrders = analyticsOverview?.delayed_orders ?? orders.filter((item) => item.status === 'Delayed').length
  const availableCount = analyticsOverview?.available_machines ?? machines.filter((m) => m.status === 'Available').length
  const totalCount = analyticsOverview?.total_machines ?? machines.length

  // Build dynamic activity items from actual disruptions and orders
  const activityItems = disruptions.length > 0
    ? disruptions.slice(0, 4).map((d) => ({
        icon: AlertTriangle,
        title: `${d.type} reported`,
        detail: `${d.resource} · ${d.recovery}`,
        time: d.reported,
        tone: d.status === 'Resolved' ? 'success' : 'warning',
      }))
    : orders.slice(0, 4).map((o) => ({
        icon: PackageCheck,
        title: `Order ${o.id} registered`,
        detail: `${o.product} · ${o.quantity} units`,
        time: shortDate(o.orderDate),
        tone: 'info',
      }))

  const chartData = productionOutputData?.data && productionOutputData.data.length > 0
    ? productionOutputData.data
    : productionTrend.map((pt) => ({
        day: pt.day,
        planned_output: pt.output,
        target: pt.target,
      }))

  const totalPlannedUnits = productionOutputData?.total_planned_units
    ?? chartData.reduce((acc, row: any) => acc + (row.planned_output || 0), 0)

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="NORTHSTAR COMPONENTS / PLANT 01"
        title="Production Overview"
        subtitle="Monitor your factory operations and production performance backed by real engine data."
        actions={
          <div className="flex items-center gap-2">
            <div className="view-toggle compact">
              <button className={analyticsRange === 'today' ? 'selected' : ''} onClick={() => setAnalyticsRange('today')}>Today</button>
              <button className={analyticsRange === 'week' ? 'selected' : ''} onClick={() => setAnalyticsRange('week')}>This week</button>
              <button className={analyticsRange === 'month' ? 'selected' : ''} onClick={() => setAnalyticsRange('month')}>This month</button>
            </div>
            <div className="header-stamp">
              <span className="pulse-dot" /> Line status <strong>{disruptions.some((d) => d.status === 'Open') ? 'Disrupted' : 'Operational'}</strong>
            </div>
          </div>
        }
      />
      <div className="stats-grid four">
        <StatCard
          label="Total active orders"
          value={String(activeOrders)}
          detail="In production system"
          icon={ClipboardIcon}
        />
        <StatCard
          label="Completed orders"
          value={String(completedOrders)}
          detail="Delivered to customer"
          icon={PackageCheck}
          tone="blue"
        />
        <StatCard
          label="Available machines"
          value={`${availableCount}/${totalCount}`}
          detail="Capacity available now"
          icon={Gauge}
          tone="teal"
        />
        <StatCard
          label="Delayed orders"
          value={String(delayedOrders)}
          detail={delayedOrders > 0 ? "Require recovery review" : "All orders on schedule"}
          icon={AlertTriangle}
          tone={delayedOrders > 0 ? "amber" : "teal"}
        />
      </div>

      <div className="dashboard-grid top-grid">
        <Panel
          title="Production output"
          eyebrow="SCHEDULED OUTPUT VS TARGET"
          action={
            <span className="panel-meta">
              <span className="legend-dot sage" /> Planned output <span className="legend-dot grey" /> Shift target
            </span>
          }
          className="chart-panel"
        >
          <div className="chart-wrap chart-tall">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 8, left: -22, bottom: 0 }}>
                <defs>
                  <linearGradient id="outputFill" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#365c55" stopOpacity={0.22} />
                    <stop offset="100%" stopColor="#365c55" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#edf0ee" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#78838a', fontSize: 11 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#78838a', fontSize: 11 }} />
                <Tooltip {...chartTooltip} />
                <Area type="monotone" dataKey="planned_output" stroke="#365c55" strokeWidth={2.5} fill="url(#outputFill)" name="Planned units" />
                <Line type="monotone" dataKey="target" stroke="#a8b8a7" strokeDasharray="4 5" strokeWidth={1.5} dot={false} name="Target" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-foot">
            <span><strong>{totalPlannedUnits.toLocaleString()}</strong> units planned</span>
            <span className="muted-note">
              {lastUpdated ? `Live sync: ${lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}` : 'Data synchronized with CP-SAT engine'}
            </span>
          </div>
        </Panel>

        <Panel
          title="Scheduled machine status"
          eyebrow="CAPACITY SNAPSHOT"
          action={
            <button className="panel-link" onClick={() => navigate('/machines')}>
              View all <ArrowRight size={14} />
            </button>
          }
        >
          <div className="machine-list">
            {machines.slice(0, 5).map((machine) => {
              const utilItem = machineUtilizationData.find((u) => u.machine_id === machine.id)
              const utilPct = utilItem ? utilItem.utilization_pct : (machine.utilization || 0)
              const opStatus = utilItem ? utilItem.operational_status : machine.status
              const taskDesc = utilItem?.current_task || machine.task

              return (
                <div className="machine-row" key={machine.id}>
                  <div className="machine-ident">
                    <span className={`machine-state state-${opStatus.toLowerCase().replaceAll(' ', '-')}`} />
                    <div>
                      <strong>{machine.name}</strong>
                      <span>{machine.id} · {machine.type} · <em style={{ fontStyle: 'normal', color: '#6d8980' }}>{taskDesc}</em></span>
                    </div>
                  </div>
                  <div className="machine-util">
                    <div>
                      <span>{utilPct}%</span>
                      <small>sched. util</small>
                    </div>
                    <MiniBar
                      value={utilPct}
                      tone={opStatus === 'Breakdown' ? 'brick' : utilPct > 85 ? 'amber' : 'teal'}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </Panel>
      </div>

      <div className="dashboard-grid bottom-grid">
        <Panel
          title="Recent orders"
          eyebrow="COMMITMENTS"
          action={
            <button className="panel-link" onClick={() => navigate('/orders')}>
              Open order book <ArrowRight size={14} />
            </button>
          }
        >
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Product</th>
                  <th>Qty</th>
                  <th>Deadline</th>
                  <th>Priority</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.slice(0, 5).map((order) => (
                  <tr key={order.id}>
                    <td><strong className="mono">{order.id}</strong></td>
                    <td>{order.product}</td>
                    <td>{order.quantity.toLocaleString()}</td>
                    <td>{shortDate(order.deadline)}</td>
                    <td><PriorityBadge value={order.priority} /></td>
                    <td><StatusBadge value={order.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Recent factory events" eyebrow="SYSTEM LOG">
          <div className="activity-list">
            {activityItems.map((item, idx) => (
              <ActivityItem
                key={idx}
                icon={item.icon}
                title={item.title}
                detail={item.detail}
                time={item.time}
                tone={item.tone}
              />
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Keep the line moving" eyebrow="QUICK ACTIONS" className="quick-panel">
        <div className="quick-actions">
          <QuickAction
            icon={Plus}
            label="Add new order"
            description="Create a customer commitment"
            onClick={() => navigate('/orders')}
          />
          <QuickAction
            icon={AlertTriangle}
            label="Report disruption"
            description="Log an event affecting production"
            onClick={() => navigate('/disruptions')}
          />
          <QuickAction
            icon={Sparkles}
            label="Generate schedule"
            description="Refresh the plan with current capacity"
            onClick={() => { generateSchedule(); navigate('/schedule') }}
          />
        </div>
      </Panel>
    </div>
  )
}
function ClipboardIcon(props: { size?: number }) { return <ClipboardList {...props} /> }
function ActivityItem({ icon: Icon, title, detail, time, tone }: { icon: ComponentType<{ size?: number }>; title: string; detail: string; time: string; tone: string }) { return <div className="activity-item"><div className={`activity-icon ${tone}`}><Icon size={15} /></div><div><strong>{title}</strong><span>{detail}</span></div><time>{time}</time></div> }

export function SchedulePage() {
  const { schedule, machines, orders, generateSchedule, disruptions, analyticsOverview } = useApp()
  const downtimes = disruptions
    .filter((d) => d.type === 'Machine Breakdown' && d.status !== 'Resolved')
    .flatMap((d) => {
      const machineId = d.resource.split(' · ')[0]
      const timeMatch = (d.description || '').match(/(\d{1,2}):(\d{2})/)
      const startH = timeMatch ? parseInt(timeMatch[1]) : 10
      const durMatch = (d.recovery || '').match(/(\d+(\.\d+)?)h/)
      const dur = durMatch ? parseFloat(durMatch[1]) : 3.0
      const startHour = startH - 6
      const endHour = startHour + dur
      const pad = (n: number) => String(Math.floor(n)).padStart(2, '0')
      const start = `${pad(startH)}:${timeMatch ? timeMatch[2] : '00'}`
      const end = `${pad(startH + dur)}:00`
      return [{ machineId, start, end, startHour, endHour, type: 'breakdown' as const, label: `BREAKDOWN ${start}–${end}`, date: '2026-11-07' }]
    })
  const [currentDate, setCurrentDate] = useState<Date>(new Date('2026-11-07T00:00:00'))
  const [view, setView] = useState<'Daily' | 'Weekly'>('Daily')
  const [machineFilter, setMachineFilter] = useState('All machines')
  const [orderFilter, setOrderFilter] = useState('All orders')
  const [selected, setSelected] = useState<typeof schedule[number] | null>(null)

  const msPerDay = 24 * 60 * 60 * 1000
  const anchorTime = new Date('2026-11-03T00:00:00').getTime()
  const diffDays = Math.floor((currentDate.getTime() - anchorTime) / msPerDay)
  const weekOffset = Math.floor(diffDays / 7)
  const weekStartTime = anchorTime + weekOffset * 7 * msPerDay
  const weekStart = new Date(weekStartTime)
  const weekEnd = new Date(weekStartTime + 6 * msPerDay)

  const pad = (n: number) => String(n).padStart(2, '0')
  const formatDateYMD = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

  const currentDateStr = formatDateYMD(currentDate)
  const weekStartStr = formatDateYMD(weekStart)
  const weekEndStr = formatDateYMD(weekEnd)

  const dailyLabel = `${dayNames[currentDate.getDay()]}, ${pad(currentDate.getDate())} ${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`
  const weekLabel = weekStart.getMonth() === weekEnd.getMonth() && weekStart.getFullYear() === weekEnd.getFullYear()
    ? `${pad(weekStart.getDate())} – ${pad(weekEnd.getDate())} ${monthNames[weekStart.getMonth()]} ${weekStart.getFullYear()}`
    : `${pad(weekStart.getDate())} ${monthNames[weekStart.getMonth()]} – ${pad(weekEnd.getDate())} ${monthNames[weekEnd.getMonth()]} ${weekEnd.getFullYear()}`

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const day = new Date(weekStartTime + i * msPerDay)
    const dateStr = formatDateYMD(day)
    const dayShort = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][day.getDay()]
    const shortDate = `${pad(day.getDate())} ${monthNames[day.getMonth()].slice(0, 3)}`
    return {
      dateStr,
      label: `${dayShort} ${shortDate}`,
      dayName: dayShort,
      shortDate,
    }
  })

  const navigatePrevious = () => {
    setCurrentDate((prev) => {
      const daysToShift = view === 'Daily' ? 1 : 7
      return new Date(prev.getTime() - daysToShift * msPerDay)
    })
  }

  const navigateNext = () => {
    setCurrentDate((prev) => {
      const daysToShift = view === 'Daily' ? 1 : 7
      return new Date(prev.getTime() + daysToShift * msPerDay)
    })
  }

  // Filter tasks: machine, order, and date range overlap
  const filtered = schedule.filter((task) => {
    if (machineFilter !== 'All machines' && task.machineId !== machineFilter) return false
    if (orderFilter !== 'All orders' && task.orderId !== orderFilter) return false

    const taskStart = task.date || '2026-11-07'
    const taskEnd = task.endDate || taskStart

    if (view === 'Daily') {
      return taskStart <= currentDateStr && taskEnd >= currentDateStr
    } else {
      return taskStart <= weekEndStr && taskEnd >= weekStartStr
    }
  })

  // Filter downtimes: machine and date range overlap
  const filteredDowntimes = downtimes.filter((dt) => {
    if (machineFilter !== 'All machines' && dt.machineId !== machineFilter) return false
    const dtDate = (dt as any).date || '2026-11-07'
    if (view === 'Daily') {
      return dtDate === currentDateStr
    } else {
      return dtDate <= weekEndStr && dtDate >= weekStartStr
    }
  })

  return <div className="page-stack"><PageHeader eyebrow="PLANNING / CAPACITY VIEW" title="Production Schedule" subtitle="Visualize and manage your factory's production timeline." actions={<Button icon={<Sparkles size={15} />} onClick={generateSchedule}>Generate schedule</Button>} /><Panel className="schedule-toolbar"><div className="view-toggle"><button className={view === 'Daily' ? 'selected' : ''} onClick={() => setView('Daily')}>Daily view</button><button className={view === 'Weekly' ? 'selected' : ''} onClick={() => setView('Weekly')}>Weekly view</button></div><div className="date-navigator"><button className="icon-btn" onClick={navigatePrevious} title={view === 'Daily' ? 'Previous day' : 'Previous week'}><ChevronLeft size={15} /></button><strong>{view === 'Daily' ? dailyLabel : weekLabel}</strong><button className="icon-btn" onClick={navigateNext} title={view === 'Daily' ? 'Next day' : 'Next week'}><ChevronRight size={15} /></button></div><div className="toolbar-filters"><select value={machineFilter} onChange={(event) => setMachineFilter(event.target.value)}><option>All machines</option>{machines.map((machine) => <option value={machine.id} key={machine.id}>{machine.id} · {machine.name}</option>)}</select><select value={orderFilter} onChange={(event) => setOrderFilter(event.target.value)}><option>All orders</option>{orders.map((order) => <option value={order.id} key={order.id}>{order.id} · {order.product}</option>)}</select></div></Panel><div className="schedule-meta"><div className="schedule-legend"><span><i className="legend-block ongoing" /> Ongoing</span><span><i className="legend-block scheduled" /> Scheduled</span><span><i className="legend-block delayed" /> Delayed</span><span><i className="legend-block completed" /> Completed</span><span><i className="legend-block rescheduled" /> Rescheduled</span></div><span className="muted-note"><Clock3 size={14} /> Last updated 2 mins ago</span></div><Panel className="gantt-panel"><GanttTimeline tasks={filtered} machines={machines.filter((machine) => machineFilter === 'All machines' || machine.id === machineFilter)} onSelect={setSelected} downtimes={filteredDowntimes} view={view} currentDate={currentDateStr} weekDays={weekDays} /></Panel><div className="schedule-bottom-grid"><Panel title="Schedule health" eyebrow="AT A GLANCE"><div className="health-grid"><HealthItem label="On-time completion" value={`${analyticsOverview?.on_time_delivery_pct ?? (orders.length > 0 ? Math.round((orders.filter(o => o.status !== 'Delayed').length / orders.length) * 100) : 100)}%`} tone="green" /><HealthItem label="Capacity booked" value={`${analyticsOverview?.average_scheduled_utilization_pct ?? 0}%`} tone="teal" /><HealthItem label="At-risk deadlines" value={String(analyticsOverview?.delayed_orders ?? orders.filter(o => o.status === 'Delayed').length).padStart(2, '0')} tone={orders.some(o => o.status === 'Delayed') ? 'amber' : 'green'} /><HealthItem label="Active disruptions" value={String(analyticsOverview?.open_disruptions_count ?? disruptions.filter(d => d.status !== 'Resolved').length).padStart(2, '0')} tone={disruptions.some(d => d.status !== 'Resolved') ? 'brick' : 'grey'} /></div></Panel><Panel title="Planning notes" eyebrow="ENGINE INSIGHTS"><div className="note-list">{disruptions.filter((d) => d.status !== 'Resolved').length > 0 ? <div><span className="note-mark amber" /><p><strong>{disruptions.find((d) => d.status !== 'Resolved')?.resource} under disruption.</strong> Affects {disruptions.find((d) => d.status !== 'Resolved')?.affectedOrders?.length || 0} production order(s). Run smart rescheduling to recover operations.</p></div> : <div><span className="note-mark teal" /><p><strong>All machines operating normally.</strong> No active unplanned downtimes logged in the CP-SAT engine.</p></div>}<div><span className="note-mark sage" /><p><strong>{filtered.length} scheduled operation(s)</strong> visible across {machines.length} active machine lane(s).</p></div></div></Panel></div><Modal open={!!selected} onClose={() => setSelected(null)} title={selected?.orderId ?? 'Task detail'} subtitle="Production task detail"><div className="detail-grid"><Detail label="Product" value={selected?.product ?? ''} /><Detail label="Assigned machine" value={selected?.machineId ?? ''} /><Detail label="Production quantity" value={`${selected?.quantity.toLocaleString() ?? 0} units`} /><Detail label="Start time" value={selected?.start ?? ''} /><Detail label="End time" value={selected?.end ?? ''} /><Detail label="Current status" value={selected?.status ?? ''} /></div><div className="modal-actions"><Button variant="outline" onClick={() => setSelected(null)}>Close</Button><Button onClick={() => setSelected(null)}>Open order</Button></div></Modal></div>
}
function HealthItem({ label, value, tone }: { label: string; value: string; tone: string }) { return <div className="health-item"><span className={`health-dot ${tone}`} /><div><strong>{value}</strong><small>{label}</small></div></div> }
function Detail({ label, value }: { label: string; value: string }) { return <div className="detail-item"><span>{label}</span><strong>{value}</strong></div> }

const emptyOrder: Omit<Order, 'id'> = { product: 'Hydraulic Valve Housing', quantity: 240, orderDate: today, deadline: '2026-11-12', priority: 'Medium', machine: 'CNC-1', status: 'Pending', estimatedHours: 8 }
export function OrdersPage() {
  const { orders, machines, addOrder, updateOrder, updateOrderStatus, deleteOrder, pushToast, analyticsOverview } = useApp()
  const [query, setQuery] = useState('')
  const [priority, setPriority] = useState('All priorities')
  const [status, setStatus] = useState('All statuses')
  const [modal, setModal] = useState<'add' | 'edit' | 'view' | null>(null)
  // Always use the first real (non-mock) machine ID as default
  const realMachines = machines.filter((m) => !m.id.match(/^M0?\d+$/))
  const defaultMachineId = realMachines[0]?.id || machines[0]?.id || 'CNC-1'
  const [form, setForm] = useState<Omit<Order, 'id'>>({ ...emptyOrder, machine: defaultMachineId })
  const [selected, setSelected] = useState<Order | null>(null)
  const filtered = orders.filter((order) => `${order.id} ${order.product}`.toLowerCase().includes(query.toLowerCase()) && (priority === 'All priorities' || order.priority === priority) && (status === 'All statuses' || order.status === status))
  const openAdd = () => {
    // Re-read machines at open time to get latest backend IDs
    const realMs = machines.filter((m) => !m.id.match(/^M0?\d+$/))
    const firstMachineId = realMs[0]?.id || machines[0]?.id || 'CNC-1'
    setForm({
      product: '',
      quantity: 100,
      orderDate: today,
      deadline: '2026-11-20',
      priority: 'Medium',
      machine: firstMachineId,
      status: 'Pending',
      estimatedHours: 8,
    })
    setSelected(null)
    setModal('add')
  }
  const openEdit = (order: Order) => { setForm(order); setSelected(order); setModal('edit') }
  const save = (event: FormEvent) => {
    event.preventDefault()
    const product = (form.product || '').trim()
    const quantity = Number(form.quantity)
    if (!product) {
      pushToast('Validation error', 'Please enter a product name.', 'error')
      return
    }
    if (!quantity || quantity <= 0) {
      pushToast('Validation error', 'Quantity must be greater than 0.', 'error')
      return
    }
    if (modal === 'edit' && selected) {
      updateOrder({ ...form, product, quantity, id: selected.id })
    } else {
      addOrder({ ...form, product, quantity })
    }
    setModal(null)
  }
  // Show real machine IDs first; fall back to defaults if backend not loaded
  const realMachineIds = machines.filter((m) => !m.id.match(/^M0?\d+$/)).map((m) => m.id)
  const machineOptions = realMachineIds.length > 0 ? realMachineIds : machines.length > 0 ? machines.map((m) => m.id) : ['CNC-1', 'CNC-2', 'MILL-1', 'MILL-2', 'GRIND-1']
  return <div className="page-stack"><PageHeader eyebrow="OPERATIONS / CUSTOMER COMMITMENTS" title="Order Management" subtitle="Manage customer orders and delivery commitments." actions={<Button icon={<Plus size={16} />} onClick={openAdd}>Add order</Button>} /><div className="stats-grid four"><StatCard label="Total orders" value={String(analyticsOverview?.total_orders ?? orders.length)} detail="In current order book" icon={ClipboardIcon} /><StatCard label="Pending" value={String(analyticsOverview?.pending_orders ?? orders.filter((order) => order.status === 'Pending').length)} detail="Awaiting production" icon={Clock3} tone="amber" /><StatCard label="Completed" value={String(analyticsOverview?.completed_orders ?? orders.filter((order) => order.status === 'Completed').length)} detail="Delivered" icon={PackageCheck} tone="blue" /><StatCard label="Urgent orders" value={String(analyticsOverview?.urgent_orders ?? orders.filter((order) => order.priority === 'High').length)} detail="High priority commitments" icon={Zap} tone="brick" /></div><Panel className="table-panel"><FilterBar><div className="table-search"><Search size={15} /><input placeholder="Search by order or product..." value={query} onChange={(event) => setQuery(event.target.value)} /></div><select value={priority} onChange={(event) => setPriority(event.target.value)}><option>All priorities</option><option>High</option><option>Medium</option><option>Low</option></select><select value={status} onChange={(event) => setStatus(event.target.value)}><option>All statuses</option><option>Pending</option><option>In Production</option><option>Completed</option><option>Delayed</option></select></FilterBar><div className="table-wrap"><table className="operations-table"><thead><tr><th>Order ID</th><th>Product name</th><th>Quantity</th><th>Order date</th><th>Delivery deadline</th><th>Priority</th><th>Assigned machine</th><th>Status</th><th /></tr></thead><tbody>{filtered.map((order) => <tr key={order.id}><td><button className="link-button mono" onClick={() => { setSelected(order); setModal('view') }}>{order.id}</button></td><td><strong>{order.product}</strong></td><td>{order.quantity.toLocaleString()} units</td><td>{shortDate(order.orderDate)}</td><td className={order.status === 'Delayed' ? 'text-danger' : ''}>{shortDate(order.deadline)}</td><td><PriorityBadge value={order.priority} /></td><td><span className="machine-tag">{order.machine}</span></td><td><select className={`order-status-select status-${order.status.toLowerCase().replace(/\s+/g, '-')}`} value={order.status} onChange={(event) => updateOrderStatus(order.id, event.target.value as Order['status'])} title={`Change status for ${order.id}`}><option value="Pending">Pending</option><option value="In Production">In Production</option><option value="Completed">Completed</option><option value="Delayed">Delayed</option></select></td><td><div className="row-actions"><button className="icon-btn" title="Edit" onClick={() => openEdit(order)}><Pencil size={14} /></button><button className="icon-btn danger-icon" title="Delete" onClick={() => { if (window.confirm(`Remove ${order.id}?`)) deleteOrder(order.id) }}><Trash2 size={14} /></button></div></td></tr>)}</tbody></table>{filtered.length === 0 && <EmptyState icon={Search} title="No orders match" description="Try changing the search or filters." />}</div><div className="table-foot"><span>{filtered.length} visible orders</span><span>Showing live local workspace data</span></div></Panel><Modal open={modal === 'add' || modal === 'edit'} onClose={() => setModal(null)} title={modal === 'edit' ? 'Edit order' : 'Add new order'} subtitle="Capture the customer commitment before planning begins."><form onSubmit={save}><div className="form-grid"><TextField label="Product name" value={form.product} onChange={(value) => setForm({ ...form, product: value })} placeholder="e.g. Hydraulic Valve Housing" /><TextField label="Quantity" value={form.quantity} onChange={(value) => setForm({ ...form, quantity: Number(value) })} type="number" /><TextField label="Order date" value={form.orderDate} onChange={(value) => setForm({ ...form, orderDate: value })} type="date" /><TextField label="Delivery deadline" value={form.deadline} onChange={(value) => setForm({ ...form, deadline: value })} type="date" /><SelectField label="Priority" value={form.priority} onChange={(value) => setForm({ ...form, priority: value as Priority })} options={['High', 'Medium', 'Low']} /><SelectField label="Required machine" value={form.machine || machineOptions[0]} onChange={(value) => setForm({ ...form, machine: value })} options={machineOptions} /><SelectField label="Order status" value={form.status} onChange={(value) => setForm({ ...form, status: value as Order['status'] })} options={['Pending', 'In Production', 'Completed', 'Delayed']} /><TextField label="Estimated production time" value={form.estimatedHours} onChange={(value) => setForm({ ...form, estimatedHours: Number(value) })} type="number" /></div><div className="modal-actions"><Button variant="outline" onClick={() => setModal(null)}>Cancel</Button><Button type="submit">{modal === 'edit' ? 'Save changes' : 'Add order'}</Button></div></form></Modal><Modal open={modal === 'view'} onClose={() => setModal(null)} title={selected?.id ?? ''} subtitle="Order commitment detail"><div className="detail-grid">{selected && <><Detail label="Product" value={selected.product} /><Detail label="Quantity" value={`${selected.quantity.toLocaleString()} units`} /><Detail label="Order date" value={shortDate(selected.orderDate)} /><Detail label="Delivery deadline" value={shortDate(selected.deadline)} /><Detail label="Priority" value={selected.priority} /><Detail label="Assigned machine" value={selected.machine} /><div className="detail-item"><span>Status</span><div style={{ marginTop: 4 }}><select className={`order-status-select status-${selected.status.toLowerCase().replace(/\s+/g, '-')}`} value={selected.status} onChange={(event) => { const nextStatus = event.target.value as Order['status']; updateOrderStatus(selected.id, nextStatus); setSelected({ ...selected, status: nextStatus }) }} title="Click to change order status"><option value="Pending">Pending</option><option value="In Production">In Production</option><option value="Completed">Completed</option><option value="Delayed">Delayed</option></select></div></div><Detail label="Estimated time" value={`${selected.estimatedHours} hours`} /></>}</div><div className="modal-actions"><Button variant="outline" onClick={() => setModal(null)}>Close</Button>{selected && <Button onClick={() => { openEdit(selected) }}>Edit order</Button>}</div></Modal></div>
}

const emptyMachine: Omit<Machine, 'utilization' | 'task'> = { id: '', name: '', type: 'CNC Lathe', capacity: 16, status: 'Available', workingHours: '06:00 – 22:00' }
export function MachinesPage() {
  const { machines, addMachine, updateMachine, updateMachineStatus, pushToast, analyticsOverview, machineUtilizationData } = useApp()
  const [modal, setModal] = useState<'add' | 'edit' | 'view' | null>(null)
  const [form, setForm] = useState<Machine>({ ...emptyMachine, utilization: 0, task: 'Available for assignment' })
  const [selected, setSelected] = useState<Machine | null>(null)
  const stats = {
    total: analyticsOverview?.total_machines ?? machines.length,
    available: analyticsOverview?.available_machines ?? machines.filter((machine) => machine.status === 'Available').length,
    running: machineUtilizationData.filter((m) => m.operational_status === 'Running').length || machines.filter((machine) => machine.status === 'Running').length,
    maintenance: analyticsOverview?.broken_machines_count ?? machines.filter((machine) => machine.status === 'Under Maintenance' || machine.status === 'Breakdown').length,
  }
  const openAdd = () => {
    // Generate a unique machine ID using a suffix that won't collide with existing IDs
    // User can override the ID in the form before submitting
    const suffix = Date.now().toString().slice(-4)
    const nextId = `MCH-${suffix}`
    setForm({
      id: nextId,
      name: '',
      type: 'CNC Lathe',
      capacity: 16,
      status: 'Available',
      workingHours: '06:00 – 22:00',
      utilization: 0,
      task: 'Available for assignment',
    })
    setSelected(null)
    setModal('add')
  }
  const save = (event: FormEvent) => {
    event.preventDefault()
    const name = (form.name || '').trim()
    const id = (form.id || '').trim().toUpperCase()
    if (!name) {
      pushToast('Validation error', 'Please provide a machine name.', 'error')
      return
    }
    if (!id) {
      pushToast('Validation error', 'Please provide a machine ID.', 'error')
      return
    }
    if (modal === 'edit') {
      updateMachine({ ...form, name, id })
    } else {
      if (machines.some((m) => m.id.toUpperCase() === id)) {
        pushToast('Machine ID exists', `Machine ${id} already exists. Please choose a different ID.`, 'error')
        return
      }
      addMachine({ ...form, name, id })
    }
    setModal(null)
  }
  return <div className="page-stack"><PageHeader eyebrow="OPERATIONS / ASSET CAPACITY" title="Machine Management" subtitle="Monitor machine availability and production capacity." actions={<Button icon={<Plus size={16} />} onClick={openAdd}>Add machine</Button>} /><div className="stats-grid four"><StatCard label="Total machines" value={String(stats.total)} detail="Across the factory" icon={Wrench} /><StatCard label="Available" value={String(stats.available)} detail="Ready for assignment" icon={CheckCircle2} tone="teal" /><StatCard label="Running" value={String(stats.running)} detail="Currently producing" icon={Activity} tone="blue" /><StatCard label="Maintenance" value={String(stats.maintenance)} detail="Requires attention" icon={AlertTriangle} tone="amber" /></div><div className="machine-card-grid">{machines.map((machine) => { const utilItem = machineUtilizationData.find((u) => u.machine_id === machine.id); const currentUtil = utilItem ? utilItem.utilization_pct : (machine.utilization || 0); const currentStatus = utilItem ? utilItem.operational_status : machine.status; const currentTask = utilItem?.current_task || machine.task; return <div className="machine-card" key={machine.id}><div className="machine-card-head"><div className="machine-avatar"><Wrench size={17} /></div><div><div className="eyebrow">{machine.id} · {machine.type.toUpperCase()}</div><h3>{machine.name}</h3></div><button className="icon-btn" onClick={() => { setSelected(machine); setModal('view') }}><MoreHorizontal size={17} /></button></div><div className="machine-card-status"><StatusBadge value={currentStatus as any} /><span>{machine.workingHours}</span></div><div className="machine-card-metric"><div><span>Daily capacity</span><strong>{machine.capacity} hrs</strong></div><div><span>Scheduled Util.</span><strong>{currentUtil}%</strong></div></div><MiniBar value={currentUtil} tone={currentStatus === 'Breakdown' ? 'brick' : currentUtil > 85 ? 'amber' : 'teal'} /><div className="machine-task"><span>ASSIGNED TASK</span><strong>{currentTask}</strong></div><div className="machine-card-actions"><button onClick={() => { setForm(machine); setModal('edit') }}><Pencil size={13} /> Edit details</button><select value={machine.status} onChange={(event) => updateMachineStatus(machine.id, event.target.value as Machine['status'])}><option>Available</option><option>Running</option><option>Under Maintenance</option><option>Breakdown</option></select></div></div> })}</div><Modal open={modal === 'add' || modal === 'edit'} onClose={() => setModal(null)} title={modal === 'edit' ? 'Edit machine' : 'Add machine'} subtitle="Keep capacity data ready for the next plan."><form onSubmit={save}><div className="form-grid"><TextField label="Machine name" value={form.name} onChange={(value) => setForm({ ...form, name: value })} placeholder="e.g. CNC Turning Cell" /><TextField label="Machine ID" value={form.id} onChange={(value) => setForm({ ...form, id: value })} placeholder="e.g. M09" /><SelectField label="Machine type" value={form.type} onChange={(value) => setForm({ ...form, type: value })} options={['CNC Lathe', 'Milling Center', 'Fiber Laser', 'Surface Grinder', 'Press Brake', 'Assembly']} /><TextField label="Daily capacity" value={form.capacity} onChange={(value) => setForm({ ...form, capacity: Number(value) })} type="number" /><TextField label="Working hours" value={form.workingHours} onChange={(value) => setForm({ ...form, workingHours: value })} /><SelectField label="Availability" value={form.status} onChange={(value) => setForm({ ...form, status: value as Machine['status'] })} options={['Available', 'Running', 'Under Maintenance', 'Breakdown']} /></div><div className="modal-actions"><Button variant="outline" onClick={() => setModal(null)}>Cancel</Button><Button type="submit">{modal === 'edit' ? 'Save machine' : 'Add machine'}</Button></div></form></Modal><Modal open={modal === 'view'} onClose={() => setModal(null)} title={selected?.name ?? ''} subtitle="Machine information"><div className="detail-grid">{selected && <><Detail label="Machine ID" value={selected.id} /><Detail label="Type" value={selected.type} /><Detail label="Daily capacity" value={`${selected.capacity} hours`} /><Detail label="Utilization" value={`${selected.utilization}%`} /><Detail label="Status" value={selected.status} /><Detail label="Assigned task" value={selected.task} /></>}</div><div className="modal-actions"><Button onClick={() => setModal(null)}>Close</Button></div></Modal></div>
}

export function DisruptionsPage() {
  const {
    machines,
    orders,
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
    analyzeDisruption,
    pushToast,
  } = useApp()

  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'breakdowns' | 'material-delays' | 'rush-orders'>('breakdowns')

  // Search & Filter state
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  // Modals state
  const [breakdownModalOpen, setBreakdownModalOpen] = useState(false)
  const [recoverModalItem, setRecoverModalItem] = useState<any | null>(null)
  const [materialDelayModalOpen, setMaterialDelayModalOpen] = useState(false)
  const [receiveModalItem, setReceiveModalItem] = useState<any | null>(null)
  const [rushOrderModalOpen, setRushOrderModalOpen] = useState(false)
  const [detailModalItem, setDetailModalItem] = useState<any | null>(null)

  // Breakdown Form
  const [bdMachineId, setBdMachineId] = useState(machines[0]?.id || 'CNC-1')
  const [bdDescription, setBdDescription] = useState('')
  const [bdStartTime, setBdStartTime] = useState('10:00')
  const [bdRepairHours, setBdRepairHours] = useState('3.0')
  const [bdSeverity, setBdSeverity] = useState('Critical')
  const [bdNotes, setBdNotes] = useState('')

  // Recover Form
  const [recNotes, setRecNotes] = useState('Repairs completed, test cycle verified, returned to production queue.')

  // Material Delay Form
  const [matId, setMatId] = useState(materials[0]?.material_id || 'MAT-001')
  const [matReason, setMatReason] = useState('Freight logistics delay')
  const [matSupplier, setMatSupplier] = useState('')
  const [matRequiredQty, setMatRequiredQty] = useState('50.0')
  const [matAvailableQty, setMatAvailableQty] = useState('20.0')
  const [matArrivalDate, setMatArrivalDate] = useState('2026-11-08')
  const [matArrivalTime, setMatArrivalTime] = useState('14:00')
  const [matSeverity, setMatSeverity] = useState('High')

  // Receive Material Form
  const [recQty, setRecQty] = useState('30.0')
  const [recNotesMat, setRecNotesMat] = useState('Received and verified against QA sheet.')

  // Rush Order Form
  const [rushCustomer, setRushCustomer] = useState('')
  const [rushProduct, setRushProduct] = useState('')
  const [rushQuantity, setRushQuantity] = useState('50')
  const [rushDeadline, setRushDeadline] = useState('2026-11-09')
  const [rushOps, setRushOps] = useState<Array<{ name: string; time: number; machines: string[] }>>([
    { name: 'Turning', time: 2.0, machines: ['CNC-1', 'CNC-2'] },
    { name: 'Milling', time: 1.5, machines: ['MILL-1', 'MILL-2'] },
  ])

  // Sync default material values when material selection changes
  useEffect(() => {
    const found = materials.find((m) => m.material_id === matId)
    if (found) {
      if (found.supplier) setMatSupplier(found.supplier)
      setMatAvailableQty(String(found.available_quantity))
    }
  }, [matId, materials])

  // Handlers
  const handleReportBreakdown = async (e: FormEvent) => {
    e.preventDefault()
    if (!bdMachineId) {
      pushToast('Validation error', 'Please select a machine.', 'error')
      return
    }
    if (!bdDescription.trim()) {
      pushToast('Validation error', 'Please describe the breakdown failure.', 'error')
      return
    }
    await reportBreakdownAction({
      machine_id: bdMachineId,
      description: bdDescription.trim(),
      breakdown_start: bdStartTime,
      estimated_repair_hours: parseFloat(bdRepairHours) || 3.0,
      severity: bdSeverity,
      notes: bdNotes,
    })
    setBreakdownModalOpen(false)
    setBdDescription('')
  }

  const handleRecoverBreakdown = async (e: FormEvent) => {
    e.preventDefault()
    if (!recoverModalItem) return
    await recoverBreakdownAction(recoverModalItem.disruption_id, {
      recovery_notes: recNotes,
    })
    setRecoverModalItem(null)
  }

  const handleReportMaterialDelay = async (e: FormEvent) => {
    e.preventDefault()
    if (!matId) {
      pushToast('Validation error', 'Please select a material.', 'error')
      return
    }
    await reportMaterialDelayAction({
      material_id: matId,
      delay_reason: matReason.trim(),
      supplier: matSupplier.trim(),
      required_quantity: parseFloat(matRequiredQty) || 50.0,
      available_quantity: parseFloat(matAvailableQty) || 0.0,
      expected_arrival_date: matArrivalDate,
      expected_arrival_time: matArrivalTime,
      severity: matSeverity,
    })
    setMaterialDelayModalOpen(false)
  }

  const handleReceiveMaterial = async (e: FormEvent) => {
    e.preventDefault()
    if (!receiveModalItem) return
    await receiveMaterialDelayAction(receiveModalItem.disruption_id, {
      received_quantity: parseFloat(recQty) || 0,
      notes: recNotesMat,
    })
    setReceiveModalItem(null)
  }

  const handleAddRushOp = () => {
    setRushOps([...rushOps, { name: 'Finishing', time: 1.0, machines: ['GRIND-1'] }])
  }

  const handleRemoveRushOp = (index: number) => {
    if (rushOps.length <= 1) {
      pushToast('Warning', 'A rush order must have at least one operation.', 'warning')
      return
    }
    setRushOps(rushOps.filter((_, idx) => idx !== index))
  }

  const handleCreateRushOrder = async (e: FormEvent) => {
    e.preventDefault()
    if (!rushCustomer.trim() || !rushProduct.trim()) {
      pushToast('Validation error', 'Customer name and product name are required.', 'error')
      return
    }
    const operationsPayload = rushOps.map((op, idx) => ({
      operation_name: op.name,
      processing_time: op.time,
      eligible_machine_ids: op.machines,
      sequence_number: idx + 1,
    }))

    await createRushOrderAction({
      customer_name: rushCustomer.trim(),
      product_name: rushProduct.trim(),
      quantity: parseInt(rushQuantity, 10) || 50,
      deadline: rushDeadline,
      operations: operationsPayload,
    })
    setRushOrderModalOpen(false)
    setRushCustomer('')
    setRushProduct('')
  }

  // Filtered lists
  const filteredBreakdowns = breakdowns.filter((b) => {
    const matchesSearch =
      !searchTerm ||
      b.disruption_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (b.machine_id && b.machine_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (b.description && b.description.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesStatus = statusFilter === 'ALL' || b.status.toUpperCase() === statusFilter.toUpperCase()
    return matchesSearch && matchesStatus
  })

  const filteredMaterialDelays = materialDelays.filter((m) => {
    const matchesSearch =
      !searchTerm ||
      m.disruption_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (m.material_id && m.material_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (m.supplier && m.supplier.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (m.description && m.description.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesStatus = statusFilter === 'ALL' || m.status.toUpperCase() === statusFilter.toUpperCase()
    return matchesSearch && matchesStatus
  })

  const filteredRushOrders = rushOrders.filter((r) => {
    const matchesSearch =
      !searchTerm ||
      r.rush_order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.product_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'ALL' || r.status.toUpperCase() === statusFilter.toUpperCase()
    return matchesSearch && matchesStatus
  })

  const activeBreakdownsCount = disruptionSummary?.active_machine_breakdowns ?? breakdowns.filter((b) => b.status !== 'Recovered').length
  const activeDelaysCount = disruptionSummary?.active_material_delays ?? materialDelays.filter((m) => m.status !== 'Received').length
  const openRushCount = disruptionSummary?.open_rush_orders ?? rushOrders.filter((r) => r.status !== 'Scheduled' && r.status !== 'Completed').length
  const totalAffectedCount = disruptionSummary?.total_affected_orders ?? 0

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="OPERATIONS / EXCEPTION CONTROL"
        title="Disruption Management Workspace"
        subtitle="Manage machine breakdowns, material delivery delays, and urgent rush orders connected to CP-SAT solver recovery."
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              icon={<RefreshCw size={14} />}
              onClick={refreshDisruptionsData}
            >
              Refresh Data
            </Button>
            {activeTab === 'breakdowns' && (
              <Button icon={<Wrench size={14} />} onClick={() => setBreakdownModalOpen(true)}>
                Report Breakdown
              </Button>
            )}
            {activeTab === 'material-delays' && (
              <Button icon={<Boxes size={14} />} onClick={() => setMaterialDelayModalOpen(true)}>
                Report Material Delay
              </Button>
            )}
            {activeTab === 'rush-orders' && (
              <Button icon={<Zap size={14} />} onClick={() => setRushOrderModalOpen(true)}>
                Create Rush Order
              </Button>
            )}
          </div>
        }
      />

      {/* Top Workspace KPI Summary Cards */}
      <div className="stats-grid four">
        <StatCard
          label="Machine Breakdowns"
          value={String(activeBreakdownsCount)}
          detail="Active offline cells"
          icon={Wrench}
          tone="brick"
        />
        <StatCard
          label="Material Delays"
          value={String(activeDelaysCount)}
          detail="Awaiting incoming stock"
          icon={Boxes}
          tone="amber"
        />
        <StatCard
          label="Open Rush Orders"
          value={String(openRushCount)}
          detail="Awaiting scheduler insertion"
          icon={Zap}
          tone="blue"
        />
        <StatCard
          label="Affected Orders"
          value={String(totalAffectedCount)}
          detail="Customer commitments at risk"
          icon={AlertTriangle}
          tone="teal"
        />
      </div>

      {/* Category Tabs */}
      <div className="flex border-b border-border gap-2 pb-0 mb-2">
        <button
          onClick={() => { setActiveTab('breakdowns'); setSearchTerm(''); setStatusFilter('ALL') }}
          className={`flex items-center gap-2 px-4 py-3 font-medium text-xs rounded-t border-b-2 transition-all ${
            activeTab === 'breakdowns'
              ? 'border-primary text-primary font-bold bg-white'
              : 'border-transparent text-muted hover:text-text hover:border-gray-300'
          }`}
        >
          <Wrench size={15} />
          <span>Machine Breakdowns</span>
          {activeBreakdownsCount > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-red-100 text-red-700 font-bold">
              {activeBreakdownsCount}
            </span>
          )}
        </button>

        <button
          onClick={() => { setActiveTab('material-delays'); setSearchTerm(''); setStatusFilter('ALL') }}
          className={`flex items-center gap-2 px-4 py-3 font-medium text-xs rounded-t border-b-2 transition-all ${
            activeTab === 'material-delays'
              ? 'border-primary text-primary font-bold bg-white'
              : 'border-transparent text-muted hover:text-text hover:border-gray-300'
          }`}
        >
          <Boxes size={15} />
          <span>Material Delays</span>
          {activeDelaysCount > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-amber-100 text-amber-800 font-bold">
              {activeDelaysCount}
            </span>
          )}
        </button>

        <button
          onClick={() => { setActiveTab('rush-orders'); setSearchTerm(''); setStatusFilter('ALL') }}
          className={`flex items-center gap-2 px-4 py-3 font-medium text-xs rounded-t border-b-2 transition-all ${
            activeTab === 'rush-orders'
              ? 'border-primary text-primary font-bold bg-white'
              : 'border-transparent text-muted hover:text-text hover:border-gray-300'
          }`}
        >
          <Zap size={15} />
          <span>Rush Orders</span>
          {openRushCount > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-blue-100 text-blue-800 font-bold">
              {openRushCount}
            </span>
          )}
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex justify-between items-center bg-white p-3 rounded border border-border">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <Search size={14} className="text-muted" />
          <input
            className="w-full text-xs outline-none bg-transparent"
            placeholder={
              activeTab === 'breakdowns'
                ? 'Search breakdowns by machine or ID...'
                : activeTab === 'material-delays'
                ? 'Search material delays by material or supplier...'
                : 'Search rush orders by customer, product, or ID...'
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-muted font-medium">Status:</span>
          <select
            className="text-xs bg-soft border border-border rounded px-2 py-1 outline-none"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            {activeTab === 'breakdowns' && (
              <>
                <option value="REPORTED">Reported</option>
                <option value="UNDER REPAIR">Under Repair</option>
                <option value="RECOVERED">Recovered</option>
              </>
            )}
            {activeTab === 'material-delays' && (
              <>
                <option value="AWAITING MATERIAL">Awaiting Material</option>
                <option value="RECEIVED">Received</option>
              </>
            )}
            {activeTab === 'rush-orders' && (
              <>
                <option value="AWAITING SCHEDULING">Awaiting Scheduling</option>
                <option value="SCHEDULED">Scheduled</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* TAB 1: MACHINE BREAKDOWNS */}
      {activeTab === 'breakdowns' && (
        <Panel
          title="Machine Breakdown Records"
          eyebrow="CELL DOWNTIME TRACKING"
          action={
            <Button
              variant="quiet"
              icon={<Plus size={13} />}
              onClick={() => setBreakdownModalOpen(true)}
            >
              Report New Breakdown
            </Button>
          }
        >
          {filteredBreakdowns.length === 0 ? (
            <EmptyState
              icon={Wrench}
              title="No machine breakdowns recorded"
              description="All manufacturing cells are currently operating under normal status."
            />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Breakdown ID</th>
                    <th>Machine</th>
                    <th>Failure Description</th>
                    <th>Downtime Window</th>
                    <th>Estimated Repair</th>
                    <th>Affected Orders</th>
                    <th>Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBreakdowns.map((b) => (
                    <tr key={b.disruption_id}>
                      <td>
                        <strong className="mono text-xs">{b.disruption_id}</strong>
                      </td>
                      <td>
                        <div className="font-semibold text-xs text-text">{b.machine_id || b.resource}</div>
                        <span className="text-[10px] text-muted">
                          {machines.find((m) => m.id === b.machine_id)?.name || 'Machine Cell'}
                        </span>
                      </td>
                      <td className="max-w-xs text-xs truncate" title={b.description}>
                        {b.description || 'Unplanned breakdown reported'}
                      </td>
                      <td className="text-xs">
                        {b.breakdown_start ? `From ${b.breakdown_start}` : 'Immediate'}
                      </td>
                      <td className="text-xs">
                        {b.estimated_repair_hours ? `${b.estimated_repair_hours} hrs` : '4.0 hrs'}
                      </td>
                      <td>
                        <span className="text-xs text-muted">
                          {b.affected_job_ids && b.affected_job_ids.length > 0
                            ? b.affected_job_ids.join(', ')
                            : 'None'}
                        </span>
                      </td>
                      <td>
                        <StatusBadge
                          value={
                            b.status === 'Under Repair' || b.status === 'Reported'
                              ? 'Breakdown'
                              : b.status === 'Recovered'
                              ? 'Resolved'
                              : (b.status as any)
                          }
                        />
                      </td>
                      <td className="text-right">
                        <div className="flex justify-end gap-1">
                          {b.status !== 'Recovered' && (
                            <Button
                              variant="quiet"
                              className="text-xs py-1"
                              icon={<CheckCircle2 size={13} />}
                              onClick={() => {
                                setRecoverModalItem(b)
                                setRecNotes('Repairs completed, test cycle verified.')
                              }}
                            >
                              Recover
                            </Button>
                          )}
                          <button
                            className="small-action"
                            onClick={() => setDetailModalItem(b)}
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}

      {/* TAB 2: MATERIAL DELAYS */}
      {activeTab === 'material-delays' && (
        <Panel
          title="Material Delays & Stock Shortages"
          eyebrow="SUPPLY CHAIN DISRUPTIONS"
          action={
            <Button
              variant="quiet"
              icon={<Plus size={13} />}
              onClick={() => setMaterialDelayModalOpen(true)}
            >
              Report Material Delay
            </Button>
          }
        >
          {filteredMaterialDelays.length === 0 ? (
            <EmptyState
              icon={Boxes}
              title="No material delays reported"
              description="Inventory levels and planned deliveries are currently meeting production requirements."
            />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Delay ID</th>
                    <th>Material</th>
                    <th>Supplier</th>
                    <th>Required / Avail</th>
                    <th>Shortage</th>
                    <th>Expected Arrival</th>
                    <th>Affected Ops</th>
                    <th>Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMaterialDelays.map((m) => (
                    <tr key={m.disruption_id}>
                      <td>
                        <strong className="mono text-xs">{m.disruption_id}</strong>
                      </td>
                      <td>
                        <div className="font-semibold text-xs text-text">{m.material_id || m.resource}</div>
                        <span className="text-[10px] text-muted">
                          {materials.find((mat) => mat.material_id === m.material_id)?.name || 'Raw Material'}
                        </span>
                      </td>
                      <td className="text-xs text-muted">{m.supplier || 'Vendor'}</td>
                      <td className="text-xs">
                        {m.required_quantity != null && m.available_quantity != null ? (
                          <span>
                            {m.required_quantity} / {m.available_quantity}
                          </span>
                        ) : (
                          'N/A'
                        )}
                      </td>
                      <td>
                        {m.shortage_quantity ? (
                          <span className="text-xs font-semibold text-red-600">
                            {m.shortage_quantity} kg
                          </span>
                        ) : (
                          <span className="text-xs text-muted">0</span>
                        )}
                      </td>
                      <td className="text-xs font-medium">
                        {m.expected_arrival || 'TBD'}
                      </td>
                      <td>
                        <span className="text-xs text-muted">
                          {m.affected_operation_ids && m.affected_operation_ids.length > 0
                            ? m.affected_operation_ids.join(', ')
                            : m.affected_job_ids?.join(', ') || 'None'}
                        </span>
                      </td>
                      <td>
                        <StatusBadge
                          value={
                            m.status === 'Received'
                              ? 'Resolved'
                              : m.status === 'Awaiting Material'
                              ? 'Ongoing'
                              : (m.status as any)
                          }
                        />
                      </td>
                      <td className="text-right">
                        <div className="flex justify-end gap-1">
                          {m.status !== 'Received' && (
                            <Button
                              variant="quiet"
                              className="text-xs py-1"
                              icon={<PackageCheck size={13} />}
                              onClick={() => {
                                setReceiveModalItem(m)
                                setRecQty(String(m.shortage_quantity || 30.0))
                              }}
                            >
                              Receive
                            </Button>
                          )}
                          <button
                            className="small-action"
                            onClick={() => setDetailModalItem(m)}
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}

      {/* TAB 3: RUSH ORDERS */}
      {activeTab === 'rush-orders' && (
        <Panel
          title="Urgent Rush Orders"
          eyebrow="HIGH-PRIORITY EXPEDITION"
          action={
            <Button
              variant="quiet"
              icon={<Plus size={13} />}
              onClick={() => setRushOrderModalOpen(true)}
            >
              Add Rush Order
            </Button>
          }
        >
          {filteredRushOrders.length === 0 ? (
            <EmptyState
              icon={Zap}
              title="No rush orders registered"
              description="Standard production sequence is active with no emergency insertion orders."
            />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Order ID</th>
                    <th>Customer & Product</th>
                    <th>Quantity</th>
                    <th>Deadline</th>
                    <th>Priority</th>
                    <th>Operations</th>
                    <th>Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRushOrders.map((r) => (
                    <tr key={r.rush_order_id}>
                      <td>
                        <strong className="mono text-xs">{r.rush_order_id}</strong>
                      </td>
                      <td>
                        <div className="font-semibold text-xs text-text">{r.customer_name}</div>
                        <span className="text-[10px] text-muted">{r.product_name}</span>
                      </td>
                      <td className="text-xs font-semibold">{r.quantity} pcs</td>
                      <td className="text-xs font-medium text-red-600">{r.deadline}</td>
                      <td>
                        <Badge tone="danger">Urgent</Badge>
                      </td>
                      <td>
                        <span className="text-xs text-muted">
                          {r.operations.length} steps ({r.operations.map((o) => o.operation_name).join(' → ')})
                        </span>
                      </td>
                      <td>
                        <StatusBadge
                          value={
                            r.status === 'Scheduled'
                              ? 'Scheduled'
                              : r.status === 'Awaiting Scheduling'
                              ? 'High'
                              : (r.status as any)
                          }
                        />
                      </td>
                      <td className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="primary"
                            className="text-xs py-1"
                            icon={<GitBranch size={13} />}
                            onClick={async () => {
                              await scheduleRushOrderAction(r.rush_order_id)
                              navigate('/rescheduling')
                            }}
                          >
                            Schedule
                          </Button>
                          <button
                            className="small-action"
                            onClick={() => setDetailModalItem(r)}
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}

      {/* MODAL 1: REPORT BREAKDOWN */}
      <Modal
        open={breakdownModalOpen}
        onClose={() => setBreakdownModalOpen(false)}
        title="Report Machine Breakdown"
        subtitle="Log an unplanned cell failure to mark machine capacity offline and compute affected schedule operations."
      >
        <form onSubmit={handleReportBreakdown}>
          <div className="form-grid">
            <SelectField
              label="Select Machine"
              value={bdMachineId}
              onChange={setBdMachineId}
              options={machines.map((m) => `${m.id} · ${m.name}`)}
            />
            <TextField
              label="Breakdown Start Time (e.g. 10:00)"
              value={bdStartTime}
              onChange={setBdStartTime}
              placeholder="10:00"
            />
            <TextField
              label="Estimated Repair Hours"
              value={bdRepairHours}
              onChange={setBdRepairHours}
              type="number"
              placeholder="3.0"
            />
            <SelectField
              label="Severity"
              value={bdSeverity}
              onChange={setBdSeverity}
              options={['Critical', 'High', 'Medium', 'Low']}
            />
          </div>
          <div className="my-3">
            <label className="field">
              <span>Failure Description</span>
              <textarea
                value={bdDescription}
                onChange={(e) => setBdDescription(e.target.value)}
                placeholder="e.g. Spindle bearing vibration alarm, spindle offline for bearing replacement."
                rows={3}
                required
              />
            </label>
          </div>
          <div className="my-2">
            <label className="field">
              <span>Maintenance Notes (Optional)</span>
              <input
                className="text-xs p-2 border border-border rounded w-full"
                value={bdNotes}
                onChange={(e) => setBdNotes(e.target.value)}
                placeholder="Technician dispatched from plant maintenance division."
              />
            </label>
          </div>
          <div className="modal-actions mt-4">
            <Button variant="outline" onClick={() => setBreakdownModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" icon={<AlertTriangle size={15} />}>
              Report Breakdown
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL 2: RECOVER MACHINE */}
      <Modal
        open={!!recoverModalItem}
        onClose={() => setRecoverModalItem(null)}
        title={`Recover Machine ${recoverModalItem?.machine_id || ''}`}
        subtitle="Record actual repair completion and restore cell availability in the factory model."
      >
        <form onSubmit={handleRecoverBreakdown}>
          <div className="p-3 bg-soft rounded border border-border mb-3 text-xs">
            <div>
              <strong>Breakdown ID:</strong> {recoverModalItem?.disruption_id}
            </div>
            <div>
              <strong>Failure:</strong> {recoverModalItem?.description}
            </div>
            <div>
              <strong>Reported Duration:</strong> {recoverModalItem?.estimated_repair_hours} hrs
            </div>
          </div>
          <label className="field">
            <span>Recovery Notes</span>
            <textarea
              value={recNotes}
              onChange={(e) => setRecNotes(e.target.value)}
              placeholder="Describe repairs conducted and verification test runs..."
              rows={3}
              required
            />
          </label>
          <div className="modal-actions mt-4">
            <Button variant="outline" onClick={() => setRecoverModalItem(null)}>
              Cancel
            </Button>
            <Button type="submit" icon={<CheckCircle2 size={15} />}>
              Confirm Machine Recovery
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL 3: REPORT MATERIAL DELAY */}
      <Modal
        open={materialDelayModalOpen}
        onClose={() => setMaterialDelayModalOpen(false)}
        title="Report Material Delivery Delay"
        subtitle="Log late raw material arrival to calculate production shortages and constrain dependent operation start times."
      >
        <form onSubmit={handleReportMaterialDelay}>
          <div className="form-grid">
            <SelectField
              label="Select Material"
              value={matId}
              onChange={setMatId}
              options={materials.map((m) => `${m.material_id} · ${m.name}`)}
            />
            <TextField
              label="Supplier"
              value={matSupplier}
              onChange={setMatSupplier}
              placeholder="e.g. Apex Metals Corp"
            />
            <TextField
              label="Required Quantity (kg/units)"
              value={matRequiredQty}
              onChange={setMatRequiredQty}
              type="number"
            />
            <TextField
              label="Available In-Stock (kg/units)"
              value={matAvailableQty}
              onChange={setMatAvailableQty}
              type="number"
            />
            <TextField
              label="Expected Arrival Date"
              value={matArrivalDate}
              onChange={setMatArrivalDate}
              type="date"
            />
            <TextField
              label="Expected Arrival Time"
              value={matArrivalTime}
              onChange={setMatArrivalTime}
              placeholder="14:00"
            />
            <SelectField
              label="Severity"
              value={matSeverity}
              onChange={setMatSeverity}
              options={['High', 'Critical', 'Medium', 'Low']}
            />
          </div>
          <div className="my-3">
            <label className="field">
              <span>Delay Reason</span>
              <textarea
                value={matReason}
                onChange={(e) => setMatReason(e.target.value)}
                placeholder="e.g. Freight customs clearance delay at port warehouse."
                rows={2}
                required
              />
            </label>
          </div>
          <div className="modal-actions mt-4">
            <Button variant="outline" onClick={() => setMaterialDelayModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" icon={<Boxes size={15} />}>
              Report Delay
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL 4: RECEIVE MATERIAL */}
      <Modal
        open={!!receiveModalItem}
        onClose={() => setReceiveModalItem(null)}
        title={`Receive Material for ${receiveModalItem?.disruption_id || ''}`}
        subtitle="Confirm physical receipt of delayed raw material to replenish inventory and release operational constraints."
      >
        <form onSubmit={handleReceiveMaterial}>
          <div className="p-3 bg-soft rounded border border-border mb-3 text-xs">
            <div>
              <strong>Disruption ID:</strong> {receiveModalItem?.disruption_id}
            </div>
            <div>
              <strong>Material:</strong> {receiveModalItem?.material_id}
            </div>
            <div>
              <strong>Reported Shortage:</strong> {receiveModalItem?.shortage_quantity} units
            </div>
          </div>
          <div className="form-grid">
            <TextField
              label="Received Quantity (units)"
              value={recQty}
              onChange={setRecQty}
              type="number"
            />
          </div>
          <div className="my-3">
            <label className="field">
              <span>Receipt Notes</span>
              <textarea
                value={recNotesMat}
                onChange={(e) => setRecNotesMat(e.target.value)}
                placeholder="Inspected and accepted at receiving dock..."
                rows={2}
              />
            </label>
          </div>
          <div className="modal-actions mt-4">
            <Button variant="outline" onClick={() => setReceiveModalItem(null)}>
              Cancel
            </Button>
            <Button type="submit" icon={<PackageCheck size={15} />}>
              Confirm Receipt
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL 5: CREATE RUSH ORDER */}
      <Modal
        open={rushOrderModalOpen}
        onClose={() => setRushOrderModalOpen(false)}
        title="Create Urgent Customer Rush Order"
        subtitle="Insert an emergency customer job with high priority into the production pipeline."
        wide
      >
        <form onSubmit={handleCreateRushOrder}>
          <div className="form-grid">
            <TextField
              label="Customer Name"
              value={rushCustomer}
              onChange={setRushCustomer}
              placeholder="e.g. AeroSpace Dynamics Ltd"
            />
            <TextField
              label="Product Name"
              value={rushProduct}
              onChange={setRushProduct}
              placeholder="e.g. Titanium Manifold Flange"
            />
            <TextField
              label="Order Quantity (units)"
              value={rushQuantity}
              onChange={setRushQuantity}
              type="number"
            />
            <TextField
              label="Deadline Date"
              value={rushDeadline}
              onChange={setRushDeadline}
              type="date"
            />
          </div>

          <div className="mt-4 mb-2">
            <div className="flex justify-between items-center mb-2">
              <strong className="text-xs font-semibold uppercase text-muted">
                Production Routing Operations ({rushOps.length})
              </strong>
              <Button variant="quiet" icon={<Plus size={13} />} onClick={handleAddRushOp}>
                Add Operation
              </Button>
            </div>

            <div className="space-y-2">
              {rushOps.map((op, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-soft rounded border border-border flex items-center justify-between gap-3 text-xs"
                >
                  <span className="font-bold text-muted mono">#{idx + 1}</span>
                  <div className="flex-1">
                    <span className="text-[10px] text-muted uppercase">Operation</span>
                    <input
                      className="w-full text-xs p-1 border border-border rounded bg-white"
                      value={op.name}
                      onChange={(e) => {
                        const updated = [...rushOps]
                        updated[idx].name = e.target.value
                        setRushOps(updated)
                      }}
                      placeholder="e.g. Turning"
                    />
                  </div>
                  <div className="w-24">
                    <span className="text-[10px] text-muted uppercase">Duration (hrs)</span>
                    <input
                      type="number"
                      step="0.5"
                      className="w-full text-xs p-1 border border-border rounded bg-white"
                      value={op.time}
                      onChange={(e) => {
                        const updated = [...rushOps]
                        updated[idx].time = parseFloat(e.target.value) || 1.0
                        setRushOps(updated)
                      }}
                    />
                  </div>
                  <div className="flex-1">
                    <span className="text-[10px] text-muted uppercase">Eligible Machine</span>
                    <select
                      className="w-full text-xs p-1 border border-border rounded bg-white"
                      value={op.machines[0]}
                      onChange={(e) => {
                        const updated = [...rushOps]
                        updated[idx].machines = [e.target.value]
                        setRushOps(updated)
                      }}
                    >
                      {machines.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.id} ({m.name})
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    className="icon-btn danger-icon mt-3"
                    onClick={() => handleRemoveRushOp(idx)}
                    title="Remove operation"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="modal-actions mt-4">
            <Button variant="outline" onClick={() => setRushOrderModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" icon={<Zap size={15} />}>
              Create Rush Order
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL 6: VIEW DETAILS */}
      <Modal
        open={!!detailModalItem}
        onClose={() => setDetailModalItem(null)}
        title="Disruption Record Details"
        subtitle="Complete database record and audit fields."
      >
        <div className="detail-grid">
          {detailModalItem &&
            Object.entries(detailModalItem).map(([key, val]) => (
              <Detail
                key={key}
                label={key.replace(/_/g, ' ')}
                value={
                  typeof val === 'object' && val !== null
                    ? JSON.stringify(val)
                    : String(val ?? 'None')
                }
              />
            ))}
        </div>
        <div className="modal-actions mt-4">
          <Button onClick={() => setDetailModalItem(null)}>Close</Button>
        </div>
      </Modal>
    </div>
  )
}

export function ReschedulingPage() {
  const {
    activeDisruption,
    disruptions,
    schedule,
    originalSchedule,
    machines,
    orders,
    generateSchedule,
    generateReschedule,
    approveSchedule,
    recalculateSchedule,
    impactData,
    explanations,
    proposedSchedule,
    proposedScheduleId,
    proposedHasChanges,
    proposedChangesCount,
    proposedMode,
    proposedSolverStatus,
    proposedWallTime,
    proposedObjectiveValue,
    proposedBestBound,
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
  } = useApp()

  const [prioritize, setPrioritize] = useState(true)
  const [delivery, setDelivery] = useState(true)
  const [idle, setIdle] = useState(false)
  const [overtime, setOvertime] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [approving, setApproving] = useState(false)
  const [viewGanttMode, setViewGanttMode] = useState<'proposed' | 'baseline'>('proposed')
  const [controlsHighlighted, setControlsHighlighted] = useState(false)

  const openDisruptions = disruptions.filter((d) => d.status === 'Open' || d.status === 'Analyzed')
  const hasActiveDisruption = openDisruptions.length > 0
  const hasBaseline = schedule && schedule.length > 0
  const hasProposal = !!proposedScheduleId

  // Explicit dynamic page states (PART 3)
  // STATE A: No active disruption, no baseline schedule
  // STATE B: No active disruption, existing schedule available
  // STATE C: Active disruption detected
  // STATE D: Optimization in progress
  // STATE E: Successful proposal
  // STATE F: No improvement found
  // STATE G: Infeasible schedule
  type PageState = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G'
  let currentState: PageState = 'B'
  if (generating) {
    currentState = 'D'
  } else if (proposedSolverStatus === 'INFEASIBLE' || !!proposedError) {
    currentState = 'G'
  } else if (hasProposal) {
    currentState = proposedHasChanges ? 'E' : 'F'
  } else if (hasActiveDisruption) {
    currentState = 'C'
  } else if (!hasBaseline) {
    currentState = 'A'
  } else {
    currentState = 'B'
  }

  const effectiveMode = hasActiveDisruption ? 'recovery' : 'optimization'

  const runGeneration = async (overrideMode?: 'optimization' | 'recovery') => {
    if (generating || approving) return
    clearProposedError()
    setGenerating(true)
    try {
      if (currentState === 'A') {
        await generateSchedule()
      } else {
        const mode = overrideMode || effectiveMode
        await generateReschedule({ mode, prioritize, delivery, idle, overtime })
      }
    } finally {
      setGenerating(false)
    }
  }

  const isApprovalDisabled =
    !hasProposal ||
    approving ||
    generating ||
    currentState === 'G' ||
    (proposalValidation && !proposalValidation.valid)

  const handleApprove = async () => {
    if (isApprovalDisabled) return
    setApproving(true)
    try {
      await approveSchedule()
    } finally {
      setApproving(false)
    }
  }

  const handleRecalculate = async () => {
    if (generating || approving) return
    setGenerating(true)
    try {
      const mode = proposedMode || effectiveMode
      await recalculateSchedule({ mode, prioritize, delivery, idle, overtime })
    } finally {
      setGenerating(false)
    }
  }

  const handleModifyClick = async () => {
    await startManualEdit()
  }

  const displaySchedule = proposedSchedule ?? schedule
  const ganttTasksToRender = viewGanttMode === 'baseline' && originalSchedule.length > 0 ? originalSchedule : displaySchedule

  const affected = activeDisruption?.affectedOrders ?? ['O-1039']
  const affectedOrders = orders.filter((order) => affected.includes(order.id))

  const downtimes = activeDisruption && activeDisruption.type === 'Machine Breakdown' ? (() => {
    const machineId = activeDisruption.resource.split(' · ')[0]
    const timeMatch = (activeDisruption.description || '').match(/(\d{1,2}):(\d{2})/)
    const startH = timeMatch ? parseInt(timeMatch[1]) : 10
    const durMatch = (activeDisruption.recovery || '').match(/(\d+(\.\d+)?)h/)
    const dur = durMatch ? parseFloat(durMatch[1]) : 3.0
    const startHour = startH - 6
    const endHour = startHour + dur
    const pad = (n: number) => String(Math.floor(n)).padStart(2, '0')
    const start = `${pad(startH)}:${timeMatch ? timeMatch[2] : '00'}`
    const end = `${pad(startH + dur)}:00`
    return [{ machineId, start, end, startHour, endHour, type: 'breakdown' as const, label: `BREAKDOWN ${start}–${end}` }]
  })() : []

  // Dynamic banner configuration based on State A-G
  const bannerConfig = {
    A: {
      eyebrow: 'STATE A · NO BASELINE SCHEDULE',
      title: 'No production schedule available',
      subtitle: 'Generate an initial optimized schedule from customer commitments and machine capacity.',
      badge: 'INITIAL PLANNING REQUIRED',
      tone: 'grey',
    },
    B: {
      eyebrow: 'STATE B · NORMAL MONITORING',
      title: 'Production schedule active · Monitoring schedule performance',
      subtitle: 'All machines operating normally. You can optimize the active baseline schedule to minimize idle time, overtime, and makespan.',
      badge: 'NORMAL OPTIMIZATION READY',
      tone: 'teal',
    },
    C: {
      eyebrow: 'STATE C · DISRUPTION DETECTED',
      title: 'Disruption detected · Recovery analysis required',
      subtitle: `${openDisruptions.length} active event(s) logged. Rebalance operations around downtime and protect commitments.`,
      badge: 'RECOVERY MODE ACTIVE',
      tone: 'amber',
    },
    D: {
      eyebrow: 'STATE D · OPTIMIZING CONSTRAINTS',
      title: 'Analyzing production constraints · Running CP-SAT optimization',
      subtitle: 'Google OR-Tools CP-SAT is evaluating machine compatibility, operation precedence, and weighted objectives.',
      badge: 'SOLVING MODEL...',
      tone: 'blue',
    },
    E: {
      eyebrow: 'STATE E · OPTIMIZED PROPOSAL READY',
      title: 'Optimized schedule ready',
      subtitle: proposedMode === 'recovery'
        ? 'Recovery schedule reallocated affected operations to protect deadlines.'
        : 'Baseline schedule rebalanced to minimize delivery tardiness and machine idle time.',
      badge: `${proposedChangesCount} CHANGE${proposedChangesCount === 1 ? '' : 'S'} PROPOSED`,
      tone: 'teal',
    },
    F: {
      eyebrow: 'STATE F · NO IMPROVEMENT FOUND',
      title: 'Current schedule is already the best solution found',
      subtitle: proposedSolverStatus === 'OPTIMAL'
        ? 'Mathematically proven optimal schedule: no alternative assignment achieves a superior objective score.'
        : 'Search limit reached: the solver verified that no better feasible plan could be found within the time limit.',
      badge: proposedSolverStatus === 'OPTIMAL' ? 'PROVEN OPTIMAL' : 'FEASIBLE · BEST FOUND',
      tone: 'green',
    },
    G: {
      eyebrow: 'STATE G · INFEASIBLE SCHEDULE',
      title: 'No feasible schedule found',
      subtitle: proposedError || 'The CP-SAT solver could not satisfy all delivery deadlines and machine constraints simultaneously.',
      badge: 'INFEASIBLE CONFLICT',
      tone: 'brick',
    },
  }[currentState]

  // Primary action button config based on current state
  const primaryButtonLabel = {
    A: 'Generate Initial Schedule',
    B: 'Optimize Current Schedule',
    C: 'Generate Recovery Schedule',
    D: 'Solving CP-SAT Model...',
    E: proposedMode === 'recovery' ? 'Re-run Recovery Schedule' : 'Re-optimize Schedule',
    F: 'Re-run Optimization',
    G: 'Retry Optimization',
  }[currentState]

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="OPERATIONS / DUAL-MODE OPTIMIZER"
        title="Schedule Optimization & Recovery"
        subtitle="Optimize baseline production schedules or recover dynamically when disruptions occur."
        actions={
          <div className="header-stamp">
            <span className={`pulse-dot ${hasActiveDisruption ? 'amber' : 'green'}`} />
            {hasActiveDisruption ? 'Disruption recovery mode' : 'Normal schedule optimization'}
          </div>
        }
      />

      {/* Dynamic State Banner */}
      <div className={`recovery-banner ${bannerConfig.tone === 'brick' ? 'bg-danger' : ''}`} style={bannerConfig.tone === 'brick' ? { background: '#9e3f36' } : undefined}>
        <div className="recovery-banner-icon">
          {currentState === 'G' ? <AlertTriangle size={19} /> : currentState === 'F' ? <CheckCircle2 size={19} /> : <Sparkles size={19} />}
        </div>
        <div>
          <div style={{ fontSize: 9, letterSpacing: '0.12em', color: '#b9d4c7', textTransform: 'uppercase', marginBottom: 2 }}>{bannerConfig.eyebrow}</div>
          <strong>{bannerConfig.title}</strong>
          <span>{bannerConfig.subtitle}</span>
        </div>
        <div className="recovery-banner-status">
          <span>STATUS</span>
          <strong>{bannerConfig.badge}</strong>
        </div>
      </div>

      <div className="rescheduling-grid">
        {/* Left Column - Panel 1: Context (Disruption summary OR Baseline info) */}
        {hasActiveDisruption ? (
          <Panel title="Disruption summary" eyebrow="01 / WHAT CHANGED" className="summary-panel">
            <div className="disruption-summary">
              <div className="summary-type">
                <div className="summary-icon"><AlertTriangle size={18} /></div>
                <div>
                  <StatusBadge value={activeDisruption?.severity ?? 'High'} />
                  <h3>{activeDisruption?.type ?? 'Machine Breakdown'}</h3>
                </div>
              </div>
              <div className="summary-grid">
                <Detail label="Affected resource" value={activeDisruption?.resource ?? '—'} />
                <Detail label="Reported time" value={activeDisruption?.reported ?? '—'} />
                <Detail label="Estimated recovery" value={activeDisruption?.recovery ?? '—'} />
                <Detail label="Affected orders" value={`${impactData?.affected_jobs_count || affectedOrders.length || 0} order${(impactData?.affected_jobs_count || affectedOrders.length) === 1 ? '' : 's'}`} />
              </div>
              <div className="summary-orders">
                {affectedOrders.map((order) => (
                  <div key={order.id}>
                    <span className="order-chip">{order.id}</span>
                    <span>{order.product}</span>
                    <PriorityBadge value={order.priority} />
                  </div>
                ))}
              </div>
            </div>
          </Panel>
        ) : (
          <Panel title="Production baseline status" eyebrow="01 / OPERATIONAL BASELINE" className="summary-panel">
            <div className="disruption-summary">
              <div className="summary-type">
                <div className="summary-icon" style={{ background: '#eaf3ee', color: '#365c55' }}><CheckCircle2 size={18} /></div>
                <div>
                  <StatusBadge value="Available" />
                  <h3>Active Production Schedule</h3>
                </div>
              </div>
              <div className="summary-grid">
                <Detail label="Factory status" value="Normal operations · 0 disruptions" />
                <Detail label="Active commitments" value={`${orders.length} total orders`} />
                <Detail label="Scheduled operations" value={`${schedule.length} tasks scheduled`} />
                <Detail label="Asset availability" value={`${machines.filter(m => m.status === 'Available' || m.status === 'Running').length} of ${machines.length} active`} />
              </div>
              <div className="summary-orders">
                <p style={{ fontSize: 11, color: '#72827d', lineHeight: 1.5, margin: 0 }}>
                  ReSchedule monitors baseline efficiency. Running optimization reorganizes task sequences and balances machine loads without requiring an unplanned disruption.
                </p>
              </div>
            </div>
          </Panel>
        )}

        {/* Left Column - Panel 2: Impact & Optimization Metrics (PART 4) */}
        <Panel title="Optimization & Impact Metrics" eyebrow="02 / SOLVER COMPARISON" className="impact-panel">
          <div className="impact-metrics">
            <ImpactMetric
              label="Makespan (Orig vs Rev)"
              value={impactData?.original_makespan_hours != null && impactData?.revised_makespan_hours != null
                ? `${impactData.original_makespan_hours.toFixed(1)}h → ${impactData.revised_makespan_hours.toFixed(1)}h`
                : schedule.length > 0 ? '16.0h' : '—'}
              detail={impactData?.makespan_change_hours != null ? `${impactData.makespan_change_hours > 0 ? '+' : ''}${impactData.makespan_change_hours.toFixed(1)}h makespan delta` : 'Total production span'}
              icon={Clock3}
              tone="teal"
            />
            <ImpactMetric
              label="Total tardiness"
              value={impactData?.original_total_tardiness_hours != null && impactData?.revised_total_tardiness_hours != null
                ? `${impactData.original_total_tardiness_hours.toFixed(1)}h → ${impactData.revised_total_tardiness_hours.toFixed(1)}h`
                : '0.0h'}
              detail={impactData?.tardiness_change_hours != null && impactData.tardiness_change_hours < 0 ? `${impactData.tardiness_change_hours.toFixed(1)}h tardiness reduced` : 'Delivery delay hours'}
              icon={TimerReset}
              tone={impactData?.revised_total_tardiness_hours ? 'amber' : 'teal'}
            />
            <ImpactMetric
              label="Reassigned operations"
              value={String(proposedReassignedCount || (impactData as any)?.reassigned_operations_count || 0)}
              detail="Shifted to alt machines"
              icon={ArrowRight}
              tone="blue"
            />
            <ImpactMetric
              label="Delayed operations"
              value={String(proposedDelayedCount || (impactData as any)?.delayed_operations_count || 0)}
              detail={`Unchanged: ${proposedUnchangedCount || (impactData as any)?.unaffected_operations_count || schedule.length}`}
              icon={CalendarClock}
              tone="brick"
            />
          </div>
          <div className="impact-callout">
            <ShieldCheck size={16} />
            <span>
              <strong>Hard constraints strictly enforced:</strong> Machine no-overlap, operation precedence, machine compatibility, and downtime windows verified by CP-SAT solver.
            </span>
          </div>
        </Panel>

        {/* Left Column - Panel 3: Rescheduling Controls */}
        <Panel
          id="rescheduling-controls-panel"
          title="Optimization controls"
          eyebrow="03 / WEIGHTED OBJECTIVES"
          className={`controls-panel ${controlsHighlighted ? 'highlight-box' : ''}`}
          style={controlsHighlighted ? { outline: '2px solid #365c55', transition: 'outline 0.3s ease' } : undefined}
        >
          <div className="controls-intro">
            Tune objective weights. The Google OR-Tools CP-SAT solver finds the best trade-off satisfying all production rules.
          </div>
          <Toggle label="Prioritize urgent orders" hint="Protect High priority customer commitments first" checked={prioritize} onChange={setPrioritize} />
          <Toggle label="Minimize delivery delays" hint="Penalize completion past delivery deadlines" checked={delivery} onChange={setDelivery} />
          <Toggle label="Minimize machine idle time" hint="Keep eligible work cells uniformly loaded" checked={idle} onChange={setIdle} />
          <Toggle label="Minimize overtime" hint="Discourage scheduling outside regular factory shifts" checked={overtime} onChange={setOvertime} />

          <div style={{ marginTop: 14 }}>
            <Button
              className="full-width recovery-button"
              onClick={() => runGeneration()}
              disabled={generating || approving}
              icon={generating ? <RefreshCw className="spin" size={16} /> : <Sparkles size={16} />}
            >
              {generating ? 'Solving CP-SAT Model...' : primaryButtonLabel}
            </Button>
          </div>

          {generating && (
            <div className="analysis-progress">
              <span className="progress-track"><span /></span>
              <small>Running Google OR-Tools CP-SAT · Mapping eligible machines · Eliminating overlaps</small>
            </div>
          )}
        </Panel>

        {/* Right Column - Panel 4: Recommended Schedule & Audit (PART 5 & PART 6) */}
        <Panel
          title="Recommended schedule"
          eyebrow="04 / SOLVER PROPOSAL"
          action={
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {hasProposal && (
                <div className="view-toggle compact">
                  <button className={viewGanttMode === 'proposed' ? 'selected' : ''} onClick={() => setViewGanttMode('proposed')}>
                    Proposed
                  </button>
                  <button className={viewGanttMode === 'baseline' ? 'selected' : ''} onClick={() => setViewGanttMode('baseline')}>
                    Baseline
                  </button>
                </div>
              )}
              <span className="panel-meta">
                <span className={`legend-dot ${hasProposal ? (proposedHasChanges ? 'teal' : 'sage') : 'amber'}`} />
                {hasProposal
                  ? (proposedHasChanges ? `${proposedChangesCount} operations changed` : 'Optimal — no changes needed')
                  : 'Awaiting solver run'}
              </span>
            </div>
          }
          className="recommended-panel"
        >
          {currentState === 'G' ? (
            <div className="infeasible-alert-box" style={{ padding: 20, background: '#fff5f4', border: '1px solid #f2cfcb', borderRadius: 8, margin: '16px 0' }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ color: '#c7493a' }}><AlertTriangle size={24} /></div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ margin: '0 0 6px', color: '#8a2b20', fontSize: 14 }}>No feasible schedule found (CP-SAT INFEASIBLE)</h4>
                  <p style={{ margin: 0, fontSize: 11, color: '#6d433f', lineHeight: 1.5 }}>
                    {proposedError || 'The requested deadlines, machine capacities, or downtime windows cannot be satisfied simultaneously without violating hard constraints.'}
                  </p>
                  <div style={{ marginTop: 12, fontSize: 11, color: '#553633' }}>
                    <strong>Recommended actions:</strong>
                    <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
                      <li>Enable "Minimize overtime" toggle to allow shift flexibility.</li>
                      <li>Review machine eligibility and add alternate compatible machines.</li>
                      <li>Extend tight delivery deadlines for lower-priority orders.</li>
                    </ul>
                  </div>
                  <div style={{ marginTop: 14, display: 'flex', gap: 8 }}>
                    <button
                      onClick={() => { clearProposedError(); runGeneration() }}
                      disabled={generating || approving}
                      style={{
                        padding: '6px 14px', fontSize: 11, fontWeight: 600, borderRadius: 6, cursor: 'pointer',
                        background: '#8a2b20', color: '#fff', border: 'none', letterSpacing: 0.3,
                        opacity: (generating || approving) ? 0.5 : 1,
                      }}
                    >
                      {generating ? 'Retrying…' : 'Try Again'}
                    </button>
                    <button
                      onClick={() => clearProposedError()}
                      style={{
                        padding: '6px 14px', fontSize: 11, fontWeight: 500, borderRadius: 6, cursor: 'pointer',
                        background: 'transparent', color: '#8a2b20', border: '1px solid #f2cfcb', letterSpacing: 0.3,
                      }}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : hasProposal ? (
            <>
              {/* Solver Audit Strip (PART 5) */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 12,
                  alignItems: 'center',
                  padding: '8px 12px',
                  background: '#f4f7f5',
                  border: '1px solid #d8e2dc',
                  borderRadius: 6,
                  marginBottom: 14,
                  fontSize: 10,
                }}
              >
                <div>
                  <span style={{ color: '#7a8984' }}>STATUS: </span>
                  <strong style={{
                    color: proposedSolverStatus === 'OPTIMAL' ? '#2f6d54' : proposedSolverStatus === 'FEASIBLE' ? '#325d72' : '#8a2b20',
                    fontFamily: 'var(--mono)',
                  }}>
                    {proposedSolverStatus || 'OPTIMAL'}
                  </strong>
                </div>
                <div>
                  <span style={{ color: '#7a8984' }}>MODE: </span>
                  <strong style={{ fontFamily: 'var(--mono)', textTransform: 'uppercase' }}>
                    {proposedMode || 'optimization'}
                  </strong>
                </div>
                <div>
                  <span style={{ color: '#7a8984' }}>EXECUTION TIME: </span>
                  <strong style={{ fontFamily: 'var(--mono)' }}>{proposedWallTime != null ? `${proposedWallTime}s` : '< 0.05s'}</strong>
                </div>
                {proposedObjectiveValue != null && (
                  <div>
                    <span style={{ color: '#7a8984' }}>OBJECTIVE: </span>
                    <strong style={{ fontFamily: 'var(--mono)' }}>{proposedObjectiveValue.toLocaleString()}</strong>
                  </div>
                )}
                {proposedBestBound != null && (
                  <div>
                    <span style={{ color: '#7a8984' }}>BEST BOUND: </span>
                    <strong style={{ fontFamily: 'var(--mono)' }}>{proposedBestBound.toLocaleString()}</strong>
                  </div>
                )}
              </div>

              {/* Manual Edit Mode Toolbar */}
              {isEditMode && (
                <div
                  style={{
                    padding: '12px 16px',
                    background: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    borderRadius: 8,
                    marginBottom: 16,
                    display: 'flex',
                    flexWrap: 'wrap',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ background: '#22c55e', color: '#fff', borderRadius: '50%', width: 26, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Pencil size={14} />
                    </div>
                    <div>
                      <strong style={{ color: '#166534', fontSize: 13, display: 'block' }}>
                        Manual Schedule Editor Active (Draft: {proposedScheduleId})
                      </strong>
                      <span style={{ color: '#15803d', fontSize: 11 }}>
                        Click any operation bar on the Gantt chart or click &quot;Edit&quot; in the table below to reassign machine or adjust timing.
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <Button
                      variant="outline"
                      onClick={validateCurrentProposal}
                      icon={<CheckCircle2 size={14} />}
                    >
                      Validate schedule
                    </Button>
                    <Button
                      variant="outline"
                      onClick={discardDraftProposal}
                      icon={<Trash2 size={14} />}
                    >
                      Discard changes
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setIsEditMode(false)}
                      icon={<X size={14} />}
                    >
                      Close editor
                    </Button>
                  </div>
                </div>
              )}

              {/* Proposal Validation Notice */}
              {proposalValidation && (
                <div
                  style={{
                    padding: '12px 16px',
                    background: proposalValidation.valid ? '#f0fdf4' : '#fff5f5',
                    border: `1px solid ${proposalValidation.valid ? '#bbf7d0' : '#fed7d7'}`,
                    borderRadius: 8,
                    marginBottom: 16,
                    display: 'flex',
                    gap: 12,
                    alignItems: 'flex-start',
                  }}
                >
                  {proposalValidation.valid ? (
                    <CheckCircle2 size={18} style={{ color: '#16a34a', marginTop: 2, flexShrink: 0 }} />
                  ) : (
                    <AlertTriangle size={18} style={{ color: '#e53e3e', marginTop: 2, flexShrink: 0 }} />
                  )}
                  <div style={{ flex: 1 }}>
                    <strong style={{ color: proposalValidation.valid ? '#166534' : '#9b2c2c', fontSize: 13, display: 'block' }}>
                      {proposalValidation.valid
                        ? `Schedule Valid (${proposalValidation.checks_passed}/${proposalValidation.total_checks} Hard Constraints Passed)`
                        : `Schedule Validation Warning (${proposalValidation.errors?.length || 0} Constraint Conflict${proposalValidation.errors?.length === 1 ? '' : 's'})`}
                    </strong>
                    {proposalValidation.errors && proposalValidation.errors.length > 0 && (
                      <ul style={{ margin: '6px 0 0 16px', padding: 0, fontSize: 11, color: '#9b2c2c', lineHeight: 1.5 }}>
                        {proposalValidation.errors.map((err: string, i: number) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}

              {/* Gantt Timeline */}
              <div style={{ marginBottom: 16 }}>
                <GanttTimeline
                  tasks={ganttTasksToRender}
                  machines={machines.slice(0, 5)}
                  downtimes={viewGanttMode === 'proposed' ? downtimes : []}
                  highlightChanges={viewGanttMode === 'proposed'}
                  onSelect={(task) => setSelectedOperationForEdit(task)}
                />
              </div>

              {/* Operations Table */}
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Machine</th>
                      <th>Order</th>
                      <th>Product</th>
                      <th>Operation</th>
                      <th>Scheduled start</th>
                      <th>Completion</th>
                      <th>Duration</th>
                      <th>Deadline</th>
                      <th>Priority</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displaySchedule.map((task) => (
                      <tr key={task.id} className={task.status === 'Rescheduled' ? 'highlight-row' : ''}>
                        <td>
                          <strong>{task.machineId}</strong>
                          {task.status === 'Rescheduled' && <span className="new-tag">MODIFIED</span>}
                        </td>
                        <td className="mono">{task.orderId}</td>
                        <td>{task.product}</td>
                        <td>{task.operationName || task.id}</td>
                        <td>{task.start}</td>
                        <td>{task.end}</td>
                        <td>{task.duration ? `${task.duration.toFixed(1)}h` : '—'}</td>
                        <td>{shortDate(orders.find((order) => order.id === task.orderId)?.deadline ?? today)}</td>
                        <td><PriorityBadge value={orders.find((order) => order.id === task.orderId)?.priority ?? 'Medium'} /></td>
                        <td style={{ textAlign: 'right' }}>
                          <Button
                            variant="outline"
                            onClick={() => setSelectedOperationForEdit(task)}
                            disabled={task.frozen || task.status === 'Completed'}
                            icon={<Pencil size={12} />}
                          >
                            Edit
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Explanations Section */}
              <div className="explanation" style={{ marginTop: 14 }}>
                <div className="explanation-mark"><Sparkles size={16} /></div>
                <div>
                  <div className="eyebrow">SCHEDULE EXPLANATION · GROUNDED REASONING</div>
                  {explanations.length > 0 ? (
                    explanations.slice(0, 4).map((exp, idx) => (
                      <p key={idx} style={{ marginBottom: 6 }}>
                        <strong>[{exp.type.replace('_', ' ').toUpperCase()}]</strong> {exp.message}
                      </p>
                    ))
                  ) : (
                    <p>
                      {proposedHasChanges
                        ? (proposedMode === 'recovery'
                            ? 'The CP-SAT solver rescheduled affected operations to alternative compatible machines to bypass the downtime window.'
                            : 'The CP-SAT solver rebalanced operations across available machines to reduce makespan and idle time.')
                        : (proposedSolverStatus === 'OPTIMAL'
                            ? 'The current schedule is already mathematically optimal for the chosen weights. No changes were required.'
                            : 'The current schedule is the best feasible solution found within the solver search limit.')}
                    </p>
                  )}
                </div>
              </div>

              {/* Optimal / No Changes Notice */}
              {!proposedHasChanges && currentState === 'F' && !isEditMode && (
                <div className="impact-callout" style={{ marginBottom: 16 }}>
                  <CheckCircle2 size={16} />
                  <span>
                    <strong>Schedule is already optimal.</strong> The CP-SAT solver confirmed no superior allocation exists under the active constraints. Click &quot;Modify schedule&quot; to manually customize allocations.
                  </span>
                </div>
              )}

              {/* Approval Row (PART 6) */}
              <div className="approval-row">
                <div>
                  <strong>{proposedHasChanges ? 'Ready for your approval' : 'Confirm current schedule'}</strong>
                  <span>
                    {proposalValidation && !proposalValidation.valid ? (
                      <span style={{ color: '#dc2626', fontWeight: 600 }}>
                        Approval disabled: Hard constraint conflicts must be resolved before approval.
                      </span>
                    ) : proposedChangesCount > 0 ? (
                      `${proposedChangesCount} operation${proposedChangesCount === 1 ? '' : 's'} modified. Approving updates the active production schedule across all modules.`
                    ) : (
                      'No operations were moved. Approving confirms the existing baseline plan as active.'
                    )}
                  </span>
                </div>
                <div className="approval-actions">
                  <Button variant="outline" onClick={handleRecalculate} disabled={generating || approving} icon={<RefreshCw size={14} />}>
                    Recalculate
                  </Button>
                  <Button variant="secondary" onClick={handleModifyClick} disabled={generating || approving} icon={<Pencil size={14} />}>
                    Modify schedule
                  </Button>
                  <Button
                    onClick={handleApprove}
                    disabled={isApprovalDisabled}
                    icon={approving ? <RefreshCw className="spin" size={15} /> : <CheckCircle2 size={15} />}
                  >
                    {approving ? 'Approving…' : proposedHasChanges ? 'Approve new schedule' : 'Confirm current schedule'}
                  </Button>
                </div>
              </div>

              {/* Operation Editor Modal */}
              <OperationEditorModal
                task={selectedOperationForEdit}
                onClose={() => setSelectedOperationForEdit(null)}
              />
            </>
          ) : (
            <EmptyState
              icon={Sparkles}
              title={currentState === 'A' ? 'No schedule generated yet' : 'Ready to optimize'}
              description={
                currentState === 'A'
                  ? 'Click "Generate Initial Schedule" to create an initial optimized production plan.'
                  : hasActiveDisruption
                  ? 'Active disruptions detected. Click "Generate Recovery Schedule" to rebalance work around downtime.'
                  : 'Click "Optimize Current Schedule" to evaluate and streamline the current baseline plan.'
              }
            />
          )}
        </Panel>
      </div>
    </div>
  )
}
function ImpactMetric({ label, value, detail, icon: Icon, tone }: { label: string; value: string; detail: string; icon: ComponentType<{ size?: number }>; tone: string }) { return <div className="impact-metric"><div className={`impact-icon ${tone}`}><Icon size={16} /></div><div><strong>{value}</strong><span>{label}</span><small>{detail}</small></div></div> }

export function ComparisonPage() {
  const { originalSchedule, schedule, machines, impactData } = useApp()
  const changed = schedule.filter((task, index) => originalSchedule[index] && (task.machineId !== originalSchedule[index].machineId || task.start !== originalSchedule[index].start)).length
  const recovered = schedule.filter((task) => task.status === 'Rescheduled').length
  return <div className="page-stack"><PageHeader eyebrow="RECOVERY / BEFORE & AFTER" title="Schedule Comparison" subtitle="Understand how production plans changed after a disruption." actions={<Button variant="outline" icon={<Download size={15} />} onClick={() => downloadCsv('schedule-comparison.csv', schedule.map((task) => ({ task: task.id, order: task.orderId, machine: task.machineId, start: task.start, end: task.end, status: task.status })))}>Export comparison</Button>} /><div className="stats-grid four"><StatCard label="Orders recovered" value={String(impactData?.rescheduled_operations_count ?? recovered)} detail="Returned to active planning" icon={ShieldCheck} tone="teal" /><StatCard label="Delayed orders" value={impactData ? String(impactData.delayed_count) : (changed ? '1' : '—')} detail="After recovery" trend={impactData ? `${impactData.on_time_delivery_pct}% on-time` : undefined} icon={TimerReset} tone="blue" /><StatCard label="Makespan change" value={impactData?.makespan_change_hours !== undefined ? `${impactData.makespan_change_hours > 0 ? '+' : ''}${impactData.makespan_change_hours}h` : (changed ? '+1.2h' : '—')} detail="Compared with original" icon={TrendingUp} tone="teal" /><StatCard label="Solver status" value={impactData?.solver_status || 'OPTIMAL'} detail="CP-SAT mathematical solver" icon={Clock3} tone="amber" /></div>{impactData && <div className="comparison-toggle-bar"><MetricChip label="Orig Makespan" value={impactData.original_makespan_hours != null ? `${impactData.original_makespan_hours.toFixed(1)}h` : `\u2014`} /><MetricChip label="Rev Makespan" value={impactData.revised_makespan_hours != null ? `${impactData.revised_makespan_hours.toFixed(1)}h` : `\u2014`} delta={impactData.makespan_change_hours} /><MetricChip label="Reassigned" value={String((impactData as any).reassigned_operations_count ?? impactData.rescheduled_operations_count ?? 0)} /><MetricChip label="Delayed Ops" value={String((impactData as any).delayed_operations_count ?? impactData.delayed_count ?? 0)} /></div>}<div className="comparison-grid"><ComparisonPanel title="Original production schedule" label="BASELINE · INITIAL PLAN" tasks={originalSchedule} machines={machines} tone="original" /><ComparisonPanel title="Rescheduled production plan" label={changed ? 'RECOVERY PLAN · CP-SAT' : 'AWAITING RECOVERY'} tasks={schedule} machines={machines} tone="updated" /></div><Panel title="Change register" eyebrow="WHAT MOVED"><div className="change-list">{schedule.map((task, index) => { const base = originalSchedule[index]; const isChanged = base && (base.machineId !== task.machineId || base.start !== task.start); return <div className="change-row" key={task.id}><div className={`change-state ${isChanged ? 'moved' : 'same'}`}>{isChanged ? <ArrowRight size={14} /> : <CheckCircle2 size={14} />}</div><div><strong>{task.orderId} · {task.product}</strong><span>{isChanged ? `Moved from ${base.machineId} ${base.start}–${base.end} to ${task.machineId} ${task.start}–${task.end}` : `Unchanged · ${task.machineId} ${task.start}–${task.end}`}</span></div><span className="change-label">{isChanged ? 'Rescheduled' : 'Unchanged'}</span></div> })}</div></Panel></div>
}
function ComparisonPanel({ title, label, tasks, machines, tone }: { title: string; label: string; tasks: ScheduleTask[]; machines: Machine[]; tone: string }) { return <Panel title={title} eyebrow={label} className={`comparison-panel ${tone}`}><GanttTimeline tasks={tasks} machines={machines.slice(0, 5)} highlightChanges={tone === 'updated'} /><div className="comparison-summary"><span><i className="legend-block unchanged" /> Unchanged</span><span><i className={`legend-block ${tone === 'updated' ? 'rescheduled' : 'delayed'}`} /> {tone === 'updated' ? 'New assignment' : 'At risk'}</span></div></Panel> }
function MetricChip({ label, value, delta }: { label: string; value: string; delta?: number }) {
  const isWorse = delta != null && delta > 0
  const isBetter = delta != null && delta < 0
  return <div className="comparison-metric-chip"><span>{label}</span><strong>{value}</strong>{delta != null && <small className={isBetter ? 'positive' : isWorse ? 'text-danger' : ''}>{delta > 0 ? '+' : ''}{delta.toFixed(1)}h</small>}</div>
}

export function AnalyticsPage() {
  const [range, setRange] = useState<'today' | 'week' | 'month'>('week')
  const { machines, impactData, analyticsOverview, machineUtilizationData, productionOutputData, orders, disruptions, setAnalyticsRange } = useApp()
  const utilMap: Record<string, number> = (impactData as any)?.machine_utilization ?? {}

  const handleRangeChange = (newRange: 'today' | 'week' | 'month') => {
    setRange(newRange)
    setAnalyticsRange(newRange)
  }

  const chartData = productionOutputData?.data && productionOutputData.data.length > 0
    ? productionOutputData.data
    : productionTrend.map((pt, i) => ({
        date: `2026-11-0${i + 3}`,
        day: pt.day,
        planned_output: pt.output,
        actual_output: pt.output,
        target: pt.target,
        operations_count: 4,
      }))

  const completedOrdersCount = orders.filter((o) => o.status === 'Completed').length
  const remainingOrdersCount = orders.filter((o) => o.status !== 'Completed').length
  const totalOrdersCount = orders.length
  const completionRatePct = totalOrdersCount > 0
    ? Math.round((completedOrdersCount / totalOrdersCount) * 100)
    : 0

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="INSIGHTS / PERFORMANCE SIGNALS"
        title="Production Analytics"
        subtitle="Operational insights driven directly by database schedules and CP-SAT solver results."
        actions={
          <div className="view-toggle compact">
            <button className={range === 'today' ? 'selected' : ''} onClick={() => handleRangeChange('today')}>Today</button>
            <button className={range === 'week' ? 'selected' : ''} onClick={() => handleRangeChange('week')}>Weekly</button>
            <button className={range === 'month' ? 'selected' : ''} onClick={() => handleRangeChange('month')}>Monthly</button>
          </div>
        }
      />
      <div className="analytics-kpis">
        <Kpi
          label="On-time delivery"
          value={`${analyticsOverview?.on_time_delivery_pct ?? (totalOrdersCount > 0 ? Math.round((orders.filter(o => o.status !== 'Delayed').length / totalOrdersCount) * 100) : 100)}%`}
          delta="Grounded schedule data"
          tone="positive"
        />
        <Kpi
          label="Order completion rate"
          value={`${completionRatePct}%`}
          delta={`${completedOrdersCount} of ${totalOrdersCount} orders`}
          tone="positive"
        />
        <Kpi
          label="Avg. scheduled utilization"
          value={`${analyticsOverview?.average_scheduled_utilization_pct ?? 0}%`}
          delta="Across factory assets"
          tone="positive"
        />
        <Kpi
          label="Active disruptions"
          value={String(analyticsOverview?.open_disruptions_count ?? disruptions.filter(d => d.status !== 'Resolved').length)}
          delta={`${disruptions.length} total events`}
          tone={disruptions.some(d => d.status !== 'Resolved') ? "brick" : "positive"}
        />
      </div>

      <div className="analytics-grid">
        <Panel title="Production output trend" eyebrow={`${range.toUpperCase()} / PLANNED UNITS`} className="chart-panel">
          <div className="chart-wrap chart-medium">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 8, left: -22, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#edf0ee" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#78838a', fontSize: 11 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#78838a', fontSize: 11 }} />
                <Tooltip {...chartTooltip} />
                <Line type="monotone" dataKey="planned_output" stroke="#365c55" strokeWidth={2.5} dot={{ r: 3, fill: '#365c55', strokeWidth: 0 }} name="Planned output" />
                <Line type="monotone" dataKey="target" stroke="#a8b8a7" strokeDasharray="4 5" strokeWidth={1.5} dot={false} name="Target" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Scheduled machine utilization" eyebrow="ACTIVE PRODUCTION HORIZON">
          <div className="analytics-bars">
            {machines.map((m) => {
              const utilItem = machineUtilizationData.find((u) => u.machine_id === m.id)
              const util = utilItem ? utilItem.utilization_pct : Math.round(utilMap[m.id] ?? m.utilization ?? 0)
              const isBreakdown = (utilItem?.operational_status === 'Breakdown') || (m.status === 'Breakdown')

              return (
                <div className="analytics-bar-row" key={m.id}>
                  <span title={m.name}>{m.id}</span>
                  <div className="analytics-bar-track">
                    <div style={{ width: `${Math.min(100, util)}%`, background: isBreakdown ? '#c78376' : '#6d8980' }} />
                  </div>
                  <strong className={isBreakdown ? 'text-danger' : ''}>{util}%</strong>
                </div>
              )
            })}
          </div>
        </Panel>

        <Panel title="Completion rate" eyebrow="ACTIVE ORDER BOOK">
          <div className="donut-wrap">
            <ResponsiveContainer width="50%" height={190}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Completed', value: completedOrdersCount || 0 },
                    { name: 'Remaining', value: remainingOrdersCount || (completedOrdersCount === 0 ? 1 : 0) },
                  ]}
                  dataKey="value"
                  innerRadius={60}
                  outerRadius={78}
                  startAngle={90}
                  endAngle={-270}
                  paddingAngle={2}
                >
                  <Cell fill="#365c55" />
                  <Cell fill="#e7ece9" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <strong>{completionRatePct}%</strong>
              <span>completed</span>
            </div>
          </div>
          <div className="analytics-foot-list">
            <span><i className="legend-dot sage" /> Completed <strong>{completedOrdersCount}</strong></span>
            <span><i className="legend-dot grey" /> Remaining <strong>{remainingOrdersCount}</strong></span>
          </div>
        </Panel>

        <Panel title="Disruption category distribution" eyebrow="FACTORY EVENTS">
          <div className="delay-chart">
            <ResponsiveContainer width="100%" height={210}>
              <BarChart
                data={[
                  { name: 'Breakdowns', value: disruptions.filter((d) => d.type === 'Machine Breakdown').length },
                  { name: 'Rush Orders', value: disruptions.filter((d) => d.type === 'Rush Order').length },
                  { name: 'Material Delays', value: disruptions.filter((d) => d.type === 'Material Delay').length },
                ]}
                layout="vertical"
                margin={{ top: 4, right: 8, left: 20, bottom: 0 }}
              >
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: '#78838a', fontSize: 11 }} width={90} />
                <Tooltip {...chartTooltip} />
                <Bar dataKey="value" fill="#6d8980" radius={[0, 4, 4, 0]} barSize={12} name="Events" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  )
}
function Kpi({ label, value, delta, tone }: { label: string; value: string; delta: string; tone: string }) { return <div className="kpi-card"><span>{label}</span><strong>{value}</strong><small className={tone}>{delta}</small></div> }

export function ReportsPage() {
  const [view, setView] = useState<string | null>(null)
  const reports = [{ name: 'Daily Production Report', description: 'Output, line utilization and exceptions for the current production day.', meta: '07 Nov 2026 · PDF / CSV', icon: FileText, accent: 'teal' }, { name: 'Weekly Production Report', description: 'Throughput against target, completion rate and delivery health.', meta: 'Week 45 · PDF / CSV', icon: BarChart3, accent: 'blue' }, { name: 'Monthly Production Report', description: 'Month-to-date production output and capacity trends.', meta: 'November 2026 · PDF / CSV', icon: TrendingUp, accent: 'amber' }, { name: 'Machine Performance Report', description: 'Utilization, downtime and current task assignment by machine.', meta: 'Current shift · CSV', icon: Wrench, accent: 'brick' }, { name: 'Disruption Recovery Report', description: 'Events, affected orders, recovery time and schedule outcomes.', meta: 'Last 30 days · PDF / CSV', icon: RefreshCw, accent: 'teal' }]
  return <div className="page-stack"><PageHeader eyebrow="OPERATIONS / DOCUMENTS" title="Production Reports" subtitle="Turn operational data into a clear shift handoff." actions={<Button variant="outline" icon={<Printer size={15} />} onClick={() => window.print()}>Print report</Button>} /><div className="report-grid">{reports.map((report) => <div className="report-card" key={report.name}><div className={`report-icon ${report.accent}`}><report.icon size={19} /></div><div className="eyebrow">{report.meta}</div><h3>{report.name}</h3><p>{report.description}</p><div className="report-actions"><Button variant="quiet" onClick={() => setView(report.name)}>View report</Button><button className="download-button" onClick={() => downloadCsv(`${report.name.toLowerCase().replaceAll(' ', '-')}.csv`, [{ report: report.name, generated: '07 Nov 2026', status: 'Ready' }])}><Download size={14} /> CSV</button></div></div>)}</div><Panel title="Export history" eyebrow="RECENTLY GENERATED"><div className="export-history"><div><div className="export-file"><FileDown size={15} /></div><div><strong>weekly-production-report.csv</strong><span>Generated today at 09:22 · 18 KB</span></div></div><StatusBadge value="Completed" /><button className="icon-btn"><MoreHorizontal size={16} /></button></div><div className="export-history"><div><div className="export-file"><FileDown size={15} /></div><div><strong>machine-performance-report.csv</strong><span>Generated yesterday at 17:40 · 12 KB</span></div></div><StatusBadge value="Completed" /><button className="icon-btn"><MoreHorizontal size={16} /></button></div></Panel><Modal open={!!view} onClose={() => setView(null)} title={view ?? ''} subtitle="Preview before export"><div className="report-preview"><div className="report-preview-header"><div><div className="eyebrow">NORTHSTAR COMPONENTS</div><h3>{view}</h3></div><Badge tone="success">Ready</Badge></div><div className="report-preview-stats"><Detail label="Production output" value="13,395 units" /><Detail label="On-time delivery" value="92.4%" /><Detail label="Open disruptions" value="2" /><Detail label="Capacity used" value="76%" /></div><div className="report-preview-lines"><span /><span /><span /><span /><span /></div></div><div className="modal-actions"><Button variant="outline" onClick={() => setView(null)}>Close</Button><Button icon={<Download size={14} />} onClick={() => downloadCsv(`${view?.toLowerCase().replaceAll(' ', '-')}.csv`, [{ report: view, generated: '07 Nov 2026', output: 13395, onTime: '92.4%' }])}>Export CSV</Button></div></Modal></div>
}

export function SettingsPage() {
  const { settings, updateSettings } = useApp()
  const [form, setForm] = useState<FactorySettings>(settings)
  return <div className="page-stack"><PageHeader eyebrow="ADMINISTRATION / WORKSPACE CONFIGURATION" title="Factory Settings" subtitle="Keep the workspace aligned with the way your factory runs." actions={<Button icon={<CheckCircle2 size={15} />} onClick={() => updateSettings(form)}>Save changes</Button>} /><div className="settings-grid"><div className="settings-nav"><div className="settings-nav-title">Configuration</div>{['Factory information', 'Working hours', 'Machine configuration', 'Production preferences', 'Notification preferences', 'User profile'].map((item, index) => <button className={index === 0 ? 'active' : ''} key={item}>{item}<ChevronRight size={14} /></button>)}</div><div className="settings-main"><Panel title="Factory information" eyebrow="WORKSPACE IDENTITY"><div className="form-grid"><TextField label="Factory name" value={form.factoryName} onChange={(value) => setForm({ ...form, factoryName: value })} /><TextField label="Location" value={form.location} onChange={(value) => setForm({ ...form, location: value })} /><SelectField label="Timezone" value={form.timezone} onChange={(value) => setForm({ ...form, timezone: value })} options={['Asia/Kolkata (UTC+05:30)', 'Asia/Singapore (UTC+08:00)', 'Europe/Berlin (UTC+01:00)']} /><TextField label="Factory code" value="NSC-PL01" onChange={() => undefined} /></div></Panel><Panel title="Working hours" eyebrow="SHIFT PATTERN"><div className="form-grid"><TextField label="Daily operating hours" value={form.workingHours} onChange={(value) => setForm({ ...form, workingHours: value })} /><SelectField label="Shift pattern" value={form.shiftPattern} onChange={(value) => setForm({ ...form, shiftPattern: value })} options={['2 shifts · 8 hours', '3 shifts · 8 hours', '1 shift · 10 hours']} /><TextField label="Overtime limit" value={form.overtimeLimit} onChange={(value) => setForm({ ...form, overtimeLimit: value })} /></div></Panel><Panel title="Production preferences" eyebrow="PLANNING BEHAVIOUR"><Toggle label="Auto-reschedule after a disruption" hint="Prepare a recommended plan automatically" checked={form.autoReschedule} onChange={(checked) => setForm({ ...form, autoReschedule: checked })} /><Toggle label="Use machine idle time first" hint="Prefer available capacity before overtime" checked={true} onChange={() => undefined} /><Toggle label="Protect high-priority deadlines" hint="Prioritize customer commitments over throughput" checked={true} onChange={() => undefined} /></Panel><Panel title="Notification preferences" eyebrow="ALERT DELIVERY"><Toggle label="Disruption alerts" hint="Notify when a production event is reported" checked={form.disruptionAlerts} onChange={(checked) => setForm({ ...form, disruptionAlerts: checked })} /><Toggle label="Email alerts" hint="Send daily exception summaries to the plant manager" checked={form.emailAlerts} onChange={(checked) => setForm({ ...form, emailAlerts: checked })} /><Toggle label="Weekly digest" hint="Receive a Monday performance snapshot" checked={form.weeklyDigest} onChange={(checked) => setForm({ ...form, weeklyDigest: checked })} /></Panel><Panel title="User profile" eyebrow="ACCOUNT OWNER"><div className="profile-banner"><div className="avatar avatar-large">AM</div><div><strong>{form.managerName}</strong><span>{form.managerRole}</span></div><Button variant="outline" icon={<UserRound size={14} />}>Edit profile</Button></div></Panel></div></div></div>
}

function downloadCsv(filename: string, rows: Record<string, unknown>[]) { const keys = Object.keys(rows[0] ?? {}); const csv = [keys.join(','), ...rows.map((row) => keys.map((key) => JSON.stringify(row[key] ?? '')).join(','))].join('\n'); const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = filename; link.click(); URL.revokeObjectURL(link.href) }
