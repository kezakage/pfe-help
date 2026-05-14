import { useMemo, useRef, useEffect } from 'react'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { useTranslation } from 'react-i18next'

/**
 * WYSIWYG editor (Quill) used inside ProjectWorkspace.
 *
 * Storage model: we keep the existing `content_json` shape on PageVersion by
 * embedding the Quill HTML output under `{ format: "quill", html: "..." }`.
 * The legacy Tiptap-style `{ type: "doc", content: [...] }` shape is still
 * supported on read so old pages keep rendering until they get re-saved.
 *
 * RTL: when i18next is in Arabic mode, Quill receives `direction: "rtl"` and
 * a logical `text-align: right` so the toolbar + editor flip correctly.
 */
const FORMATS = [
  'header', 'bold', 'italic', 'underline', 'strike',
  'list', 'bullet', 'blockquote', 'code-block',
  'link', 'image', 'align', 'direction',
]

export default function RichEditor({ value, onChange, placeholder, borderColor }) {
  const { i18n } = useTranslation()
  const isRtl = i18n.language?.startsWith('ar')
  const ref = useRef(null)

  const modules = useMemo(() => ({
    toolbar: [
      [{ header: [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ list: 'ordered' }, { list: 'bullet' }],
      ['blockquote', 'code-block'],
      ['link'],
      [{ align: [] }, { direction: 'rtl' }],
      ['clean'],
    ],
    clipboard: { matchVisual: false },
  }), [])

  // When the document language flips, force the Quill root direction so the
  // current editor instance reflows even without re-mount.
  useEffect(() => {
    const root = ref.current?.getEditor()?.root
    if (!root) return
    root.setAttribute('dir', isRtl ? 'rtl' : 'ltr')
    root.style.textAlign = isRtl ? 'right' : 'left'
  }, [isRtl])

  return (
    <div
      className="quill-shell rounded-lg overflow-hidden border"
      style={{ borderColor: borderColor || 'rgb(228 222 213)' }}
    >
      <ReactQuill
        ref={ref}
        theme="snow"
        value={value || ''}
        onChange={onChange}
        modules={modules}
        formats={FORMATS}
        placeholder={placeholder}
      />
    </div>
  )
}
