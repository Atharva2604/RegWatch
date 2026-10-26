import React from 'react';
import { Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { api } from '../../lib/api';

export const AppLayout: React.FC = () => {
  // Query open alerts count
  const { data: alertsData } = useQuery({
    queryKey: ['alerts', 'count'],
    queryFn: () => api.getAlerts(undefined, 'open'),
    refetchInterval: 30000,
  });

  const openCount = alertsData?.count || 0;

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 flex flex-col">
      <Navbar openAlertsCount={openCount} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar openAlertsCount={openCount} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
