"use client";

import useSWR from 'swr';
import { eventsApi } from '@/lib/api/events';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RefreshCcw } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';

export default function EventsPage() {
  const { data: events, error, isLoading } = useSWR('/events', () => eventsApi.list());
  const { hasPermission } = useAuth();

  const handleReprocess = async (id: string) => {
    if (!confirm('Are you sure you want to reprocess this event?')) return;
    try {
      const res = await eventsApi.reprocess(id);
      toast.success(`Reprocessing Job Started: ${res.job_id}`);
    } catch (err: any) {
      toast.error(`Reprocess failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Events</h1>
      </div>

      <div className="border rounded-md bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Event ID</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Event Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Received At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">Loading events...</TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-red-500">Failed to load events.</TableCell>
              </TableRow>
            ) : events?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-500 py-8">No events found.</TableCell>
              </TableRow>
            ) : (
              events?.map((event) => (
                <TableRow key={event.id}>
                  <TableCell className="font-mono text-xs max-w-[120px] truncate" title={event.id}>
                    {event.id}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{event.provider}</Badge>
                  </TableCell>
                  <TableCell>{event.event_type}</TableCell>
                  <TableCell>
                    <Badge variant={event.processing_status === 'processed' ? 'default' : (event.processing_status === 'failed' ? 'destructive' : 'secondary')}>
                      {event.processing_status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-500">{new Date(event.received_at).toLocaleString()}</TableCell>
                  <TableCell className="text-right">
                    {hasPermission('events:ingest') && event.processing_status === 'failed' && (
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleReprocess(event.id)}
                        title="Reprocess Event"
                      >
                        <RefreshCcw className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
