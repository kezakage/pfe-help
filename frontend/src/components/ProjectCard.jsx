import { Link } from 'react-router-dom'
import { MapPin, Calendar, Image as ImageIcon, Users } from 'lucide-react'
import StatusBadge from './StatusBadge.jsx'

export default function ProjectCard({ project, to }) {
  const target = to || `/projets-publics/${project.id}`
  return (
    <Link to={target} className="card overflow-hidden hover:-translate-y-0.5 hover:shadow-lg transition-all block group">
      <div className="h-40 relative" style={{ background: `linear-gradient(135deg, ${project.coverColor}, #3e2417)` }}>
        <div className="absolute inset-0 opacity-20"
          style={{ backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,.4) 0 1px, transparent 1px 12px)' }} />
        <div className="absolute inset-0 grid place-items-center">
          <div className="font-display text-white text-3xl font-semibold drop-shadow text-center px-4">
            {project.name}
          </div>
        </div>
        <div className="absolute top-3 left-3"><StatusBadge status={project.status} /></div>
        <span className="chip bg-white/90 text-sand-800 absolute top-3 right-3">{project.type}</span>
      </div>
      <div className="p-4">
        <p className="text-sm text-sand-700 line-clamp-2">{project.summary}</p>
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-sand-600">
          <span className="flex items-center gap-1"><MapPin size={14}/>{project.region}</span>
          <span className="flex items-center gap-1"><Calendar size={14}/>{project.period}</span>
          <span className="flex items-center gap-1"><ImageIcon size={14}/>{project.images ?? 0}</span>
          <span className="flex items-center gap-1"><Users size={14}/>{project.contributors?.length ?? 0}</span>
        </div>
      </div>
    </Link>
  )
}
