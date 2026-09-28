"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import {
  LayoutDashboard,
  Server,
  Plug,
  Activity,
  BellRing,
  AlertTriangle,
  PlaySquare,
  ShieldCheck,
  FileText,
  LogOut,
  Menu,
  X,
  Zap,
  Box
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/sonner';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  permission?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: 'Overview',
    items: [
      { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    ]
  },
  {
    title: 'My Applications',
    items: [
      { name: 'All Applications', href: '/applications', icon: Box, permission: 'resources:read' },
    ]
  },
  {
    title: 'Infrastructure',
    items: [
      { name: 'Resources', href: '/infrastructure/resources', icon: Server, permission: 'resources:read' },
      { name: 'Environments', href: '/infrastructure/environments', icon: Box, permission: 'resources:read' },
      { name: 'Topology Map', href: '/infrastructure/topology', icon: Activity, permission: 'resources:read' },
    ]
  },
  {
    title: 'Observability',
    items: [
      { name: 'Live Feed', href: '/observability/live', icon: Activity, permission: 'events:read' },
      { name: 'Incidents', href: '/incidents', icon: AlertTriangle, permission: 'incidents:read' },
      { name: 'Alerts', href: '/alerts', icon: BellRing, permission: 'alerts:read' },
      { name: 'Logs Explorer', href: '/observability/logs', icon: FileText, permission: 'events:read' },
    ]
  },
  {
    title: 'Automation',
    items: [
      { name: 'Workflows', href: '/automation/workflows', icon: PlaySquare, permission: 'automation:read' },
      { name: 'Run History', href: '/automation/executions', icon: Activity, permission: 'automation:read' },
      { name: 'Approvals', href: '/automation/approvals', icon: ShieldCheck, permission: 'automation:read' },
      { name: 'Scheduler', href: '/automation/scheduler', icon: Zap, permission: 'automation:read' },
    ]
  },
  {
    title: 'Governance',
    items: [
      { name: 'Policies', href: '/policies', icon: ShieldCheck, permission: 'policies:read' },
      { name: 'Compliance Checks', href: '/governance/compliance', icon: ShieldCheck, permission: 'policies:read' },
      { name: 'Audit Trail', href: '/audit', icon: FileText, permission: 'security:read' },
    ]
  },
  {
    title: 'Settings',
    items: [
      { name: 'Integrations', href: '/integrations', icon: Plug, permission: 'integrations:read' },
      { name: 'Users & Roles', href: '/settings/users', icon: Server, permission: 'admin_only' },
      { name: 'Notifications', href: '/settings/notifications', icon: BellRing, permission: 'integrations:read' },
    ]
  }
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, hasPermission } = useAuth();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between bg-slate-900 text-white p-4">
        <span className="text-xl font-bold">InfraPilot</span>
        <button onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar */}
      <div className={cn(
        "w-64 bg-slate-900 text-slate-300 flex-col h-screen sticky top-0 transition-transform duration-300 md:flex",
        sidebarOpen ? "fixed z-50 flex inset-y-0 left-0" : "hidden"
      )}>
        <div className="p-6">
          <Link href="/dashboard">
            <h1 className="text-2xl font-bold text-white tracking-tight">InfraPilot</h1>
          </Link>
        </div>

        <nav className="flex-1 px-4 space-y-6 overflow-y-auto pb-6">
          {navSections.map((section) => {
            const filteredItems = section.items.filter(item => !item.permission || hasPermission(item.permission));
            if (filteredItems.length === 0) return null;
            
            return (
              <div key={section.title} className="space-y-1">
                <h3 className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  {section.title}
                </h3>
                {filteredItems.map((item) => {
                  const isActive = pathname.startsWith(item.href) && (item.href !== '/dashboard' || pathname === '/dashboard');
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-sm",
                        isActive ? "bg-indigo-600 text-white font-medium" : "hover:bg-slate-800 hover:text-white"
                      )}
                      onClick={() => setSidebarOpen(false)}
                    >
                      <item.icon size={18} />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="mb-4 px-3">
            <p className="text-sm text-slate-400 truncate">{user?.email}</p>
            <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
          </div>
          <Button variant="ghost" className="w-full justify-start text-slate-300 hover:text-white hover:bg-slate-800" onClick={logout}>
            <LogOut size={20} className="mr-3" />
            Sign out
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen max-w-full overflow-hidden">
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          {children}
        </main>
      </div>
      
      <Toaster />
    </div>
  );
}
