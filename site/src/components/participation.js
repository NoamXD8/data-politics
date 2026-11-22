// Graphique de participation en « petits multiples » : un panneau par type d'élection,
// pour ne comparer une présidentielle qu'avec d'autres présidentielles.
import * as Plot from "npm:@observablehq/plot";
import {fmtPct, participation} from "./elections.js";

const TYPES = [
  {type: "pres", nom: "Présidentielles"},
  {type: "legi", nom: "Législatives"},
  {type: "euro", nom: "Européennes (tour unique)"}
];

/**
 * @param elections  liste des scrutins (elections.json)
 * @param series     [{nom, couleur, valeurs: {id_election: vecteur}}]
 * @param tour       1 ou 2 (les européennes n'ont qu'un tour et restent affichées)
 * @param selection  scrutin sélectionné ailleurs sur la page, mis en évidence
 */
export function graphiqueParticipation({elections, series, tour, width, selection}) {
  const nomType = new Map(TYPES.map((t) => [t.type, t.nom]));
  const lignes = [];
  for (const e of elections) {
    if (!nomType.has(e.type) || e.tour !== (e.type === "euro" ? 1 : tour)) continue;
    for (const s of series) {
      const p = participation(s.valeurs[e.id]);
      if (p != null) lignes.push({panneau: nomType.get(e.type), annee: e.annee, qui: s.nom, p, choisi: e.id === selection?.id, libelle: e.libelle});
    }
  }
  const panneaux = TYPES.map((t) => t.nom).filter((n) => lignes.some((d) => d.panneau === n));
  const annees = [...new Set(lignes.map((d) => d.annee))].sort();
  const etroit = width < 640; // sur mobile, panneaux empilés
  const f = etroit ? {fy: "panneau"} : {fx: "panneau"};
  const unique = series.length === 1;

  return Plot.plot({
    width,
    height: etroit ? 190 * panneaux.length : 300,
    marginTop: 28,
    marginRight: 20,
    // Les titres de panneaux sont dessinés au-dessus de chaque panneau (lisible sur mobile)
    [etroit ? "fy" : "fx"]: {domain: panneaux, label: null, axis: null, padding: etroit ? 0.25 : 0.1},
    x: {label: null, ticks: annees, tickFormat: "d", inset: 14},
    y: {label: null, domain: [0, 1], ticks: 5, tickFormat: (d) => fmtPct(d).replace(",0", ""), grid: true},
    color: {domain: series.map((s) => s.nom), range: series.map((s) => s.couleur), legend: !unique},
    marks: [
      Plot.frame({...f, strokeOpacity: 0.1}),
      Plot.text(panneaux, {...(etroit ? {fy: (d) => d} : {fx: (d) => d}), text: (d) => d, frameAnchor: "top", dy: -16, fontWeight: 600, fill: "currentColor"}),
      Plot.line(lignes, {...f, x: "annee", y: "p", stroke: "qui", strokeWidth: 2}),
      Plot.dot(lignes, {...f, x: "annee", y: "p", fill: "qui", r: (d) => (d.choisi ? 6 : 4), stroke: "var(--theme-background)", strokeWidth: 2}),
      // Étiquette de valeur seulement avec une seule série (sinon elles se chevauchent ; l'infobulle suffit)
      Plot.text(lignes.filter((d) => d.choisi && unique), {...f, x: "annee", y: "p", text: (d) => fmtPct(d.p), dy: -14, fill: "currentColor"}),
      Plot.tip(lignes, Plot.pointer({...f, x: "annee", y: "p", title: (d) => `${d.qui} · ${d.libelle}\nParticipation : ${fmtPct(d.p)}`}))
    ]
  });
}
