import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import 'leaflet/dist/leaflet.css';
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute'
import { Toaster } from 'react-hot-toast';

// --- Layouts (Eager Load) ---
import { DashboardLayout } from './layouts/DashboardLayout'
import { Login } from './pages/Login' // Login deve abrir rapido

// --- Pages (Lazy Load) ---
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Towers = lazy(() => import('./pages/Towers').then(m => ({ default: m.Towers })));
const Equipments = lazy(() => import('./pages/Equipments').then(m => ({ default: m.Equipments })));
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const NetMap = lazy(() => import('./pages/NetMap').then(m => ({ default: m.NetMap })));
const ManageUsers = lazy(() => import('./pages/ManageUsers').then(m => ({ default: m.ManageUsers })));
const Profile = lazy(() => import('./pages/Profile').then(m => ({ default: m.Profile })));
const Alerts = lazy(() => import('./pages/Alerts').then(m => ({ default: m.Alerts })));
const Backup = lazy(() => import('./pages/Backup').then(m => ({ default: m.Backup })));
const LiveMonitor = lazy(() => import('./pages/LiveMonitor').then(m => ({ default: m.LiveMonitor })));
const Agent = lazy(() => import('./pages/Agent'));
const Health = lazy(() => import('./pages/Health').then(m => ({ default: m.Health })));

const RequestsPage = lazy(() => import('./pages/RequestsPage'));
const MobileApp = lazy(() => import('./pages/MobileApp').then(m => ({ default: m.MobileApp })));
const Reports = lazy(() => import('./pages/Reports'));
const Schedules = lazy(() => import('./pages/Schedules').then(m => ({ default: m.Schedules })));

// Loading Component
const PageLoader = () => (
  <div className="h-full w-full flex items-center justify-center bg-slate-950 text-slate-500">
    <div className="animate-pulse flex flex-col items-center gap-2">
      <div className="h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <span className="text-sm font-medium">Carregando...</span>
    </div>
  </div>
);

import { ScannerProvider } from './contexts/ScannerContext'



createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <ScannerProvider>
        <BrowserRouter>
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: '#0f172a',
                color: '#fff',
                border: '1px solid #1e293b',
              },
            }}
          />
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/login" element={<Login />} />

              <Route path="/" element={<ProtectedRoute />}>
                <Route element={<DashboardLayout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="live" element={<LiveMonitor />} />
                  <Route path="map" element={<NetMap />} />
                  <Route path="towers" element={<Towers />} />
                  <Route path="equipments" element={<Equipments />} />
                  <Route path="alerts" element={<Alerts />} />
                  <Route path="profile" element={<Profile />} />
                  <Route path="agent" element={<Agent />} />
                  <Route path="reports" element={<Reports />} />
                  <Route path="health" element={<Health />} />

                  {/* Admin Routes */}
                  <Route element={<AdminRoute />}>
                    <Route path="requests" element={<RequestsPage />} />
                    <Route path="mobile" element={<MobileApp />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="schedules" element={<Schedules />} />
                    <Route path="users" element={<ManageUsers />} />
                    <Route path="backup" element={<Backup />} />
                  </Route>
                </Route>
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ScannerProvider>
    </AuthProvider>
  </StrictMode>,
)
