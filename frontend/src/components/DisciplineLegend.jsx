import { useTranslation } from 'react-i18next'
import { Tag } from 'lucide-react'

/**
 * Dynamic legend showing the disciplines that have authored at least one
 * version on the current project. Each row uses the discipline's
 * `color_hex` (set in the admin) as the swatch — this is the same color
 * used to outline section headers and the contributor avatars in the
 * editor, fulfilling the "color-coding contributors by discipline" item
 * from the spec.
 */
export default function DisciplineLegend({ disciplines }) {
  const { t, i18n } = useTranslation()
  if (!disciplines || disciplines.length === 0) return null
  const isRtl = i18n.language?.startsWith('ar')

  return (
    <div className="card p-5">
      <h3 className="font-semibold flex items-center gap-2">
        <Tag size={16}/>{t('projects.legend.title')}
      </h3>
      <ul className="mt-3 space-y-1.5">
        {disciplines.map((d) => (
          <li key={d.id} className="flex items-center gap-2 text-sm">
            <span
              className="inline-block w-3.5 h-3.5 rounded-sm flex-shrink-0"
              style={{ background: d.color_hex || '#824c2b' }}
            />
            <span className="text-sand-800">
              {isRtl && d.name_ar ? d.name_ar : d.name_fr}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
