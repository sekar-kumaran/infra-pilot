import { fetchApi } from './client';

export interface WorkerNode {
  id: string;
  worker_id: string;
  hostname: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  active_tasks: number;
  queue: string;
  concurrency: number;
  version?: string;
  last_heartbeat?: string;
  started_at?: string;
}

export interface QueueStat {
  queue_name: string;
  pending_tasks: number;
  active_tasks: number;
  reserved_tasks: number;
  worker_count: number;
  healthy_worker_count: number;
  unhealthy_worker_count: number;
}

export interface SystemHealth {
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  workers: {
    total: number;
    online: number;
    degraded: number;
    offline: number;
  };
}

export const operationsApi = {
  getWorkers: () => fetchApi<WorkerNode[]>('/operations/workers'),
  getWorker: (id: string) => fetchApi<WorkerNode>(`/operations/workers/${id}`),
  getQueues: () => fetchApi<QueueStat[]>('/operations/queues'),
  getHealth: () => fetchApi<SystemHealth>('/operations/health'),
};
