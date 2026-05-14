import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

// Fix Leaflet's default icon path (broken under Vite/Webpack bundlers)
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

// UNESCO marker — terracotta circle to stand out
const unescoIcon = L.divIcon({
  className: 'unesco-marker',
  html: '<div style="background:#c2410c;color:#fff;border:2px solid #fff;border-radius:9999px;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;box-shadow:0 1px 4px rgba(0,0,0,.3)">★</div>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
})

// Algeria centroid + zoom showing the whole country
const ALGERIA_CENTER = [28.0339, 1.6596]
const DEFAULT_ZOOM = 5

const PERIOD_LABELS = {
  prehistoric: 'Préhistorique',
  numidian: 'Numide',
  roman: 'Romaine',
  medieval: 'Médiévale',
  ottoman: 'Ottomane',
  colonial: 'Coloniale',
  contemporary: 'Contemporaine',
}

function FitToFeatures({ features }) {
  const map = useMap()
  useEffect(() => {
    if (!features || features.length === 0) return
    const bounds = L.latLngBounds(
      features.map(f => [f.geometry.coordinates[1], f.geometry.coordinates[0]])
    )
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 9 })
  }, [features, map])
  return null
}

export default function MapView({ features = [] }) {
  return (
    <div className="relative w-full h-[560px] rounded-xl border border-sand-200 overflow-hidden">
      <MapContainer
        center={ALGERIA_CENTER}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        className="w-full h-full"
        style={{ background: '#f5f1e8' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitToFeatures features={features} />
        {features.map(f => {
          const [lng, lat] = f.geometry.coordinates
          const p = f.properties || {}
          const isUnesco = p.classification_level === 'unesco'
          return (
            <Marker
              key={f.id}
              position={[lat, lng]}
              icon={isUnesco ? unescoIcon : new L.Icon.Default()}
            >
              <Popup>
                <div className="space-y-1 min-w-[180px]">
                  <div className="font-semibold text-sand-900">{p.name_fr}</div>
                  {p.name_ar && (
                    <div dir="rtl" className="text-xs text-sand-600">{p.name_ar}</div>
                  )}
                  <div className="text-xs text-sand-700">
                    {p.commune ? `${p.commune}, ` : ''}{p.wilaya}
                  </div>
                  <div className="text-xs">
                    <span className="inline-block bg-sand-100 px-1.5 py-0.5 rounded">
                      {PERIOD_LABELS[p.period] || p.period}
                    </span>
                    {isUnesco && (
                      <span className="ml-1 inline-block bg-terracotta-600 text-white px-1.5 py-0.5 rounded">
                        UNESCO
                      </span>
                    )}
                  </div>
                  <Link
                    to={`/projets-publics/${f.id}`}
                    className="inline-block text-xs text-terracotta-700 underline mt-1"
                  >
                    Voir la fiche →
                  </Link>
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>

      <div className="absolute bottom-3 right-3 z-[400] bg-white/90 px-3 py-1.5 rounded text-xs text-sand-700 shadow flex items-center gap-3">
        <span className="inline-flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-terracotta-600"></span> UNESCO
        </span>
        <span>{features.length} ressource(s)</span>
      </div>
    </div>
  )
}
