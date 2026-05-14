import { Routes, Route, Navigate } from 'react-router-dom'
import PublicLayout from './layouts/PublicLayout.jsx'
import AppLayout from './layouts/AppLayout.jsx'
import AuthLayout from './layouts/AuthLayout.jsx'
import RequireAuth from './components/RequireAuth.jsx'

// Public
import Home from './pages/public/Home.jsx'
import Explore from './pages/public/Explore.jsx'
import PublicProjectDetail from './pages/public/PublicProjectDetail.jsx'
import ARViewer from './pages/public/ARViewer.jsx'

// Auth
import Login from './pages/auth/Login.jsx'
import Register from './pages/auth/Register.jsx'
import VerifyEmail from './pages/auth/VerifyEmail.jsx'
import ForgotPassword from './pages/auth/ForgotPassword.jsx'
import SocialCallback from './pages/auth/SocialCallback.jsx'

// User
import Dashboard from './pages/app/Dashboard.jsx'
import Profile from './pages/app/Profile.jsx'

// Collaborative
import ProjectsList from './pages/app/ProjectsList.jsx'
import ProjectCreate from './pages/app/ProjectCreate.jsx'
import ProjectWorkspace from './pages/app/ProjectWorkspace.jsx'
import Conflicts from './pages/app/Conflicts.jsx'
import AdvancedSearch from './pages/app/AdvancedSearch.jsx'

// AI
import Chatbot from './pages/app/Chatbot.jsx'
import AutoAnnotation from './pages/app/AutoAnnotation.jsx'

// Tools
import ExportCenter from './pages/app/ExportCenter.jsx'
import Notifications from './pages/app/Notifications.jsx'

// Admin
import AdminUsers from './pages/admin/AdminUsers.jsx'
import AdminProjects from './pages/admin/AdminProjects.jsx'
import AdminStats from './pages/admin/AdminStats.jsx'

import NotFound from './pages/NotFound.jsx'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route element={<PublicLayout />}>
        <Route index element={<Home />} />
        <Route path="explorer" element={<Explore />} />
        <Route path="projets-publics/:id" element={<PublicProjectDetail />} />
      </Route>

      {/* Auth */}
      <Route element={<AuthLayout />}>
        <Route path="connexion" element={<Login />} />
        <Route path="inscription" element={<Register />} />
        <Route path="verification-email" element={<VerifyEmail />} />
        <Route path="mot-de-passe-oublie" element={<ForgotPassword />} />
        {/* OAuth provider redirects land here with ?code=... */}
        <Route path="auth/:provider/callback" element={<SocialCallback />} />
      </Route>

      {/* App (auth required) */}
      <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
        <Route path="app" element={<Navigate to="/app/tableau-de-bord" replace />} />
        <Route path="app/tableau-de-bord" element={<Dashboard />} />
        <Route path="app/profil" element={<Profile />} />

        <Route path="app/projets" element={<ProjectsList />} />
        <Route path="app/projets/nouveau" element={<ProjectCreate />} />
        <Route path="app/projets/:id" element={<ProjectWorkspace />} />
        <Route path="app/projets/:id/conflits" element={<Conflicts />} />

        <Route path="app/recherche" element={<AdvancedSearch />} />

        <Route path="app/chatbot" element={<Chatbot />} />
        <Route path="app/annotation-auto" element={<AutoAnnotation />} />

        <Route path="app/export" element={<ExportCenter />} />
        <Route path="app/notifications" element={<Notifications />} />

        {/* Admin */}
        <Route path="app/admin/utilisateurs" element={<AdminUsers />} />
        <Route path="app/admin/projets" element={<AdminProjects />} />
        <Route path="app/admin/statistiques" element={<AdminStats />} />
      </Route>

      {/* Public AR viewer — full-screen, no layout, opened via QR scan */}
      <Route path="ar/model/:id" element={<ARViewer />} />

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
