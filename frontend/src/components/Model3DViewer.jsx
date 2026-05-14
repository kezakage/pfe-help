import { useEffect } from 'react'

/**
 * Lightweight wrapper around <model-viewer> (Google's web component).
 *
 * <model-viewer> is registered globally on first import — we trigger that
 * side-effectful import lazily so it doesn't bloat the initial bundle for
 * users who never open a 3D tab.
 *
 * The `ar` attribute enables free WebXR / Scene Viewer (Android) / AR Quick
 * Look (iOS) entry points where the device supports it; on desktop it's a
 * pure 3D viewer.
 */
export default function Model3DViewer({ src, alt = '3D model', poster, className = '' }) {
  useEffect(() => {
    // Register the custom element only once, on the client.
    import('@google/model-viewer').catch(() => {})
  }, [])

  if (!src) return null

  return (
    <model-viewer
      src={src}
      alt={alt}
      poster={poster}
      camera-controls=""
      auto-rotate=""
      ar=""
      ar-modes="webxr scene-viewer quick-look"
      shadow-intensity="1"
      exposure="1"
      className={`block w-full h-full bg-sand-100 rounded-lg ${className}`}
      style={{ minHeight: 360 }}
    />
  )
}
