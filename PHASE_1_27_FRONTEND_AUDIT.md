# PHASE_1_27_FRONTEND_AUDIT

## Frontend Routes

### Existing
- `/dashboard` - (Uses mock data partly? Needs audit of `metricsApi`)
- `/alerts` 
- `/audit`
- `/automation/approvals` 
- `/automation/executions`
- `/automation/playbooks` (Equivalent to workflows)
- `/automation/providers`
- `/events`
- `/incidents`
- `/incidents/[id]`
- `/infrastructure/environments`
- `/infrastructure/resources`
- `/infrastructure/resources/[id]`
- `/integrations`
- `/operations/workers`
- `/policies`
- `/policies/simulator`

### Missing
- `/infrastructure/graph`
- `/automation/actions`
- `/automation/workflows` (if not aliasing playbooks)
- `/automation/workflows/[id]`
- `/operations/queues`
- `/operations/circuit-breakers`
- `/operations/dead-letter`
- `/settings`
- `/settings/tenants`
- `/settings/users`

## API Clients

### Existing
- `alerts.ts`
- `audit.ts`
- `auth.ts`
- `automation.ts`
- `client.ts`
- `environments.ts`
- `events.ts`
- `incidents.ts`
- `integrations.ts`
- `metrics.ts`
- `policies.ts`
- `resources.ts`

### Missing
- `workers.ts` / `operations.ts`
- `search.ts`

## Known Issues

- **Hardcoded Data**: Needs verification, but likely many list pages (like Executions, Incidents) are not connected to robust backend endpoints or are swallowing errors.
- **Empty/Error States**: Missing consistent skeletons and error boundary implementations.
- **Real-Time Polling**: Using `useSWR` but intervals might be incorrect or missing.
- **Tenant Context**: Top nav might be missing a tenant selector.

## Next Steps

1. Create missing API client endpoints (`operations.ts`, `search.ts`).
2. Scaffold missing routes (`/operations/dead-letter`, `/operations/circuit-breakers`, `/automation/workflows/[id]`).
3. Refactor all list/detail components to strictly use `lib/api/` clients and handle 404/500 properly.
4. Enhance Dashboard to use real metrics logic in the backend.
5. Create the local DevOps lab (Docker Compose with Prometheus, Grafana, App).
