// Static reference data + helpers to map backend payloads to frontend shape.

export const PERIODS = [
  { value: 'prehistoric', label: 'Préhistorique' },
  { value: 'numidian', label: 'Numide' },
  { value: 'roman', label: 'Antique' },
  { value: 'medieval', label: 'Médiéval' },
  { value: 'ottoman', label: 'Ottoman' },
  { value: 'colonial', label: 'Colonial' },
  { value: 'contemporary', label: 'Contemporain' },
]

export const TYPES = [
  { value: 'mosque', label: 'Mosquée' },
  { value: 'medersa', label: 'Médersa' },
  { value: 'casbah', label: 'Casbah' },
  { value: 'palace', label: 'Palais' },
  { value: 'fortification', label: 'Fortification' },
  { value: 'church', label: 'Église' },
  { value: 'synagogue', label: 'Synagogue' },
  { value: 'mausoleum', label: 'Mausolée' },
  { value: 'traditional_house', label: 'Habitat traditionnel' },
  { value: 'archaeological_site', label: 'Site archéologique' },
  { value: 'other', label: 'Autre' },
]

export const REGIONS = [
  'Alger', 'Oran', 'Constantine', 'Tlemcen', 'Ghardaïa', 'Annaba',
  'Béjaïa', 'Tipaza', 'Adrar', 'Béchar', 'Sétif', 'Batna', 'M\'Sila',
  'Illizi',
]

export const STATUS_LABEL = {
  draft: 'Brouillon',
  in_progress: 'En cours',
  published: 'Validé',
  archived: 'Archivé',
  en_cours: 'En cours',
  valide: 'Validé',
  en_conflit: 'En conflit',
}

export const STATUS_CLASS = {
  draft: 'bg-slate-100 text-slate-700',
  in_progress: 'bg-amber-100 text-amber-800',
  published: 'bg-emerald-100 text-emerald-800',
  archived: 'bg-slate-100 text-slate-600',
  en_cours: 'bg-amber-100 text-amber-800',
  valide: 'bg-emerald-100 text-emerald-800',
  en_conflit: 'bg-red-100 text-red-800',
}

const COLOR_PALETTE = ['#8f2e1c', '#a56432', '#cd5028', '#bd7d3d', '#824c2b', '#67241a']
const colorFor = (id) => COLOR_PALETTE[(Number(id) || 0) % COLOR_PALETTE.length]

export const periodLabel = (v) => PERIODS.find(p => p.value === v)?.label || v
export const typeLabel = (v) => TYPES.find(t => t.value === v)?.label || v

/** Map a backend HeritageResource to the legacy front-end card shape. */
export function resourceToCard(r) {
  if (!r) return null
  return {
    id: r.id,
    name: r.name_fr,
    name_ar: r.name_ar,
    summary: (r.description || '').split('\n')[0]?.slice(0, 180) || '',
    description: r.description,
    period: periodLabel(r.period),
    periodValue: r.period,
    type: typeLabel(r.architectural_type),
    typeValue: r.architectural_type,
    region: r.wilaya,
    classification: r.classification_level,
    lat: r.latitude,
    lng: r.longitude,
    coverColor: colorFor(r.id),
    status: 'valide',
  }
}

/** Map a backend Project (with embedded resource) to a card. */
export function projectToCard(p) {
  if (!p) return null
  const base = p.resource ? resourceToCard(p.resource) : {}
  return {
    ...base,
    id: p.id,
    resourceId: p.resource?.id,
    name: p.title || base.name,
    summary: p.description?.slice(0, 180) || base.summary,
    description: p.description || base.description,
    status: p.status || 'in_progress',
    contributors: (p.members_preview || []).map((m) => m.full_name || m.email),
    images: p.media_count ?? 0,
    annotations: p.annotation_count ?? 0,
    versions: p.version_count ?? 0,
  }
}
