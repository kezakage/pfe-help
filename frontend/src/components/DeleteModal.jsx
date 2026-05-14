import { useEffect } from "react";
import { createPortal } from "react-dom";
import { AlertTriangle, X, Loader2 } from "lucide-react";

export default function DeleteModal({
  open,
  title,
  description,
  confirmLabel,
  cancelLabel,
  loading = false,
  error = null,
  onClose,
  onConfirm,
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape" && !loading) onClose?.();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, loading, onClose]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
      className="fixed inset-0 z-[1200] grid place-items-center bg-black/60 p-4"
      onClick={() => {
        if (!loading) onClose?.();
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white shadow-2xl ring-1 ring-black/5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-sand-100 px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-red-50 p-2 text-red-700">
              <AlertTriangle size={18} />
            </div>
            <div>
              <h3
                id="delete-modal-title"
                className="font-semibold text-sand-900"
              >
                {title}
              </h3>
              <p className="mt-1 text-sm text-sand-600">{description}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              if (!loading) onClose?.();
            }}
            aria-label={cancelLabel}
            className="rounded p-1 text-sand-500 hover:bg-sand-100 disabled:opacity-50"
            disabled={loading}
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex flex-wrap justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                if (!loading) onClose?.();
              }}
              className="btn-ghost"
              disabled={loading}
            >
              {cancelLabel}
            </button>
            <button
              type="button"
              onClick={onConfirm}
              className="btn-danger inline-flex items-center gap-2"
              disabled={loading}
            >
              {loading && <Loader2 size={14} className="animate-spin" />}
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
