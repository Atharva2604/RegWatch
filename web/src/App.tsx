import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { BaselineAudit } from './pages/BaselineAudit';
import { Regulations } from './pages/Regulations';
import { Policies } from './pages/Policies';
import { ProposeChange } from './pages/ProposeChange';
import { Checks } from './pages/Checks';
import { Alerts } from './pages/Alerts';
import { Explain } from './pages/Explain';
import { Events } from './pages/Events';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 30, // 30 seconds
      retry: 1,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="baseline-audit" element={<BaselineAudit />} />
            <Route path="regulations" element={<Regulations />} />
            <Route path="policies" element={<Policies />} />
            <Route path="propose-change" element={<ProposeChange />} />
            <Route path="checks" element={<Checks />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="explain/:id" element={<Explain />} />
            <Route path="events" element={<Events />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
