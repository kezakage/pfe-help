import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Navigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ArrowLeft,
  History,
  Users as UsersIcon,
  MessageSquare,
  Image as ImageIcon,
  FileText,
  MapPin,
  Save,
  Eye,
  Pin,
  GitCompare,
  RotateCcw,
  Plus,
  Loader2,
  Upload,
  AlertTriangle,
  Box as Box3D,
  Smartphone,
} from "lucide-react";
import StatusBadge from "../../components/StatusBadge.jsx";
import Model3DViewer from "../../components/Model3DViewer.jsx";
import ARShareModal from "../../components/ARShareModal.jsx";
import DeleteModal from "../../components/DeleteModal.jsx";
import RichEditor from "../../components/RichEditor.jsx";
import VersionDiff from "../../components/VersionDiff.jsx";
import DisciplineLegend from "../../components/DisciplineLegend.jsx";
import MediaAnnotator from "../../components/MediaAnnotator.jsx";
import {
  heritage,
  pages as pagesApi,
  media as mediaApi,
  discussions as discApi,
  mediaUrl,
} from "../../lib/api.js";
import { projectToCard } from "../../data/projects.js";
import { useAuth } from "../../context/AuthContext.jsx";

const TABS = [
  { k: "edit", label: "Éditeur", icon: FileText },
  { k: "media", label: "Médias & galerie", icon: ImageIcon },
  { k: "models3d", label: "3D", icon: Box3D },
  { k: "annotations", label: "Annotations", icon: Pin },
  { k: "history", label: "Historique", icon: History },
  { k: "discussion", label: "Discussion", icon: MessageSquare },
];

