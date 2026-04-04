import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { useWebSocket } from './hooks/useWebSocket';

import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import DatabaseView from './pages/DatabaseView';
import CRUDView from './pages/CRUDView';
import SearchView from './pages/SearchView';
import AnalyticsView from './pages/AnalyticsView';

function App() {
  // Initialize WebSocket connection
  useWebSocket();

  return (
    <BrowserRouter>
      <Toaster position="top-right" richColors closeButton />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="database" element={<DatabaseView />} />
          <Route path="crud" element={<CRUDView />} />
          <Route path="search" element={<SearchView />} />
          <Route path="analytics" element={<AnalyticsView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
