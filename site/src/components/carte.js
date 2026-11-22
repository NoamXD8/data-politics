// Carte des départements : couleur de la famille du candidat arrivé en tête,
// teinte plus ou moins soutenue selon son score. Clic = page du département.
import * as Plot from "npm:@observablehq/plot";
import {html} from "npm:htl";
import {fmtPct, resultats} from "./elections.js";
import {couleur, FAMILLES} from "./familles.js";

function enTete(election, v) {
  return resultats(election, v).filter((d) => d.candidat !== "Autres")[0] ?? null;
}

/**
 * @param contours      GeoJSON des départements de métropole (propriétés code, nom)
 * @param departements  liste [{code, nom}] issue du pipeline
 * @param parDep        france.departements (résultats par département)
 */
export function carteDepartements({contours, departements, parDep, election, width, dark, base = "./"}) {
  const noms = new Map(departements.map((d) => [d.code, d.nom]));
  const infos = new Map(departements.map((d) => [d.code, enTete(election, parDep[d.code]?.[election.id])]));
  const parts = [...infos.values()].filter(Boolean).map((d) => d.part);
  const [min, max] = [Math.min(...parts), Math.max(...parts)];
  // Teinte : de 45 % d'opacité (score le plus faible) à 100 % (score le plus fort)
  const opacite = (part) => (max > min ? 0.45 + (0.55 * (part - min)) / (max - min) : 1);

  const features = contours.features.map((f) => ({...f, info: infos.get(f.properties.code)}));
  const titre = (f) => {
    const i = f.info;
    const nom = noms.get(f.properties.code) ?? f.properties.nom;
    return i ? `${nom}\nEn tête : ${i.candidat} (${fmtPct(i.part)})\nCliquer pour le détail` : `${nom}\nPas de données`;
  };

  const carte = Plot.plot({
    width,
    height: Math.min(width, 620),
    projection: {type: "conic-conformal", parallels: [44, 49], rotate: [-3, 0], domain: contours, inset: 6},
    marks: [
      Plot.geo(features, {
        fill: (f) => (f.info ? couleur(f.info.famille, dark) : "var(--theme-foreground-faintest)"),
        fillOpacity: (f) => (f.info ? opacite(f.info.part) : 1),
        stroke: "var(--theme-background)",
        strokeWidth: 0.8,
        href: (f) => `${base}departement/${f.properties.code}`
      }),
      Plot.tip(features, Plot.pointer(Plot.centroid({title: titre})))
    ]
  });

  // Légende : familles présentes, avec le nombre de départements gagnés (métropole + outre-mer)
  const compte = new Map();
  for (const i of infos.values()) if (i) compte.set(i.famille, (compte.get(i.famille) ?? 0) + 1);
  const legende = html`<div style="display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;font-size:.85rem;margin:.25rem 0 .5rem">
    ${[...compte].sort((a, b) => b[1] - a[1]).map(([fam, n]) => html`<span style="display:inline-flex;align-items:center;gap:.4em">
      <span style="width:.9em;height:.9em;border-radius:2px;background:${couleur(fam, dark)}"></span>${FAMILLES[fam].nom} · ${n} dép.</span>`)}
  </div>`;

  // Outre-mer, Français de l'étranger et tout code absent des contours de métropole
  const enMetropole = new Set(contours.features.map((f) => f.properties.code));
  const autres = departements.filter((d) => !enMetropole.has(d.code) && infos.get(d.code));
  const tuiles = autres.length ? html`<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:.5rem;margin-top:.5rem">
    ${autres.map((d) => {
      const i = infos.get(d.code);
      return html`<a href="${base}departement/${d.code}" style="display:flex;gap:.5em;align-items:center;padding:.4rem .6rem;border:1px solid var(--theme-foreground-faintest);border-radius:6px;text-decoration:none;color:inherit;font-size:.85rem">
        <span style="width:1em;height:1em;flex:none;border-radius:2px;background:${couleur(i.famille, dark)};opacity:${opacite(i.part)}"></span>
        <span>${d.nom}<br><small style="color:var(--theme-foreground-muted)">${i.candidat} · ${fmtPct(i.part)}</small></span></a>`;
    })}
  </div>` : "";

  return html`<div>${legende}${carte}${tuiles}</div>`;
}
