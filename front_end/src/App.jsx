import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import DatabaseView from './pages/DatabaseView';
import CRUDView from './pages/CRUDView';
import SearchView from './pages/SearchView';
import AnalyticsView from './pages/AnalyticsView';

function App() {
  return (
    <BrowserRouter>
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
