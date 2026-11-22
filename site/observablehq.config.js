import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";

// Dossier des fichiers produits par le pipeline (surchargeable : DATA_DIR=... npm run dev)
const ICI = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = process.env.DATA_DIR ?? path.join(ICI, "..", "data", "processed");

// Une page par département, générée à partir de la liste produite par le pipeline
let departements = [];
try {
  departements = JSON.parse(fs.readFileSync(path.join(DATA_DIR, "departements.json"), "utf-8"));
} catch {
  console.warn(`⚠ ${DATA_DIR}/departements.json introuvable : lance d'abord le pipeline.`);
}

// Une page par candidat de la dernière présidentielle (1er tour), même gabarit pour tous
export function slug(nom) {
  return nom.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}
let candidats = [];
try {
  const elections = JSON.parse(fs.readFileSync(path.join(DATA_DIR, "elections.json"), "utf-8"));
  const derniere = elections.filter((e) => e.type === "pres" && e.tour === 1).at(-1);
  candidats = (derniere?.noms ?? []).filter((n) => n !== "Autres").map(slug);
} catch {}

// Une fiche par candidature 2027 (liste tenue à la main dans src/data/candidats-2027.json)
let candidats2027 = [];
try {
  candidats2027 = JSON.parse(fs.readFileSync(path.join(ICI, "src", "data", "candidats-2027.json"), "utf-8")).candidats.map((c) => slug(c.nom));
} catch {}

export default {
  title: "Data Politics",
  root: "src",
  lang: "fr",
  theme: ["air", "near-midnight"],
  style: "style.css",
  pages: [
    {name: "Accueil", path: "/"},
    {name: "Candidats 2027", path: "/candidats-2027"},
    {name: "Sondages 2022", path: "/sondages-2022"},
    {name: "Reports de voix", path: "/reports-de-voix"},
    {name: "Méthodologie", path: "/methodologie"}
  ],
  dynamicPaths: [
    ...departements.map((d) => `/departement/${d.code}`),
    ...candidats.map((c) => `/candidat/${c}`),
    ...candidats2027.map((c) => `/candidat-2027/${c}`)
  ],
  interpreters: {".py": [process.platform === "win32" ? "python" : "python3"]},
  footer:
    "Données : Ministère de l'Intérieur via data.gouv.fr (Licence Ouverte). Site indépendant et non partisan."
};
