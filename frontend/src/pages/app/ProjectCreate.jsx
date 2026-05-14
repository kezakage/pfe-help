import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Upload, Image as ImageIcon, Loader2 } from "lucide-react";
import { PERIODS, REGIONS, TYPES } from "../../data/projects.js";
import {
  heritage,
  media as mediaApi,
  pages as pagesApi,
} from "../../lib/api.js";

const STEPS = ["Informations", "Médias", "Structure du contenu"];

export default function ProjectCreate() {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [files, setFiles] = useState([]);
  const [data, setData] = useState({
    name: "",
    name_ar: "",
    region: "Alger",
    period: "ottoman",
    type: "mosque",
    classification_level: "unclassified",
    summary: "",
    description: "",
    longitude: "",
    latitude: "",
    sections: [
      "Présentation",
      "Histoire",
      "Description architecturale",
      "État de conservation",
    ],
  });

  const set = (k) => (e) => setData({ ...data, [k]: e.target.value });

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      // 1. HeritageResource
      const resourcePayload = {
        name_fr: data.name,
        name_ar: data.name_ar,
        wilaya: data.region,
        period: data.period,
        architectural_type: data.type,
        classification_level: data.classification_level,
        description: data.description || data.summary,
      };
      if (data.longitude && data.latitude) {
        resourcePayload.longitude = parseFloat(data.longitude);
        resourcePayload.latitude = parseFloat(data.latitude);
      }
      const resource = await heritage.createResource(resourcePayload);

      // 2. Project bound to that resource
      const project = await heritage.createProject({
        resource_id: resource.id,
        title: data.name,
        description: data.summary || "",
        status: "draft",
      });

      // 3. Initial pages from sections
      for (let i = 0; i < data.sections.length; i++) {
        await pagesApi.create({
          project: project.id,
          title: data.sections[i],
          position: i,
        });
      }

      // 4. Optional media uploads
      for (const f of files) {
        const fd = new FormData();
        fd.append("file", f);
        fd.append("project", project.id);
        const kind = f.type.startsWith("image/")
          ? "image"
          : f.type.startsWith("video/")
            ? "video"
            : "document";
        fd.append("media_type", kind);
        try {
          await mediaApi.upload(fd);
        } catch (_) {
          /* tolerate single failure */
        }
      }

      nav(`/app/projets/${project.id}`);
    } catch (e) {
      if (e.data && typeof e.data === "object") {
        const labels = {
          name_fr: "Nom du monument",
          name_ar: "Nom (arabe)",
          resource_id: "Ressource patrimoniale",
          title: "Titre",
          description: "Description",
          wilaya: "Région",
          period: "Période",
          architectural_type: "Type architectural",
        };
        const messages = Object.entries(e.data).map(([field, errs]) => {
          const label =
            labels[field] || (field === "non_field_errors" ? "" : field);
          const text = Array.isArray(errs) ? errs.join(" ") : String(errs);
          return label ? `${label} : ${text}` : text;
        });
        setError(messages.join("\n"));
      } else {
        setError(e.message || "Une erreur est survenue. Veuillez réessayer.");
      }
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button onClick={() => nav(-1)} className="btn-ghost">
        <ArrowLeft size={16} />
        Retour
      </button>
      <div>
        <h1 className="section-title">Nouveau projet</h1>
        <p className="section-subtitle">
          Créez la fiche initiale du monument ou du site.
        </p>
      </div>

      <div className="flex items-center gap-3">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-3">
            <div
              className={`w-7 h-7 rounded-full grid place-items-center text-xs font-semibold ${i <= step ? "bg-terracotta-600 text-white" : "bg-sand-200 text-sand-600"}`}
            >
              {i + 1}
            </div>
            <div
              className={`text-sm ${i === step ? "font-semibold" : "text-sand-600"}`}
            >
              {s}
            </div>
            {i < STEPS.length - 1 && <div className="w-12 h-px bg-sand-200" />}
          </div>
        ))}
      </div>

      <div className="card p-6">
        {step === 0 && (
          <div className="grid md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="label">Nom du monument / projet *</label>
              <input
                className="input"
                required
                value={data.name}
                onChange={set("name")}
                placeholder="Ex. Mosquée de Sidi Boumediene"
              />
            </div>
            <div className="md:col-span-2">
              <label className="label">Nom (arabe)</label>
              <input
                className="input"
                value={data.name_ar}
                onChange={set("name_ar")}
                placeholder="جامع سيدي بومدين"
                dir="rtl"
              />
            </div>
            <div>
              <label className="label">Région</label>
              <select
                className="input"
                value={data.region}
                onChange={set("region")}
              >
                {REGIONS.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Période</label>
              <select
                className="input"
                value={data.period}
                onChange={set("period")}
              >
                {PERIODS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Type architectural</label>
              <select
                className="input"
                value={data.type}
                onChange={set("type")}
              >
                {TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Classement</label>
              <select
                className="input"
                value={data.classification_level}
                onChange={set("classification_level")}
              >
                <option value="unclassified">Non classé</option>
                <option value="regional">Régional</option>
                <option value="national">National</option>
                <option value="unesco">UNESCO</option>
              </select>
            </div>
            <div>
              <label className="label">Longitude (optionnel)</label>
              <input
                className="input"
                value={data.longitude}
                onChange={set("longitude")}
                placeholder="3.0588"
              />
            </div>
            <div>
              <label className="label">Latitude (optionnel)</label>
              <input
                className="input"
                value={data.latitude}
                onChange={set("latitude")}
                placeholder="36.7833"
              />
            </div>
            <div className="md:col-span-2">
              <label className="label">Résumé court</label>
              <textarea
                rows={3}
                className="input resize-none"
                value={data.summary}
                onChange={set("summary")}
                placeholder="Décrivez brièvement le projet..."
              />
            </div>
            <div className="md:col-span-2">
              <label className="label">Description complète</label>
              <textarea
                rows={5}
                className="input resize-none"
                value={data.description}
                onChange={set("description")}
                placeholder="Histoire, contexte, sources..."
              />
            </div>
          </div>
        )}

        {step === 1 && (
          <div>
            <label className="label">Médias (images, plans, documents)</label>
            <div className="border-2 border-dashed border-sand-300 rounded-xl p-10 text-center bg-sand-50">
              <Upload className="mx-auto text-sand-500" size={32} />
              <p className="mt-3 text-sand-700">
                Glissez-déposez vos fichiers ou
              </p>
              <input
                id="filepick"
                type="file"
                multiple
                className="hidden"
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
              />
              <label
                htmlFor="filepick"
                className="btn-primary mt-3 inline-flex"
              >
                <ImageIcon size={16} />
                Parcourir
              </label>
              <p className="text-xs text-sand-500 mt-3">
                JPG, PNG, PDF — max 50 Mo / fichier
              </p>
            </div>
            {files.length > 0 && (
              <ul className="mt-4 text-sm space-y-1">
                {files.map((f, i) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>{f.name}</span>
                    <span className="text-sand-500">
                      {(f.size / 1024).toFixed(0)} Ko
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {step === 2 && (
          <div>
            <label className="label">Structure initiale du contenu</label>
            <p className="text-sm text-sand-600 mb-3">
              Définissez les sections principales de la fiche. Vous pourrez les
              modifier dans l'éditeur.
            </p>
            <ul className="space-y-2">
              {data.sections.map((s, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="w-6 text-center text-sand-500">
                    {i + 1}.
                  </span>
                  <input
                    className="input"
                    value={s}
                    onChange={(e) => {
                      const next = [...data.sections];
                      next[i] = e.target.value;
                      setData({ ...data, sections: next });
                    }}
                  />
                  <button
                    onClick={() =>
                      setData({
                        ...data,
                        sections: data.sections.filter((_, j) => j !== i),
                      })
                    }
                    className="btn-ghost text-red-600"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
            <button
              onClick={() =>
                setData({
                  ...data,
                  sections: [...data.sections, "Nouvelle section"],
                })
              }
              className="btn-secondary mt-3"
            >
              + Ajouter une section
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="card p-4 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm font-semibold text-red-700 mb-1">
            Impossible de créer le projet
          </p>
          {error.split("\n").map((line, i) => (
            <p key={i} className="text-sm text-red-600">
              • {line}
            </p>
          ))}
        </div>
      )}

      <div className="flex justify-between">
        <button
          disabled={step === 0 || submitting}
          onClick={() => setStep(step - 1)}
          className="btn-secondary"
        >
          Précédent
        </button>
        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep(step + 1)}
            className="btn-primary"
            disabled={submitting}
          >
            Suivant
          </button>
        ) : (
          <button
            onClick={submit}
            className="btn-primary"
            disabled={submitting || !data.name}
          >
            {submitting && <Loader2 className="animate-spin" size={14} />} Créer
            le projet
          </button>
        )}
      </div>
    </div>
  );
}
