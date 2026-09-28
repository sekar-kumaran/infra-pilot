"use client";

import { useState } from 'react';
import useSWR from 'swr';
import { fetchApi } from '@/lib/api/client';
import { useAuth } from '@/lib/auth';
import { toast } from 'sonner';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from "@/components/ui/badge";
import { Users, Plus, Shield, Mail, MoreHorizontal, AlertTriangle, RefreshCw } from "lucide-react";

export default function UsersAndRolesPage() {
  const { user } = useAuth();
  const [showInvite, setShowInvite] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  const { data: usersData, error, isLoading, mutate } = useSWR('/users', () => fetchApi<{ items: any[]; total: number }>('/users'));

  const users = usersData?.items || [];
  const totalUsers = usersData?.total || 0;
  
  const handleCreateViewer = async () => {
    try {
      await fetchApi('/users', {
        method: 'POST',
        body: JSON.stringify({ email: newEmail, password: newPassword })
      });
      toast.success('Viewer user created successfully');
      setShowInvite(false);
      setNewEmail('');
      setNewPassword('');
      mutate();
    } catch (e: any) {
      toast.error(e.message || 'Failed to create user');
    }
  };

  if (user?.role?.toLowerCase() !== 'admin') {
    return <div className="p-12 text-center text-red-500 font-medium">Access Denied. Admins only.</div>;
  }
  
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Users & Roles</h1>
          <p className="text-muted-foreground mt-1">Manage tenant members and role-based access control (RBAC).</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Shield className="w-4 h-4 mr-2" /> Manage Roles</Button>
          <Button className="bg-indigo-600 hover:bg-indigo-700" onClick={() => setShowInvite(!showInvite)}>
            <Plus className="w-4 h-4 mr-2" /> Create Viewer
          </Button>
        </div>
      </div>

      {showInvite && (
        <Card className="mb-6 p-4">
          <CardHeader className="px-0 pt-0">
            <CardTitle className="text-lg">Create Viewer User</CardTitle>
          </CardHeader>
          <div className="flex gap-4 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Email</label>
              <input type="email" value={newEmail} onChange={e => setNewEmail(e.target.value)} className="flex h-10 w-full rounded-md border border-slate-300 bg-transparent px-3 py-2 text-sm" placeholder="viewer@example.com" />
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Password</label>
              <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className="flex h-10 w-full rounded-md border border-slate-300 bg-transparent px-3 py-2 text-sm" placeholder="SecretPassword123" />
            </div>
            <Button onClick={handleCreateViewer} className="bg-emerald-600 hover:bg-emerald-700">Submit</Button>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <RefreshCw className="h-4 w-4 animate-spin text-slate-400" />
            ) : (
              <div className="text-2xl font-bold">{totalUsers}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-sm">
        {error ? (
          <div className="p-8">
            <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-md">
              <h3 className="font-bold flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Failed to load users</h3>
              <p className="font-mono text-sm mt-2">API: /api/v1/users</p>
              <p className="text-sm mt-1">Reason: {error.message}</p>
            </div>
          </div>
        ) : isLoading ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center">
            <RefreshCw className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
            Loading users...
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-slate-50 dark:bg-slate-900/50">
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Active</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-slate-500">No users found.</TableCell>
                </TableRow>
              ) : users.map((user: any) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs uppercase">
                        {user.name ? user.name.substring(0,2) : (user.email ? user.email.substring(0,2) : 'U')}
                      </div>
                      <div>
                        <div className="font-medium">{user.name || 'Unnamed User'}</div>
                        <div className="text-xs text-slate-500 flex items-center gap-1"><Mail className="w-3 h-3" /> {user.email}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="bg-slate-50 dark:bg-slate-800">{user.role || 'User'}</Badge>
                  </TableCell>
                  <TableCell>
                    {user.status === 'Active' ? (
                      <Badge className="bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 shadow-none border-0">Active</Badge>
                    ) : (
                      <Badge className="bg-amber-500/10 text-amber-600 hover:bg-amber-500/20 shadow-none border-0">{user.status || 'Invited'}</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-slate-500 text-sm">{user.lastActive || 'Never'}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" className="text-slate-400 hover:text-slate-700">
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
