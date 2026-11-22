---
title: Reports de voix
toc: false
---

```js
import {couleur} from "./components/familles.js";

const tous = FileAttachment("data/reports.json").json();
```

# Les reports de voix entre les deux tours

<div class="note" label="Une estimation, pas une mesure">Le vote est secret : personne ne sait ce qu'a fait chaque électeur au 2nd tour. Ces chiffres sont une <strong>estimation statistique</strong> : on compare, commune par commune, les résultats des deux tours. Là où un candidat était fort au 1er tour, quel finaliste, ou l'abstention, a gagné le plus au 2nd ? Cela suppose que les électeurs d'un même candidat se comportent de façon comparable partout. Les fourchettes indiquent l'incertitude du calcul. Les instituts de sondage publient aussi leurs propres estimations, issues d'enquêtes le soir du vote, qui peuvent différer.</div>

```js
const annees = Object.keys(tous).sort();
if (!annees.length) display(html`<div class="note">Les reports ne sont pas encore calculés : lance <code>python -m pipeline.reports</code> à la racine du projet, puis relance le site.</div>`);
```

```js
const annee = view(Inputs.radio(annees, {label: "Présidentielle", value: annees.at(-1)}));
```

```js
const r = tous[annee];
const GRIS = {blanc: dark ? "#6b6b6b" : "#c9c9c9", abstention: dark ? "#4a4a4a" : "#8f8f8f"};
const teinte = (famille) => GRIS[famille] ?? couleur(famille, dark);
const nomCourt = (n) => (/[A-ZÀ-Ý]{2,}/.test(n) ? n.replace(/^(\S+) /, (m, p) => `${p[0]}. `) : n);
const lignes = r.origines.flatMap((o, i) => r.destinations.map((d, j) => ({
  origine: o.nom, destination: d.nom, part: r.matrice[i][j], bas: r.bas[i][j], haut: r.haut[i][j],
  voix: r.effectifs[i] * r.matrice[i][j], famille: d.famille
})));
const pctTxt = (x) => `${Math.round(100 * x)} %`;
```

## Où sont allés les électeurs de chaque candidat ?

<p class="explication">Pour 100 électeurs de chaque candidat du 1er tour (et pour 100 abstentionnistes), la répartition estimée au 2nd tour de ${annee}. Calcul sur ${r.n_communes.toLocaleString("fr-FR")} communes.</p>

```js
display(Plot.plot({
  width,
  height: 50 + r.origines.length * 36,
  marginLeft: 170,
  x: {axis: null, domain: [0, 1]},
  y: {label: null, domain: r.origines.map((o) => o.nom)},
  color: {domain: r.destinations.map((d) => d.nom), range: r.destinations.map((d) => teinte(d.famille)), legend: true},
  marks: [
    Plot.barX(lignes, Plot.stackX({y: "origine", x: "part", fill: "destination", order: r.destinations.map((d) => d.nom), insetTop: 4, insetBottom: 4, insetRight: 1})),
    Plot.text(lignes.filter((d) => d.part >= 0.1), Plot.stackX({y: "origine", x: "part", z: "destination", order: r.destinations.map((d) => d.nom), text: (d) => pctTxt(d.part),
      fill: (d) => (["rn", "lfi", "pcf", "exg", "rec", "abstention", "ug", "lr"].includes(d.famille) ? "white" : "black"), fontSize: 11})),
    Plot.tip(lignes, Plot.pointer(Plot.stackX({y: "origine", x: "part", fill: "destination", order: r.destinations.map((d) => d.nom),
      title: (d) => `Électeurs de ${d.origine} au 1er tour\n→ ${d.destination} : ${pctTxt(d.part)} (entre ${pctTxt(d.bas)} et ${pctTxt(d.haut)})\nsoit environ ${Math.round(d.voix / 1000).toLocaleString("fr-FR")} 000 personnes`})))
  ]
}));
```

## D'où viennent les voix de chaque finaliste ?

<p class="explication">Nombre estimé d'électeurs du 2nd tour, selon ce qu'ils avaient fait au 1er tour (en millions).</p>

```js
const finalistes = r.destinations.filter((d) => !["blanc", "abstention"].includes(d.famille));
display(html`<div class="grid grid-cols-2">${finalistes.map((f) => {
  const sources = lignes.filter((d) => d.destination === f.nom && d.voix > 0).sort((a, b) => b.voix - a.voix);
  const total = sources.reduce((s, d) => s + d.voix, 0);
  const familleOrigine = new Map(r.origines.map((o) => [o.nom, o.famille]));
  return html`<div class="card" style="margin:0">
    <h3 style="margin-top:0">${f.nom}</h3>
    <div style="color:var(--theme-foreground-muted);font-size:.85rem">environ ${(total / 1e6).toLocaleString("fr-FR", {maximumFractionDigits: 1})} millions de voix</div>
    ${Plot.plot({
      width: Math.min(width / 2 - 40, 460),
      height: 30 + sources.length * 24,
      marginLeft: 120,
      marginRight: 50,
      x: {axis: null},
      y: {label: null, domain: sources.map((d) => d.origine), tickFormat: nomCourt},
      marks: [
        Plot.barX(sources, {y: "origine", x: (d) => d.voix / 1e6, fill: (d) => teinte(familleOrigine.get(d.origine)), rx2: 3, insetTop: 3, insetBottom: 3}),
        Plot.text(sources, {y: "origine", x: (d) => d.voix / 1e6, text: (d) => (d.voix < 5e4 ? "< 0,1" : (d.voix / 1e6).toLocaleString("fr-FR", {maximumFractionDigits: 1})), dx: 5, textAnchor: "start", fill: "currentColor", fontSize: 11})
      ]
    })}
  </div>`;
})}</div>`);
```

## Comment c'est calculé

<p class="explication">Pour chaque commune, on connaît la part des inscrits qui a voté pour chaque candidat, voté blanc ou nul, ou s'est abstenue, au 1er et au 2nd tour. On cherche les taux de report qui expliquent le mieux le 2nd tour à partir du 1er, pour toutes les communes à la fois (moindres carrés pondérés par le nombre d'inscrits). Chaque taux est compris entre 0 et 100 %, et les reports de chaque électorat totalisent 100 %. Les fourchettes viennent de ${r.n_bootstrap} recalculs, en tirant les départements au hasard. La méthode a été vérifiée sur des données fabriquées dont les reports étaient connus (voir <code>tests/test_reports.py</code>). Les petits électorats, comme ceux des candidats sous 2 %, sont estimés avec beaucoup moins de précision.</p>
