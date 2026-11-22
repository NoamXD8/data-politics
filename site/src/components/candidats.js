// Outils partagés par l'onglet Candidats 2027 et les fiches individuelles.
import * as Plot from "npm:@observablehq/plot";
import {html} from "npm:htl";
import {fmtPct, court, slug, partDe, rangDe} from "./elections.js";
import {couleur} from "./familles.js";

// Regroupement politique repris de la source (République 2027), pas d'un classement maison
export const GROUPES = ["Extrême gauche", "Gauche", "Écologistes", "Centre", "Droite", "Extrême droite", "Divers"];
export function groupeDe(c) {
  return c.groupe ?? ({
    exg: "Extrême gauche", pcf: "Gauche", lfi: "Gauche", ug: "Gauche", ps: "Gauche", dvg: "Gauche",
    eco: "Écologistes", ens: "Centre", mdm: "Centre", udi: "Centre", dvc: "Centre",
    lr: "Droite", dvd: "Droite", souv: c.nom === "Florian Philippot" ? "Extrême droite" : "Droite",
    rn: "Extrême droite", uxd: "Extrême droite", rec: "Extrême droite"
  }[c.famille] ?? "Divers");
}

const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
export function dateFr(d) {
  if (!d) return "date non précisée";
  const [a, m, j] = d.split("-");
  if (!m) return a;
  return `${j ? `${+j === 1 ? "1er" : +j} ` : ""}${MOIS[+m - 1]} ${a}`;
}

export const nomDeFamille = (nom) => nom.split(" ").slice(1).join(" ");

/** Portrait si une photo libre de droits a été renseignée (champ photo + credit), sinon initiales. */
export function portrait(c, dark, taille = 56) {
  const bord = couleur(c.famille, dark);
  if (c.photo) {
    return html`<figure style="margin:0;flex:none;width:${taille}px">
      <img src="${c.photo}" alt="Portrait de ${c.nom}" loading="lazy"
        style="width:${taille}px;height:${taille}px;border-radius:50%;object-fit:cover;border:3px solid ${bord}">
      ${c.credit && taille > 80 ? html`<figcaption style="font-size:.7rem;color:var(--theme-foreground-muted);margin-top:.2rem">${c.credit}</figcaption>` : ""}
    </figure>`;
  }
  const initiales = c.nom.split(/[\s-]+/).filter((m) => /^[A-ZÀ-Ý]/.test(m)).map((m) => m[0]).slice(0, 2).join("");
  return html`<div aria-hidden="true" style="flex:none;width:${taille}px;height:${taille}px;border-radius:50%;border:3px solid ${bord};
    display:flex;align-items:center;justify-content:center;font-weight:600;font-size:${taille * 0.34}px;color:var(--theme-foreground-muted)">${initiales}</div>`;
}

/** Résultats d'une personne aux présidentielles, calculés depuis les données officielles. */
export function historique(nom, elections, france) {
  const s = slug(nom);
  return elections
    .filter((e) => e.type === "pres")
    .map((e) => ({e, part: partDe(e, france.france[e.id], s), rang: rangDe(e, france.france[e.id], s)}))
    .filter((d) => d.part != null);
}

/** Graphique en barres des scores nationaux aux présidentielles. */
export function graphiqueHistorique(presences, teinte, width) {
  return Plot.plot({
    subtitle: "Part des suffrages exprimés, France entière",
    width: Math.min(width, 140 * presences.length + 60),
    height: 240,
    marginBottom: 40,
    x: {label: null, domain: presences.map((d) => court(d.e))},
    y: {axis: null, domain: [0, Math.max(0.3, ...presences.map((d) => d.part)) * 1.15]},
    marks: [
      Plot.barY(presences, {x: (d) => court(d.e), y: "part", fill: teinte, rx1: 4, insetLeft: 12, insetRight: 12,
        tip: {format: {x: false, y: false}, channels: {Scrutin: (d) => d.e.libelle, Score: (d) => fmtPct(d.part), Rang: (d) => `${d.rang}${d.rang === 1 ? "er" : "e"}`}}}),
      Plot.text(presences, {x: (d) => court(d.e), y: "part", text: (d) => fmtPct(d.part), dy: -10, fill: "currentColor"}),
      Plot.ruleY([0])
    ]
  });
}