export default function ProjectWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("edit");
  const [notFound, setNotFound] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  // Disciplines that have authored at least one version on this project — used
  // by the dynamic legend in the sidebar and to color-code section headers.
  const [projectDisciplines, setProjectDisciplines] = useState([]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      heritage.project(id),
      heritage.members(id).catch(() => []),
      pagesApi.list(id).catch(() => []),
    ])
      .then(([proj, mem, pgs]) => {
        if (cancelled) return;
        setProject({ raw: proj, ...projectToCard(proj) });
        setMembers(Array.isArray(mem) ? mem : []);
        const list = Array.isArray(pgs) ? pgs : pgs.results || [];
        const seen = new Map();
        for (const p of list) {
          const d = p.current_version?.discipline;
          if (d && !seen.has(d.id)) seen.set(d.id, d);
        }
        setProjectDisciplines(Array.from(seen.values()));
      })
      .catch((e) => {
        if (e.status === 404) setNotFound(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading)
    return (
      <div className="text-sand-600 inline-flex items-center gap-2 p-6">
        <Loader2 className="animate-spin" size={16} />
        {t("common.loading")}
      </div>
    );
  if (notFound || !project) return <Navigate to="/app/projets" replace />;

  const handleDeleteProject = async () => {
    if (!project?.id) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await heritage.deleteProject(project.id);
      if (project.resourceId) {
        await heritage.deleteResource(project.resourceId);
      }
      navigate("/app/projets", { replace: true });
    } catch (e) {
      setDeleteError(e?.message || t("common.loadingError"));
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-4 flex-wrap">
        <Link to="/app/projets" className="btn-ghost">
          <ArrowLeft size={16} />
          Projets
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-display font-semibold">
              {project.name}
            </h1>
            <StatusBadge status={project.status} />
          </div>
          <p className="text-sand-600 text-sm mt-1">
            {project.region} • {project.period} • {project.type}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/projets-publics/${project.resourceId}`}
            className="btn-secondary"
          >
            <Eye size={16} />
            Aperçu public
          </Link>
          <button
            className="btn-primary"
            onClick={async () => {
              await heritage.publish(project.id);
              const fresh = await heritage.project(id);
              setProject({ raw: fresh, ...projectToCard(fresh) });
            }}
          >
            <Save size={16} />
            Publier
          </button>
          <button className="btn-danger" onClick={() => setDeleteOpen(true)}>
            <AlertTriangle size={16} />
            Supprimer
          </button>
        </div>
      </div>

      <div className="border-b border-sand-200">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px flex items-center gap-2 ${
                tab === t.k
                  ? "border-terracotta-600 text-terracotta-700"
                  : "border-transparent text-sand-600 hover:text-sand-900"
              }`}
            >
              <t.icon size={16} />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-5">
          {tab === "edit" && <Editor projectId={project.id} />}
          {tab === "media" && (
            <MediaGallery
              projectId={project.id}
              coverColor={project.coverColor}
            />
          )}
          {tab === "models3d" && <Models3DPanel projectId={project.id} />}
          {tab === "annotations" && <AnnotationsPanel projectId={project.id} />}
          {tab === "history" && <VersionHistory projectId={project.id} />}
          {tab === "discussion" && <DiscussionTab projectId={project.id} />}
        </div>

        <aside className="space-y-4">
          <div className="card p-5">
            <h3 className="font-semibold flex items-center gap-2">
              <UsersIcon size={16} />
              Contributeurs
            </h3>
            <ul className="mt-3 space-y-2">
              {members.length === 0 && (
                <li className="text-sm text-sand-500">Aucun contributeur</li>
              )}
              {members.map((m, i) => (
                <li key={m.id || i} className="flex items-center gap-2">
                  <div
                    className="w-8 h-8 rounded-full grid place-items-center text-white text-xs font-semibold"
                    style={{
                      background: ["#824c2b", "#cd5028", "#67241a", "#a56432"][
                        i % 4
                      ],
                    }}
                  >
                    {(m.user?.full_name || m.user?.email || "U")
                      .slice(0, 2)
                      .toUpperCase()}
                  </div>
                  <div className="text-sm">
                    <div>{m.user?.full_name || m.user?.email}</div>
                    <div className="text-xs text-sand-500">
                      {m.project_role}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <DisciplineLegend disciplines={projectDisciplines} />

          {project.lat != null && project.lng != null && (
            <div className="card p-5">
              <h3 className="font-semibold flex items-center gap-2">
                <MapPin size={16} />
                {t("projects.location")}
              </h3>
              <div className="mt-3 h-32 rounded-lg map-bg relative overflow-hidden">
                <div className="absolute" style={{ top: "40%", left: "45%" }}>
                  <MapPin className="text-terracotta-700" size={24} />
                </div>
              </div>
              <div className="text-xs text-sand-500 mt-2">
                {project.lat.toFixed(3)}, {project.lng.toFixed(3)}
              </div>
            </div>
          )}
        </aside>
      </div>

      <DeleteModal
        open={deleteOpen}
        title={t("projects.deleteResource.title")}
        description={t("projects.deleteResource.body", { name: project.name })}
        confirmLabel={t("projects.deleteResource.confirm")}
        cancelLabel={t("common.cancel")}
        loading={deleting}
        error={deleteError}
        onClose={() => {
          if (!deleting) setDeleteOpen(false);
        }}
        onConfirm={handleDeleteProject}
      />
    </div>
  );
}

function Editor({ projectId }) {
  const { t, i18n } = useTranslation();
  const { user } = useAuth() || {};
  const locale = i18n.language?.startsWith("ar") ? "ar" : "fr-FR";
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [drafts, setDrafts] = useState({});
  // Each entry tracks the version the user *based their edits on*. If the
  // server's current_version has moved past it, another contributor saved in
  // between — that's the conflict we surface before letting the save go through.
  const [baselines, setBaselines] = useState({}); // { [pageId]: { versionId, versionNumber } }
  const [conflicts, setConflicts] = useState({}); // { [pageId]: { baseline, current } }
  const [diffPair, setDiffPair] = useState(null); // [a, b] for VersionDiff modal

  // Helper: hydrate state from a fresh page list. Used at mount, after save,
  // and after the user explicitly chooses "reload from server" on a conflict.
  const ingestPages = (list, { resetDrafts = true } = {}) => {
    setPages(list);
    const b = {};
    const d = {};
    for (const p of list) {
      const cv = p.current_version;
      b[p.id] = { versionId: cv?.id, versionNumber: cv?.version_number ?? 0 };
      if (resetDrafts) d[p.id] = htmlFromContent(cv?.content_json);
    }
    setBaselines(b);
    if (resetDrafts) setDrafts(d);
    setConflicts({});
  };

  useEffect(() => {
    let cancelled = false;
    pagesApi
      .list(projectId)
      .then((data) => {
        if (cancelled) return;
        const list = Array.isArray(data) ? data : data.results || [];
        ingestPages(list, { resetDrafts: true });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  /**
   * Save flow with optimistic concurrency check.
   *
   * The backend always appends a new version (no server-side rejection on
   * conflict — see PageVersionViewSet.perform_create), so we detect conflicts
   * client-side: refresh the page list, compare each page's current
   * version_number to our baseline. If something has moved, we block the save
   * for that page and let the user inspect / reload / force-save.
   *
   * Pass force=true to bypass the conflict gate (after the user has reviewed
   * the diff and decided their edit takes priority).
   */
  const saveAll = async (force = false) => {
    setSaving(true);
    const disciplineId = user?.disciplines?.[0]?.id;
    try {
      // Concurrency check: refresh the page list and compare baselines.
      const data = await pagesApi.list(projectId);
      const fresh = Array.isArray(data) ? data : data.results || [];
      const freshById = Object.fromEntries(fresh.map((p) => [p.id, p]));

      if (!force) {
        const detected = {};
        for (const p of pages) {
          const baseline = baselines[p.id];
          const current = freshById[p.id]?.current_version;
          if (
            baseline &&
            current &&
            current.version_number > baseline.versionNumber
          ) {
            detected[p.id] = { baseline, current };
          }
        }
        if (Object.keys(detected).length > 0) {
          setConflicts(detected);
          // Reflect newest version numbers in the header without overwriting drafts.
          setPages(fresh);
          return;
        }
      }

      for (const p of pages) {
        const html = drafts[p.id] || "";
        await pagesApi.createVersion({
          page: p.id,
          content_json: contentFromHtml(html),
          change_summary: t("common.edit"),
          status: "draft",
          ...(disciplineId ? { discipline_id: disciplineId } : {}),
        });
      }
      const after = await pagesApi.list(projectId);
      const afterList = Array.isArray(after) ? after : after.results || [];
      ingestPages(afterList, { resetDrafts: false });
    } finally {
      setSaving(false);
    }
  };

  const reloadPageFromServer = (pageId) => {
    const fresh = pages.find((p) => p.id === pageId);
    if (!fresh) return;
    setDrafts((d) => ({
      ...d,
      [pageId]: htmlFromContent(fresh.current_version?.content_json),
    }));
    setBaselines((b) => ({
      ...b,
      [pageId]: {
        versionId: fresh.current_version?.id,
        versionNumber: fresh.current_version?.version_number ?? 0,
      },
    }));
    setConflicts((c) => {
      const next = { ...c };
      delete next[pageId];
      return next;
    });
  };

  const dismissConflict = (pageId) => {
    setConflicts((c) => {
      const next = { ...c };
      delete next[pageId];
      return next;
    });
  };

  const addSection = async () => {
    const title = prompt(t("projects.promptSectionTitle"));
    if (!title) return;
    await pagesApi.create({
      project: projectId,
      title,
      position: pages.length,
    });
    const data = await pagesApi.list(projectId);
    const list = Array.isArray(data) ? data : data.results || [];
    setPages(list);
  };

  if (loading)
    return (
      <div className="card p-6 text-sand-600 inline-flex items-center gap-2">
        <Loader2 className="animate-spin" size={16} />
        {t("common.loading")}
      </div>
    );

  return (
    <div className="card overflow-hidden">
      <div className="p-6 space-y-6">
        {pages.length === 0 && (
          <div className="text-center text-sand-500 py-10">
            {t("projects.noSection")}
          </div>
        )}
        {pages.map((p) => {
          // Color the section header with the author-discipline of the latest
          // version — fulfils the "color-coding contributors by discipline"
          // deliverable from the spec.
          const color = p.current_version?.discipline?.color_hex;
          const conflict = conflicts[p.id];
          return (
            <article key={p.id} className="group">
              <header
                className="flex items-center justify-between mb-2 ps-3 border-s-4"
                style={{ borderColor: color || "transparent" }}
              >
                <h3 className="font-display text-xl font-semibold">
                  {p.title}
                </h3>
                <span className="text-xs text-sand-500">
                  v{p.current_version?.version_number ?? 0}
                </span>
              </header>
              {conflict && (
                <ConflictBanner
                  conflict={conflict}
                  locale={locale}
                  onDiff={() =>
                    setDiffPair([
                      conflict.baseline.versionId,
                      conflict.current.id,
                    ])
                  }
                  onReload={() => reloadPageFromServer(p.id)}
                  onDismiss={() => dismissConflict(p.id)}
                />
              )}
              <RichEditor
                value={drafts[p.id] || ""}
                onChange={(html) => setDrafts({ ...drafts, [p.id]: html })}
                placeholder={t("projects.editor.placeholder")}
                borderColor={color}
              />
            </article>
          );
        })}
        <div className="flex gap-2 flex-wrap">
          <button className="btn-secondary" onClick={addSection}>
            <Plus size={16} />
            {t("projects.addSection")}
          </button>
          {pages.length > 0 && (
            <button
              className="btn-primary"
              disabled={saving}
              onClick={() => saveAll(false)}
            >
              {saving && <Loader2 className="animate-spin" size={14} />}{" "}
              {t("projects.saveAll")}
            </button>
          )}
          {Object.keys(conflicts).length > 0 && (
            <button
              className="btn-danger"
              disabled={saving}
              onClick={() => saveAll(true)}
              title={t("projects.conflict.forceTitle")}
            >
              <AlertTriangle size={14} />
              {t("projects.conflict.force")}
            </button>
          )}
        </div>
      </div>
      {diffPair && (
        <VersionDiff
          a={diffPair[0]}
          b={diffPair[1]}
          onClose={() => setDiffPair(null)}
        />
      )}
    </div>
  );
}

/**
 * Inline banner shown above an article when another contributor saved a new
 * version of the same page since the editor was opened. The user can:
 *   - inspect the changes (opens VersionDiff between baseline and current)
 *   - reload from server (drops their local edits in favor of the new version)
 *   - dismiss the banner (then click "Force save" to write anyway)
 */
function ConflictBanner({ conflict, locale, onDiff, onReload, onDismiss }) {
  const { t } = useTranslation();
  const cur = conflict.current;
  const who = cur.author?.full_name || cur.author?.email || "—";
  const when = cur.created_at
    ? new Date(cur.created_at).toLocaleString(locale)
    : "";
  return (
    <div className="mb-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm">
      <div className="flex items-start gap-2">
        <AlertTriangle
          size={16}
          className="text-amber-700 flex-shrink-0 mt-0.5"
        />
        <div className="flex-1">
          <div className="font-medium text-amber-900">
            {t("projects.conflict.title")}
          </div>
          <div className="text-amber-800 mt-0.5">
            {t("projects.conflict.body", {
              who,
              when,
              from: conflict.baseline.versionNumber,
              to: cur.version_number,
            })}
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <button onClick={onDiff} className="btn-secondary text-xs">
              <GitCompare size={12} />
              {t("projects.conflict.viewChanges")}
            </button>
            <button
              onClick={onReload}
              className="btn-ghost text-xs text-amber-900"
            >
              <RotateCcw size={12} />
              {t("projects.conflict.reload")}
            </button>
            <button onClick={onDismiss} className="btn-ghost text-xs">
              {t("projects.conflict.dismiss")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Read content from a PageVersion.content_json JSONField. Supports two shapes:
 *   - new: { format: "quill", html: "<p>…</p>" }   (current Quill output)
 *   - legacy: { type: "doc", content: [...] }       (old Tiptap-style JSON)
 * Returns HTML safe to feed into <RichEditor>; falls back to plain string.
 */
function htmlFromContent(content) {
  if (!content) return "";
  if (typeof content === "string") return content;
  if (content.format === "quill" && typeof content.html === "string")
    return content.html;
  // Legacy tiptap-like fallback: turn paragraphs into <p>…</p>
  try {
    if (Array.isArray(content.content)) {
      return content.content
        .map((b) => {
          const txt = (b.content || []).map((c) => c.text || "").join("");
          return `<p>${escapeHtml(txt)}</p>`;
        })
        .join("");
    }
  } catch (_) {}
  if (typeof content.text === "string")
    return `<p>${escapeHtml(content.text)}</p>`;
  return "";
}

function contentFromHtml(html) {
  return { format: "quill", html: html || "" };
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function MediaGallery({ projectId, coverColor }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const refresh = async () => {
    const data = await mediaApi.list(projectId);
    const list = Array.isArray(data) ? data : data.results || [];
    setItems(list);
  };

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [projectId]);

  const onUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploading(true);
    try {
      for (const f of files) {
        const fd = new FormData();
        fd.append("file", f);
        fd.append("project", projectId);
        fd.append(
          "media_type",
          f.type.startsWith("image/")
            ? "image"
            : f.type.startsWith("video/")
              ? "video"
              : "document",
        );
        await mediaApi.upload(fd);
      }
      await refresh();
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  if (loading)
    return (
      <div className="card p-6 text-sand-600 inline-flex items-center gap-2">
        <Loader2 className="animate-spin" size={16} />
        Chargement...
      </div>
    );

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Médias du projet ({items.length})</h3>
        <input
          id="m-up"
          type="file"
          multiple
          className="hidden"
          onChange={onUpload}
        />
        <label htmlFor="m-up" className="btn-primary text-sm cursor-pointer">
          {uploading ? (
            <Loader2 className="animate-spin" size={14} />
          ) : (
            <Upload size={14} />
          )}{" "}
          Importer
        </label>
      </div>
      {items.length === 0 ? (
        <div className="text-sand-500 text-center py-10">
          Aucun média. Importez votre première image.
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {items.map((m) => {
            const topTag =
              Array.isArray(m.ai_tags) && m.ai_tags.length > 0
                ? m.ai_tags[0]
                : null;
            return (
              <div
                key={m.id}
                className="aspect-[4/3] rounded-lg overflow-hidden relative bg-sand-100 group"
              >
                {m.thumbnail_url || m.file_url ? (
                  <img
                    src={mediaUrl(m.thumbnail_url || m.file_url)}
                    alt={m.caption || ""}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div
                    className="w-full h-full"
                    style={{
                      background: `linear-gradient(135deg, ${coverColor}, #3e2417)`,
                    }}
                  />
                )}
                <div className="absolute bottom-2 left-2 text-white text-xs bg-black/40 px-2 py-0.5 rounded">
                  {m.media_type}
                </div>
                {m.media_type === "image" && (
                  <div className="absolute top-2 left-2 right-2 flex flex-wrap gap-1">
                    {m.ai_status === "pending" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/90 text-white inline-flex items-center gap-1">
                        <Loader2 className="animate-spin" size={10} />
                        IA…
                      </span>
                    )}
                    {m.ai_status === "failed" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/90 text-white">
                        IA échec
                      </span>
                    )}
                    {topTag && m.ai_status === "done" && (
                      <span
                        className="text-[10px] px-1.5 py-0.5 rounded bg-terracotta-600/95 text-white inline-flex items-center gap-1"
                        title={m.ai_tags
                          .map(
                            (t) => `${t.label} ${(t.score * 100).toFixed(0)}%`,
                          )
                          .join(" · ")}
                      >
                        ✨ {topTag.label} · {Math.round(topTag.score * 100)}%
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Models3DPanel({ projectId }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(null);
  const [shareOpen, setShareOpen] = useState(false);

  const refresh = async () => {
    const data = await mediaApi.list3D(projectId);
    const list = Array.isArray(data) ? data : data.results || [];
    setItems(list);
    if (!active && list.length > 0) setActive(list[0]);
    if (active && !list.find((m) => m.id === active.id))
      setActive(list[0] || null);
  };

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [projectId]);

  const onUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setError("");
    setUploading(true);
    try {
      for (const f of files) {
        const name = (f.name || "").toLowerCase();
        if (!name.endsWith(".glb") && !name.endsWith(".gltf")) {
          setError(`Format non supporté : ${f.name}. Utilisez .glb ou .gltf.`);
          continue;
        }
        const fd = new FormData();
        fd.append("file", f);
        fd.append("project", projectId);
        fd.append("media_type", "model_3d");
        fd.append("caption", f.name);
        await mediaApi.upload(fd);
      }
      await refresh();
    } catch (err) {
      setError(err?.message || "Erreur lors de l'import du modèle 3D.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  if (loading)
    return (
      <div className="card p-6 text-sand-600 inline-flex items-center gap-2">
        <Loader2 className="animate-spin" size={16} />
        Chargement...
      </div>
    );

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h3 className="font-semibold flex items-center gap-2">
              <Box3D size={18} />
              Modèles 3D du projet ({items.length})
            </h3>
            <p className="text-xs text-sand-500 mt-1">
              Format :{" "}
              <code className="px-1 py-0.5 rounded bg-sand-100">.glb</code> ou{" "}
              <code className="px-1 py-0.5 rounded bg-sand-100">.gltf</code> ·
              max 50 Mo · le bouton AR apparaît sur les appareils mobiles
              compatibles.
            </p>
          </div>
          <input
            id="m3d-up"
            type="file"
            accept=".glb,.gltf,model/gltf-binary,model/gltf+json"
            multiple
            className="hidden"
            onChange={onUpload}
          />
          <label
            htmlFor="m3d-up"
            className="btn-primary text-sm cursor-pointer"
          >
            {uploading ? (
              <Loader2 className="animate-spin" size={14} />
            ) : (
              <Upload size={14} />
            )}{" "}
            Importer un modèle
          </label>
        </div>
        {error && (
          <div className="mt-3 text-sm text-red-700 bg-red-50 border border-red-100 rounded px-3 py-2">
            {error}
          </div>
        )}
      </div>

      {items.length === 0 ? (
        <div className="card p-10 text-center text-sand-500">
          <Box3D size={32} className="mx-auto text-sand-300" />
          <p className="mt-3">Aucun modèle 3D pour ce projet.</p>
          <p className="text-xs mt-1">
            Importez un fichier GLB exporté depuis Blender, RealityCapture ou
            Sketchfab.
          </p>
        </div>
      ) : (
        <div className="grid lg:grid-cols-4 gap-4">
          <ul className="lg:col-span-1 card p-3 space-y-1 max-h-[480px] overflow-y-auto">
            {items.map((m) => (
              <li key={m.id}>
                <button
                  onClick={() => setActive(m)}
                  className={`w-full text-left px-3 py-2 rounded text-sm flex items-center gap-2 ${
                    active?.id === m.id
                      ? "bg-terracotta-50 text-terracotta-700"
                      : "hover:bg-sand-50"
                  }`}
                >
                  <Box3D size={14} className="flex-shrink-0" />
                  <span className="truncate">
                    {m.caption || `Modèle #${m.id}`}
                  </span>
                </button>
              </li>
            ))}
          </ul>

          <div className="lg:col-span-3 card p-3">
            {active ? (
              <>
                <Model3DViewer
                  src={mediaUrl(active.file_url)}
                  alt={active.caption || "Modèle 3D"}
                  className="rounded-lg"
                />
                <div className="mt-3 px-1 flex items-center justify-between gap-3 text-xs text-sand-500">
                  <span className="truncate">
                    {active.caption || `Modèle #${active.id}`}
                    {active.size_bytes
                      ? ` · ${(active.size_bytes / (1024 * 1024)).toFixed(1)} Mo`
                      : ""}
                  </span>
                  <button
                    type="button"
                    onClick={() => setShareOpen(true)}
                    className="shrink-0 inline-flex items-center gap-1.5 rounded px-2 py-1 text-terracotta-700 hover:bg-terracotta-50"
                    aria-label="Voir en réalité augmentée (QR code)"
                  >
                    <Smartphone size={14} aria-hidden="true" />
                    <span>Voir en RA</span>
                  </button>
                </div>
              </>
            ) : (
              <div className="text-sand-500 text-sm py-10 text-center">
                Sélectionnez un modèle.
              </div>
            )}
          </div>
        </div>
      )}

      <ARShareModal
        open={shareOpen}
        onClose={() => setShareOpen(false)}
        mediaId={active?.id}
        caption={active?.caption}
      />
    </div>
  );
}

/**
 * Image annotator panel.
 *
 * Lists the project's image-type media in a left rail; the selected one
 * opens in <MediaAnnotator>. Drawing a rectangle prompts for a label and
 * POSTs to /api/v1/media/annotations/. AI-generated tags from the CLIP
 * pipeline (apps/media/tasks.annotate_image) are visible alongside manual
 * ones, with validate/reject actions for moderators — exactly the human-
 * in-the-loop workflow specified for the auto-annotation deliverable.
 */
function AnnotationsPanel({ projectId }) {
  const { t } = useTranslation();
  const { user } = useAuth() || {};
  const [images, setImages] = useState([]);
  const [active, setActive] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Refresh just the annotations for the currently selected image.
  const refreshAnn = async (mediaId) => {
    if (!mediaId) {
      setAnnotations([]);
      return;
    }
    try {
      const a = await mediaApi.annotations({ media: mediaId });
      setAnnotations(Array.isArray(a) ? a : a.results || []);
    } catch (_) {
      setAnnotations([]);
    }
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    mediaApi
      .listImages(projectId)
      .then(async (data) => {
        if (cancelled) return;
        const list = Array.isArray(data) ? data : data.results || [];
        setImages(list);
        if (list.length > 0) {
          setActive(list[0]);
          await refreshAnn(list[0].id);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const switchTo = async (m) => {
    setActive(m);
    await refreshAnn(m.id);
  };

  const handleCreate = async ({ geometry_json, body_text }) => {
    if (!active) return;
    const disciplineId = user?.disciplines?.[0]?.id;
    await mediaApi.createAnnotation({
      media: active.id,
      geometry_json,
      body_text,
      ...(disciplineId ? { discipline: disciplineId } : {}),
    });
    await refreshAnn(active.id);
  };

  const handleValidate = async (id) => {
    await mediaApi.validateAnnotation(id);
    await refreshAnn(active?.id);
  };

  const handleReject = async (id) => {
    await mediaApi.rejectAnnotation(id);
    await refreshAnn(active?.id);
  };

  const handleDelete = async (id) => {
    if (!confirm(t("annotator.confirmDelete"))) return;
    await mediaApi.deleteAnnotation(id);
    await refreshAnn(active?.id);
  };

  if (loading)
    return (
      <div className="card p-6 text-sand-600 inline-flex items-center gap-2">
        <Loader2 className="animate-spin" size={16} />
        {t("common.loading")}
      </div>
    );

  if (images.length === 0) {
    return (
      <div className="card p-10 text-center text-sand-500">
        <Pin size={32} className="mx-auto text-sand-300" />
        <p className="mt-3">{t("annotator.noImages")}</p>
        <p className="text-xs mt-1">{t("annotator.noImagesHint")}</p>
      </div>
    );
  }

  return (
    <div className="grid lg:grid-cols-4 gap-4">
      <ul className="lg:col-span-1 card p-3 space-y-1 max-h-[520px] overflow-y-auto">
        {images.map((m) => (
          <li key={m.id}>
            <button
              onClick={() => switchTo(m)}
              className={`w-full text-start px-2 py-2 rounded text-sm flex items-center gap-2 ${
                active?.id === m.id
                  ? "bg-terracotta-50 text-terracotta-700"
                  : "hover:bg-sand-50"
              }`}
            >
              <div className="w-10 h-10 rounded overflow-hidden bg-sand-100 flex-shrink-0">
                {(m.thumbnail_url || m.file_url) && (
                  <img
                    src={mediaUrl(m.thumbnail_url || m.file_url)}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                )}
              </div>
              <span className="truncate">{m.caption || `#${m.id}`}</span>
            </button>
          </li>
        ))}
      </ul>

      <div className="lg:col-span-3 card p-4">
        {active ? (
          <>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold flex items-center gap-2">
                <Pin size={16} />
                {active.caption || `#${active.id}`}
              </h3>
              <span className="text-xs text-sand-500">
                {t("annotator.dragHint")}
              </span>
            </div>
            <MediaAnnotator
              mediaId={active.id}
              src={mediaUrl(active.file_url)}
              annotations={annotations}
              currentUserId={user?.id}
              onCreate={handleCreate}
              onValidate={handleValidate}
              onReject={handleReject}
              onDelete={handleDelete}
            />
          </>
        ) : (
          <div className="text-sand-500 text-sm py-10 text-center">
            {t("annotator.selectImage")}
          </div>
        )}
      </div>
    </div>
  );
}

function VersionHistory({ projectId }) {
  const { t, i18n } = useTranslation();
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  // Up to 2 version IDs the user has selected for visual diffing.
  const [picked, setPicked] = useState([]);
  const [diffPair, setDiffPair] = useState(null);
  const locale = i18n.language?.startsWith("ar") ? "ar" : "fr-FR";

  const refresh = async () => {
    const data = await pagesApi.list(projectId);
    const ps = Array.isArray(data) ? data : data.results || [];
    const all = [];
    for (const p of ps) {
      try {
        const h = await pagesApi.history(p.id);
        const list = Array.isArray(h) ? h : h.results || [];
        for (const v of list) all.push({ ...v, pageTitle: p.title });
      } catch (_) {}
    }
    all.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    setVersions(all);
  };
  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [projectId]);

  const restore = async (versionId) => {
    if (!confirm(t("projects.history.confirmRestore"))) return;
    await pagesApi.restore(versionId);
    await refresh();
  };

  const togglePick = (id) => {
    setPicked((cur) => {
      if (cur.includes(id)) return cur.filter((x) => x !== id);
      if (cur.length >= 2) return [cur[1], id]; // sliding window of 2
      return [...cur, id];
    });
  };

  if (loading)
    return (
      <div className="card p-6 text-sand-600 inline-flex items-center gap-2">
        <Loader2 className="animate-spin" size={16} />
        {t("common.loading")}
      </div>
    );
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4 gap-2 flex-wrap">
        <h3 className="font-semibold">
          {t("projects.history.title")} ({versions.length})
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-sand-500">
            {picked.length === 0
              ? t("projects.history.selectTwo")
              : picked.length === 1
                ? `1/2`
                : `2/2`}
          </span>
          <button
            disabled={picked.length !== 2}
            onClick={() => setDiffPair([picked[0], picked[1]])}
            className="btn-secondary text-xs disabled:opacity-50"
          >
            <GitCompare size={12} />
            {t("projects.history.compareSelected")}
          </button>
          {picked.length > 0 && (
            <button onClick={() => setPicked([])} className="btn-ghost text-xs">
              {t("projects.history.clear")}
            </button>
          )}
        </div>
      </div>
      {versions.length === 0 ? (
        <p className="text-sand-500 text-sm">
          {t("projects.history.noVersions")}
        </p>
      ) : (
        <ul className="relative ps-6 border-s-2 border-sand-200 space-y-5">
          {versions.map((v, i) => {
            const checked = picked.includes(v.id);
            const dotColor = v.discipline?.color_hex || "#cd5028";
            return (
              <li key={v.id} className="relative">
                <span
                  className="absolute -start-[31px] w-4 h-4 rounded-full ring-4 ring-white"
                  style={{ background: dotColor }}
                />
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <label className="flex items-start gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => togglePick(v.id)}
                      className="mt-1 accent-terracotta-600"
                    />
                    <span>
                      <span className="font-medium">
                        v{v.version_number} —{" "}
                        {v.change_summary || t("projects.history.noSummary")}
                      </span>
                      <span className="block text-xs text-sand-500">
                        {v.pageTitle} •{" "}
                        {v.author?.full_name || v.author?.email || "—"} •{" "}
                        {new Date(v.created_at).toLocaleString(locale)}
                      </span>
                    </span>
                  </label>
                  {i > 0 && (
                    <button
                      onClick={() => restore(v.id)}
                      className="btn-ghost text-xs text-terracotta-700"
                    >
                      <RotateCcw size={12} />
                      {t("projects.history.restore")}
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {diffPair && (
        <VersionDiff
          a={diffPair[0]}
          b={diffPair[1]}
          onClose={() => setDiffPair(null)}
        />
      )}
    </div>
  );
}

function DiscussionTab({ projectId }) {
  const [discussions, setDiscussions] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    const data = await discApi.list(projectId);
    const list = Array.isArray(data) ? data : data.results || [];
    setDiscussions(list);
    if (!active && list.length > 0) {
      setActive(list[0]);
      const m = await discApi.messages(list[0].id);
      setMessages(Array.isArray(m) ? m : m.results || []);
    }
  };

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [projectId]);

  const switchTo = async (d) => {
    setActive(d);
    const m = await discApi.messages(d.id);
    setMessages(Array.isArray(m) ? m : m.results || []);
  };

  const send = async () => {
    if (!draft.trim() || !active) return;
    await discApi.postMessage(active.id, draft);
    setDraft("");
    const m = await discApi.messages(active.id);
    setMessages(Array.isArray(m) ? m : m.results || []);
  };

  const create = async () => {
    const title = prompt("Titre de la discussion");
    if (!title) return;
    const d = await discApi.create({
      project: projectId,
      title,
      type: "general",
      status: "open",
    });
    await refresh();
    switchTo(d);
  };

  if (loading)
    return (
      <div className="card p-6 text-sand-600 inline-flex items-center gap-2">
        <Loader2 className="animate-spin" size={16} />
        Chargement...
      </div>
    );

  return (
    <div className="grid md:grid-cols-3 gap-4">
      <div className="card p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-sm">Discussions</h3>
          <button onClick={create} className="btn-ghost text-xs">
            <Plus size={12} />
          </button>
        </div>
        {discussions.length === 0 && (
          <p className="text-sand-500 text-xs">Aucune discussion</p>
        )}
        <ul className="space-y-1">
          {discussions.map((d) => (
            <li key={d.id}>
              <button
                onClick={() => switchTo(d)}
                className={`w-full text-left px-2 py-1.5 rounded text-sm ${active?.id === d.id ? "bg-terracotta-50 text-terracotta-700" : "hover:bg-sand-50"}`}
              >
                {d.title}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="card p-5 md:col-span-2">
        {!active ? (
          <p className="text-sand-500 text-sm">
            Sélectionnez ou créez une discussion.
          </p>
        ) : (
          <>
            <h3 className="font-semibold">{active.title}</h3>
            <ul className="mt-4 space-y-3 max-h-96 overflow-y-auto">
              {messages.map((m) => (
                <li key={m.id} className="flex gap-3">
                  <div className="w-9 h-9 rounded-full bg-terracotta-600 grid place-items-center text-white text-xs font-semibold">
                    {(m.author?.full_name || m.author?.email || "U")
                      .slice(0, 2)
                      .toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">
                        {m.author?.full_name || m.author?.email}
                      </span>
                      <span className="text-xs text-sand-500">
                        {new Date(m.created_at).toLocaleString("fr-FR")}
                      </span>
                    </div>
                    <div className="text-sm text-sand-800 mt-0.5 whitespace-pre-line">
                      {m.body}
                    </div>
                  </div>
                </li>
              ))}
              {messages.length === 0 && (
                <li className="text-sand-500 text-sm">Aucun message</li>
              )}
            </ul>
            <div className="mt-4 flex gap-2">
              <input
                className="input flex-1"
                placeholder="Écrire un message..."
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") send();
                }}
              />
              <button onClick={send} className="btn-primary">
                Envoyer
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
