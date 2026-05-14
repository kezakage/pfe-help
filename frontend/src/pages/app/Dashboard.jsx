import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FolderKanban, AlertTriangle, CheckCircle2, Activity, Sparkles,
  Users as UsersIcon, FileCheck2, BarChart3, ArrowRight, Bell
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext.jsx'
import { useNotifications } from '../../context/NotificationsContext.jsx'
import { heritage, adminApi } from '../../lib/api.js'
import { projectToCard } from '../../data/projects.js'
import StatusBadge from '../../components/StatusBadge.jsx'

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg grid place-items-center bg-terracotta-50 text-terracotta-700">
          <Icon size={20}/>
        </div>
        <div>
          <div className="text-2xl font-semibold">{value}</div>
          <div className="text-xs text-sand-500 uppercase tracking-widest">{label}</div>
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { items: notifs } = useNotifications()
  const isAdmin = user.role === 'admin'

  if (isAdmin) return <AdminDashboard notifs={notifs}/>
  return <ExpertDashboard user={user} notifs={notifs}/>
}

function ExpertDashboard({ user, notifs }) {
  const { t } = useTranslation()
  const [myProjects, setMyProjects] = useState([])
  const [stats, setStats] = useState({ total: 0, published: 0, in_progress: 0 })
  useEffect(() => {
    heritage.projects()
      .then((data) => {
        const list = (Array.isArray(data) ? data : (data.results || [])).map(projectToCard)
        setMyProjects(list.slice(0, 3))
        setStats({
          total: list.length,
          published: list.filter(p => p.status === 'published').length,
          in_progress: list.filter(p => p.status === 'in_progress').length,
        })
      })
      .catch(() => {})
  }, [])
  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="section-title">{t('dashboard.title')}</h1>
          <p className="section-subtitle">{t('dashboard.subtitle')}</p>
        </div>
        <Link to="/app/projets/nouveau" className="btn-primary">{t('appNav.newProject')}</Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={FolderKanban} label={t('dashboard.myProjects')} value={stats.total}/>
        <StatCard icon={CheckCircle2} label={t('dashboard.published')} value={stats.published}/>
        <StatCard icon={AlertTriangle} label={t('dashboard.inProgress')} value={stats.in_progress}/>
        <StatCard icon={FileCheck2} label={t('dashboard.notificationsCount')} value={notifs.length}/>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">{t('dashboard.ongoingProjects')}</h2>
            <Link to="/app/projets" className="text-sm text-terracotta-700 flex items-center gap-1">{t('dashboard.all')} <ArrowRight size={14}/></Link>
          </div>
          <ul className="divide-y divide-sand-100">
            {myProjects.map(p => (
              <li key={p.id} className="py-3 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg" style={{background: `linear-gradient(135deg, ${p.coverColor}, #3e2417)`}}/>
                <div className="flex-1 min-w-0">
                  <Link to={`/app/projets/${p.id}`} className="font-medium hover:text-terracotta-700">{p.name}</Link>
                  <div className="text-xs text-sand-500">{p.region} • {p.period}</div>
                </div>
                <StatusBadge status={p.status}/>
              </li>
            ))}
          </ul>
        </section>

        <section className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold flex items-center gap-2"><Activity size={18}/>{t('dashboard.recentActivity')}</h2>
          </div>
          <ul className="space-y-3 text-sm">
            {notifs.slice(0, 4).length === 0 && (
              <li className="text-sand-500 text-sm">{t('dashboard.noActivity')}</li>
            )}
            {notifs.slice(0, 4).map(n => (
              <li key={n.id} className="flex items-start gap-2">
                <div className={`w-2 h-2 mt-2 rounded-full shrink-0 ${n.read ? 'bg-sand-300' : 'bg-terracotta-500'}`}/>
                <div className="flex-1">
                  <div>{n.title}</div>
                  <div className="text-xs text-sand-500">{n.body}</div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <section className="card p-5">
          <h2 className="font-semibold flex items-center gap-2"><Sparkles size={18} className="text-terracotta-600"/>{t('dashboard.suggestions')}</h2>
          <p className="text-sm text-sand-600 mt-1">{t('dashboard.suggestionsBody')}</p>
          <ul className="mt-3 space-y-2">
            {myProjects.length === 0 && <li className="text-sm text-sand-500 p-3">{t('dashboard.noSuggestions')}</li>}
            {myProjects.map(p => (
              <li key={p.id} className="flex items-center justify-between p-3 rounded-lg bg-sand-50 border border-sand-100">
                <div>
                  <Link to={`/app/projets/${p.id}`} className="font-medium hover:text-terracotta-700">{p.name}</Link>
                  <div className="text-xs text-sand-500">{p.type} — {p.region}</div>
                </div>
                <Link to={`/app/projets/${p.id}`} className="btn-ghost text-sm">{t('dashboard.complete')}</Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="card p-5">
          <h2 className="font-semibold flex items-center gap-2"><Bell size={18}/>{t('appNav.notifications')}</h2>
          <ul className="mt-3 space-y-2">
            {notifs.slice(0,4).map(n => (
              <li key={n.id} className="flex gap-3 p-3 rounded-lg bg-sand-50 border border-sand-100">
                <div className={`w-2 mt-1 rounded-full ${n.read?'bg-sand-300':'bg-terracotta-500'}`} style={{height:8}}/>
                <div className="flex-1">
                  <div className="text-sm font-medium">{n.title}</div>
                  <div className="text-xs text-sand-600">{n.body}</div>
                </div>
              </li>
            ))}
          </ul>
          <Link to="/app/notifications" className="text-sm text-terracotta-700 mt-3 inline-flex items-center gap-1">{t('dashboard.viewAll')} <ArrowRight size={14}/></Link>
        </section>
      </div>
    </div>
  )
}

function AdminDashboard({ notifs }) {
  const { t } = useTranslation()
  const [stats, setStats] = useState(null)
  const [validating, setValidating] = useState({})

  useEffect(() => {
    adminApi.stats().then(setStats).catch(() => {})
  }, [])

  const handleValidate = async (userId, decision) => {
    setValidating(v => ({ ...v, [userId]: true }))
    try {
      await adminApi.validateUser(userId, decision)
      // Refresh stats so the pending list updates.
      adminApi.stats().then(setStats).catch(() => {})
    } finally {
      setValidating(v => ({ ...v, [userId]: false }))
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="section-title">{t('dashboard.adminTitle')}</h1>
        <p className="section-subtitle">{t('dashboard.adminSubtitle')}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={UsersIcon} label={t('dashboard.users')} value={stats?.total_users ?? '—'}/>
        <StatCard icon={FolderKanban} label={t('dashboard.projectsLabel')} value={stats?.total_projects ?? '—'}/>
        <StatCard icon={AlertTriangle} label={t('dashboard.openConflicts')} value={stats?.open_conflicts ?? '—'}/>
        <StatCard icon={FileCheck2} label={t('dashboard.toValidate')} value={stats?.pending_users ?? '—'}/>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <section className="card p-5">
          <h2 className="font-semibold">{t('dashboard.expertRequests')}</h2>
          <ul className="divide-y divide-sand-100 mt-2">
            {(stats?.pending_experts ?? []).length === 0 && (
              <li className="py-4 text-sm text-sand-500">{t('dashboard.noPendingExperts')}</li>
            )}
            {(stats?.pending_experts ?? []).map(u => (
              <li key={u.id} className="py-3 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-terracotta-600 text-white grid place-items-center font-semibold shrink-0">
                  {u.full_name.split(' ').map(s => s[0]).slice(0, 2).join('').toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{u.full_name}</div>
                  <div className="text-xs text-sand-500 truncate">
                    {u.disciplines.join(', ') || '—'}{u.institution ? ` • ${u.institution}` : ''}
                  </div>
                </div>
                <button
                  disabled={validating[u.id]}
                  onClick={() => handleValidate(u.id, 'reject')}
                  className="btn-secondary text-xs shrink-0"
                >{t('dashboard.reject')}</button>
                <button
                  disabled={validating[u.id]}
                  onClick={() => handleValidate(u.id, 'approve')}
                  className="btn-primary text-xs shrink-0"
                >{t('dashboard.approve')}</button>
              </li>
            ))}
          </ul>
          <Link to="/app/admin/utilisateurs" className="text-sm text-terracotta-700 mt-3 inline-flex items-center gap-1">
            {t('dashboard.manageAll')} <ArrowRight size={14}/>
          </Link>
        </section>

        <section className="card p-5">
          <h2 className="font-semibold flex items-center gap-2"><BarChart3 size={18}/>{t('dashboard.globalStats')}</h2>
          <div className="grid grid-cols-2 gap-3 mt-3">
            {[
              { l: t('dashboard.statTotalUsers'),   v: stats?.total_users    ?? '—' },
              { l: t('dashboard.statActiveUsers'),  v: stats?.active_users   ?? '—' },
              { l: t('dashboard.statProjects'),      v: stats?.total_projects ?? '—' },
              { l: t('dashboard.statConflicts'),     v: stats?.open_conflicts ?? '—' },
            ].map((k, i) => (
              <div key={i} className="p-3 rounded-lg bg-sand-50 border border-sand-100">
                <div className="text-xs text-sand-500 uppercase tracking-widest">{k.l}</div>
                <div className="text-2xl font-semibold mt-1">{k.v}</div>
              </div>
            ))}
          </div>
          <Link to="/app/admin/statistiques" className="text-sm text-terracotta-700 mt-4 inline-flex items-center gap-1">
            {t('dashboard.viewDetails')} <ArrowRight size={14}/>
          </Link>
        </section>
      </div>

      <section className="card p-5">
        <h2 className="font-semibold flex items-center gap-2">
          <AlertTriangle size={18} className="text-amber-600"/>{t('dashboard.recentAlerts')}
        </h2>
        <ul className="mt-3 space-y-2">
          {notifs.length === 0 && (
            <li className="text-sm text-sand-500 p-3">{t('dashboard.noAlerts')}</li>
          )}
          {notifs.map(n => (
            <li key={n.id} className="flex items-start gap-3 p-3 rounded-lg bg-amber-50 border border-amber-100">
              <span className="chip bg-white border border-amber-200 text-amber-800 capitalize">{n.type}</span>
              <div className="flex-1">
                <div className="text-sm font-medium">{n.title}</div>
                <div className="text-xs text-sand-600">{n.body}</div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
