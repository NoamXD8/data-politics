// Outils partagés pour lire le format compact produit par le pipeline :
// v = [inscrits, votants, exprimes, blancs, nuls, voix_candidat_1, ..., voix_autres]

export const COULEURS = {
  commune: "var(--series-1)",
  departement: "var(--series-2)",
  france: "var(--series-3)"
};

const pct = new Intl.NumberFormat("fr-FR", {style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1});
const nombre = new Intl.NumberFormat("fr-FR");
export const fmtPct = (x) => (x == null || isNaN(x) ? "–" : pct.format(x));
export const fmtNombre = (x) => (x == null ? "–" : nombre.format(x));

export function participation(v) {
  return v && v[0] ? v[1] / v[0] : null;
}

/** Résultats d'un scrutin : [{candidat, voix, part}] triés du plus fort au plus faible, « Autres » en dernier. */
export function resultats(election, v) {
  if (!v) return [];
  const lignes = election.candidats.map((cle, i) => ({
    candidat: election.noms?.[i] ?? cle,
    famille: election.familles?.[i] ?? "div",
    voix: v[5 + i],
    part: v[2] ? v[5 + i] / v[2] : 0
  }));
  const autres = lignes.filter((d) => d.candidat === "Autres" && d.voix > 0);
  return lignes
    .filter((d) => d.candidat !== "Autres" && d.voix > 0)
    .sort((a, b) => b.voix - a.voix)
    .concat(autres);
}

/** Raccourcit les noms de listes très longs pour l'axe (le nom complet reste dans l'infobulle). */
export function raccourcir(nom, max = 30) {
  return nom.length > max ? nom.slice(0, max - 1).trimEnd() + "…" : nom;
}

/** Libellé court d'un scrutin pour les axes : « Prés. 2022 T1 » */
export function court(election) {
  const types = {pres: "Prés.", legi: "Légis.", euro: "Euro."};
  return `${types[election.type] ?? election.type} ${election.annee}${election.type === "euro" ? "" : ` T${election.tour}`}`;
}

/** Scrutin affiché par défaut : le 1er tour de la présidentielle la plus récente. */
export function scrutinParDefaut(elections) {
  const pres = elections.filter((e) => e.type === "pres" && e.tour === 1);
  return (pres.length ? pres : elections).at(-1);
}

/** Recherche insensible aux accents, à la casse et aux tirets. */
export function normaliser(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[-'’]/g, " ").toLowerCase();
}

/** Identifiant d'URL d'un candidat : « Jean-Luc MÉLENCHON » → « jean-luc-melenchon ». */
export function slug(nom) {
  return nom.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

/** Part d'un candidat (par son slug) dans un vecteur de résultats, ou null s'il n'était pas candidat. */
export function partDe(election, v, s) {
  if (!v) return null;
  const i = (election.noms ?? election.candidats).findIndex((n) => slug(n) === s);
  return i < 0 || !v[2] ? null : v[5 + i] / v[2];
}

/** Rang (1 = premier) d'un candidat à un scrutin. */
export function rangDe(election, v, s) {
  const r = resultats(election, v).filter((d) => d.candidat !== "Autres");
  const i = r.findIndex((d) => slug(d.candidat) === s);
  return i < 0 ? null : i + 1;
}
