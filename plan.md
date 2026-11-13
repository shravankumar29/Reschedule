# ReSchedule implementation plan

## Scope and approach

ReSchedule is a frontend-only industrial SaaS prototype for Innovasia 2026. It uses a Vite + React + TypeScript application with React Router, Recharts, Framer Motion, and Lucide React. There is no backend, authentication service, database, or real optimization engine; the login and schedule generation flows are simulated with realistic mock data.

The product is organized around one localStorage-backed `AppContext`. Orders, machines, disruptions, active schedule, original schedule snapshot, notifications, settings, and UI loading state live in shared state so actions on one page visibly affect other pages. Route pages remain presentation-focused and use reusable primitives for layout, stats, badges, tables, modals, timeline bars, and charts.

## Design direction

**Alternative styles:** Swiss industrial operations console (0.06); quiet enterprise atelier (0.07); field-ready control room (0.05).

### Chosen movement: quiet enterprise atelier

- **Core principles:** Calm operational density; clear hierarchy over decoration; every status has a useful next action; disruption recovery should feel controlled and explainable.
- **Color philosophy:** Charcoal anchors the persistent navigation, warm off-white keeps long sessions comfortable, and sage/teal accents communicate operational confidence without looking like an AI toy. Amber and brick appear only at decision points.
- **Layout paradigm:** A fixed command rail plus a wide workbench: pages open with a compact page header, then arrange primary content in asymmetric workbench panels rather than a wall of identical cards.
- **Signature elements:** Thin timeline rails, uppercase micro-labels with generous tracking, and small “system state” indicators that make the factory feel observable and live.
- **Interaction philosophy:** Prefer inline edits, focused modals, and toast feedback. Actions should change shared data immediately and narrate the consequence.
- **Animation:** Use short opacity/translate transitions for route content, a subtle shimmer/progress treatment during schedule generation, and no decorative motion.
- **Typography system:** Inter (or a system fallback) for all interface text. Compact semibold headings, 12px uppercase labels, and tabular numerals for operational metrics.
- **Brand essence:** The calm control layer for small manufacturers keeping commitments intact; precise, reassuring, practical.
- **Brand voice:** Headlines are direct and operational. CTAs explain the next move. Example lines: “Keep the line moving.” “Recover the plan before the deadline moves.”
- **Wordmark & logo:** A compact six-node routing mark next to the ReSchedule wordmark, suggesting work moving through alternate machine paths.
- **Signature brand color:** Deep production teal `#365C55`.

## Project structure

- `src/context/AppContext.tsx`: shared state, localStorage persistence, CRUD actions, schedule recovery simulation and toast notifications.
- `src/data/mockData.ts`: seed orders, machines, schedules, disruptions and analytics data.
- `src/components/`: layout shell, navigation, reusable cards, badges, modals, tables, charts and timeline visualizations.
- `src/pages/`: login, overview, schedule, orders, machines, disruptions, rescheduling, comparison, analytics, reports and settings screens.
- `src/App.tsx`: route map and authenticated shell.
- `src/styles.css`: industrial SaaS visual system and responsive behavior.
- `public/manus-routes.json`: complete page route manifest for preview and publication.

## Build workflow

Install the pinned dependencies, run Vite on port 3000, verify the route manifest and app build, resolve TypeScript diagnostics, then commit the working frontend to the managed repository. The project is static/frontend-only and does not require managed server or database capabilities.
