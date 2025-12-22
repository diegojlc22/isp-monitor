import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import 'leaflet/dist/leaflet.css';
import { DashboardLayout } from './layouts/DashboardLayout'
import { Dashboard } from './pages/Dashboard'
import { Towers } from './pages/Towers'
import { Equipments } from './pages/Equipments'
import { Settings } from './pages/Settings'
import { NetMap } from './pages/NetMap'
import { Login } from './pages/Login'
import { ManageUsers } from './pages/ManageUsers'
import { Profile } from './pages/Profile'
import { Alerts } from './pages/Alerts'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="map" element={<NetMap />} />
              <Route path="towers" element={<Towers />} />
              <Route path="equipments" element={<Equipments />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="profile" element={<Profile />} />

              {/* Admin Routes */}
              <Route element={<AdminRoute />}>
                <Route path="settings" element={<Settings />} />
                <Route path="users" element={<ManageUsers />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)
