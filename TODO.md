# ReSchedule delivery outcomes

## Shared industrial SaaS shell
- Build a responsive desktop-first dashboard layout with a fixed dark charcoal sidebar, ReSchedule mark and “Production Intelligence” subtitle; include Overview, Production Schedule, Orders, Machines, Disruptions, Rescheduling, Analytics, Reports and Settings navigation with active state, hover state and collapsible behavior.
- Include a clean top bar with current page title, breadcrumbs, search, notifications, current date and user avatar; use the required muted industrial palette, Inter-like typography, consistent spacing, buttons, borders and status colors.
- Persist frontend mock data using localStorage and surface toast notifications, loading states, confirmation dialogs and meaningful empty states.

## Login and Overview
- Provide a split-screen simulated login with ReSchedule branding, “Keep Production Moving.” tagline, email/password, remember-me and demo-login flow that navigates to the dashboard without implementing real authentication.
- Build Production Overview with the four requested statistics, weekly Recharts production output, machine status, recent orders, recent activity and functional Add New Order, Report Disruption and Generate Schedule quick actions.

## Production planning and recovery
- Build a daily/weekly Production Schedule with date navigation, machine/order filters, machine-wise Gantt timeline, production task blocks, status coloring, task detail modal and a Generate Schedule action that changes the mock schedule.
- Build Disruption Center with Machine Breakdown, Rush Order and Material Delay cards; each opens a validated relevant form modal, updates disruption history and affected machine/order state, notifies the user and offers impact analysis.
- Build Smart Rescheduling with disruption summary, impact analysis, four optimization toggles, simulated loading/analysis, an actually changed recommended schedule, explanation and Approve New Schedule, Modify Schedule and Recalculate actions.
- Build Schedule Comparison with original and rescheduled plans side by side, visual distinctions for unchanged/rescheduled/delayed/newly assigned tasks and statistics calculated from the mock schedules; approval updates the active schedule across the app while retaining the original snapshot.

## Operations management
- Build Order Management with total/pending/completed/urgent stats, searchable/filterable table, priority and status labels, validated add/edit/view/delete modals, and fields for product, quantity, dates, priority, machine and estimated production time.
- Build Machine Management with total/available/running/maintenance stats, machine cards, ID/type/capacity/utilization/status/task details, subtle progress bars, add/edit/view flows and status changes.

## Analytics, reports and settings
- Build Production Analytics with muted Recharts for output trend, utilization, completion rate, on-time delivery, disruption frequency, recovery time and delay analysis, plus weekly/monthly/date controls.
- Build Production Reports for daily, weekly, monthly, machine performance and disruption recovery with View Report, frontend-generated CSV export and Print Report actions.
- Build Factory Settings with editable factory information, working hours, machine configuration, production preferences, notification preferences and user profile; save changes through shared frontend state.

## Delivery quality
- Ensure every navigation item works, every page loads without placeholder-only content, forms validate, modals open and close, searching/filtering works, changes persist after refresh, disruption reporting and rescheduling propagate to related pages, exports work, routes have no horizontal overflow, and the application builds without TypeScript or console errors.
