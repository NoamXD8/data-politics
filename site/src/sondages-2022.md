---
title: Sondages 2022
toc: false
---

```js
import {fmtPct} from "./components/elections.js";
import {couleur} from "./components/familles.js";

const s = FileAttachment("data/sondages-2022.json").json();
```

# Les sondages de la présidentielle 2022

<p class="explication">Tous les sondages d'intentions de vote publiés de janvier 2022 au dernier jour autorisé avant chaque tour, comparés aux résultats officiels. Un sondage n'est pas une prédiction : c'est une photographie de l'opinion à un moment donné, avec une marge d'erreur de l'ordre de 2 à 3 points pour les principaux candidats.</p>

```js
if (!s) display(html`<div class="note">Les sondages ne sont pas encore préparés : lance <code>python -m pipeline.sondages</code> à la racine du projet, puis relance le site.</div>`);
```

```js
// Mise en forme commune
const pts = (x) => `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(x).toLocaleString("fr-FR", {minimumFractionDigits: 1, maximumFractionDigits: 1})} pt`;
const jour = (d) => new Date(d + "T12:00:00");
const dateCourte = (d) => jour(d).toLocaleDateString("fr-FR", {day: "numeric", month: "long"});
const axeDate = (d) => d.toLocaleDateString("fr-FR", {day: "numeric", month: "short"});
function lignesDe(tour) {
  return tour.sondages.flatMap((p) => Object.entries(p.scores).map(([cle, pct]) => ({
    cle, pct, date: jour(p.fin), institut: p.institut, echantillon: p.echantillon,
    nom: tour.candidats[cle].nom, famille: tour.candidats[cle].famille
  })));
}
const ordre = (tour) => Object.entries(tour.candidats).sort((a, b) => b[1].pct - a[1].pct).map(([cle]) => cle);
```

## Le premier tour, sondage après sondage

```js
const t1 = s.t1;
const cles1 = ordre(t1);
const choisis = view(Inputs.checkbox(cles1, {
  label: "Candidats",
  value: cles1.slice(0, 6),
  format: (k) => t1.candidats[k].nom.replace(/ [A-ZÀ-Ý-]+( [A-ZÀ-Ý-]+)*$/, (m) => m.charAt(0) + m.slice(1).toLowerCase().replace(/(^|[ -])\p{L}/gu, (x) => x.toUpperCase()))
}));
```

```js
const l1 = lignesDe(t1).filter((d) => choisis.includes(d.cle));
const res1 = choisis.map((cle) => ({cle, ...t1.candidats[cle], date: jour(t1.vote)}));
const domaine = choisis.map((k) => t1.candidats[k].nom);
display(Plot.plot({
  subtitle: "Intentions de vote au 1er tour (%). Chaque point est un sondage, la courbe est la moyenne mobile. Les losanges sont les résultats du 10 avril.",
  width,
  height: 460,
  marginRight: 20,
  x: {label: null, type: "time", tickFormat: axeDate},
  y: {label: null, grid: true, tickFormat: (d) => `${d} %`},
  color: {domain: domaine, range: choisis.map((k) => couleur(t1.candidats[k].famille, dark)), legend: true},
  marks: [
    Plot.ruleX([jour(t1.vote)], {stroke: "currentColor", strokeOpacity: 0.3, strokeDasharray: "4 3"}),
    Plot.text([jour(t1.vote)], {x: (d) => d, frameAnchor: "top", text: () => "1er tour", dy: -4, textAnchor: "end", dx: -4, fill: "currentColor", fillOpacity: 0.6}),
    Plot.dot(l1, {x: "date", y: "pct", fill: "nom", r: 1.8, fillOpacity: 0.25}),
    Plot.line(l1, Plot.windowY({k: 25, reduce: "mean"}, {x: "date", y: "pct", stroke: "nom", strokeWidth: 2.2, sort: "date"})),
    Plot.dot(res1, {x: "date", y: "pct", fill: "nom", symbol: "diamond2", r: 6, stroke: "var(--theme-background)", strokeWidth: 1.5}),
    Plot.tip(l1, Plot.pointer({x: "date", y: "pct", title: (d) => `${d.nom} · ${d.pct.toLocaleString("fr-FR")} %\n${d.institut}, ${d.date.toLocaleDateString("fr-FR")} (${d.echantillon} personnes)`}))
  ]
}));
```

## L'écart entre les derniers sondages et le résultat

```js
const ecarts = cles1.map((cle) => {
  const c = t1.candidats[cle];
  const sondage = t1.moyenne_finale[cle];
  return {cle, nom: c.nom, famille: c.famille, resultat: c.pct, sondage, ecart: c.pct - sondage};
}).filter((d) => d.sondage != null);
const plusSurpris = [...ecarts].sort((a, b) => Math.abs(b.ecart) - Math.abs(a.ecart))[0];
```

<p class="explication">Moyenne du dernier sondage publié par chaque institut avant l'interdiction de publication (${dateCourte(t1.dernier_jour)}), comparée au résultat. Le plus grand écart concerne <strong>${plusSurpris.nom}</strong> : ${fmtPct(plusSurpris.sondage / 100)} dans les derniers sondages, ${fmtPct(plusSurpris.resultat / 100)} dans les urnes (${pts(plusSurpris.ecart)}).</p>

```js
display(Plot.plot({
  subtitle: "La flèche va du dernier sondage (moyenne des instituts) au résultat réel",
  width,
  height: 40 + ecarts.length * 30,
  marginLeft: 170,
  marginRight: 90,
  x: {label: null, grid: true, tickFormat: (d) => `${d} %`, nice: true},
  y: {label: null, domain: ecarts.map((d) => d.nom)},
  marks: [
    Plot.arrow(ecarts, {y: "nom", x1: "sondage", x2: "resultat", stroke: (d) => couleur(d.famille, dark), strokeWidth: 2, headLength: 7}),
    Plot.dot(ecarts, {y: "nom", x: "sondage", r: 3.5, fill: "var(--theme-background)", stroke: (d) => couleur(d.famille, dark)}),
    Plot.text(ecarts, {y: "nom", x: (d) => Math.max(d.sondage, d.resultat), text: (d) => pts(d.ecart), dx: 10, textAnchor: "start", fill: "currentColor"}),
    Plot.tip(ecarts, Plot.pointerY({y: "nom", x: "resultat", title: (d) => `${d.nom}\nDerniers sondages : ${fmtPct(d.sondage / 100)}\nRésultat : ${fmtPct(d.resultat / 100)}\nÉcart : ${pts(d.ecart)}`}))
  ]
}));
```

## Quel institut a le mieux prédit le 1er tour ?

<p class="explication">Pour chaque institut, on prend son dernier sondage publié et on calcule l'erreur moyenne : l'écart moyen, en points, entre ses intentions de vote et le résultat, sur les ${cles1.length} candidats. Plus le chiffre est bas, plus le sondage était proche du résultat. Attention : un institut dont le dernier sondage est plus ancien est comparé à une opinion qui a eu plus de temps pour bouger.</p>

```js
const inst1 = t1.instituts;
display(Plot.plot({
  width: Math.min(width, 720),
  height: 40 + inst1.length * 28,
  marginLeft: 150,
  marginRight: 60,
  x: {label: null, axis: null},
  y: {label: null, domain: inst1.map((d) => d.institut)},
  marks: [
    Plot.barX(inst1, {y: "institut", x: "erreur_moyenne", fill: (d, i) => (i === 0 ? "var(--series-1)" : "var(--theme-foreground-faint)"), rx2: 4, insetTop: 4, insetBottom: 4}),
    Plot.text(inst1, {y: "institut", x: "erreur_moyenne", text: (d) => `${d.erreur_moyenne.toLocaleString("fr-FR", {minimumFractionDigits: 2})} pt`, dx: 6, textAnchor: "start", fill: "currentColor"}),
    Plot.tip(inst1, Plot.pointerY({y: "institut", x: "erreur_moyenne", title: (d) => `${d.institut}, sondage terminé le ${dateCourte(d.fin)} (${d.echantillon} personnes)\nErreur moyenne : ${d.erreur_moyenne.toLocaleString("fr-FR")} pt\nPlus gros écart : ${d.pire.nom} (${pts(-d.pire.ecart)} dans les urnes)`}))
  ]
}));
```

```js
display(Inputs.table(inst1.map((d, i) => ({rang: i + 1, institut: d.institut, fin: d.fin, echantillon: d.echantillon, erreur: d.erreur_moyenne, pire: `${d.pire.nom} (${pts(-d.pire.ecart)})`})), {
  header: {rang: "Rang", institut: "Institut", fin: "Dernier sondage", echantillon: "Échantillon", erreur: "Erreur moyenne (pt)", pire: "Plus gros écart (résultat − sondage)"},
  format: {fin: dateCourte, echantillon: (x) => x.toLocaleString("fr-FR"), erreur: (x) => x.toLocaleString("fr-FR", {minimumFractionDigits: 2})},
  layout: "auto"
}));
```

## Le second tour

```js
const t2 = s.t2;
const cles2 = ordre(t2);
const l2 = lignesDe(t2).filter((d) => d.cle === cles2[0]);
const gagnant = t2.candidats[cles2[0]];
display(Plot.plot({
  subtitle: `Intentions de vote pour ${gagnant.nom} au 2nd tour (%). La ligne horizontale est son résultat du ${dateCourte(t2.vote)} (${fmtPct(gagnant.pct / 100)}).`,
  width,
  height: 320,
  x: {label: null, type: "time", tickFormat: axeDate},
  y: {label: null, grid: true, domain: [45, 70], tickFormat: (d) => `${d} %`},
  marks: [
    Plot.ruleY([50], {stroke: "currentColor", strokeOpacity: 0.4}),
    Plot.ruleY([gagnant.pct], {stroke: couleur(gagnant.famille, dark), strokeDasharray: "5 3"}),
    Plot.dot(l2, {x: "date", y: "pct", fill: couleur(gagnant.famille, dark), r: 2, fillOpacity: 0.35}),
    Plot.line(l2, Plot.windowY({k: 15, reduce: "mean"}, {x: "date", y: "pct", stroke: couleur(gagnant.famille, dark), strokeWidth: 2.2, sort: "date"})),
    Plot.tip(l2, Plot.pointer({x: "date", y: "pct", title: (d) => `${d.nom} · ${d.pct.toLocaleString("fr-FR")} %\n${d.institut}, ${d.date.toLocaleDateString("fr-FR")}`}))
  ]
}));
```

```js
display(t2.instituts.length ? Inputs.table(t2.instituts.map((d, i) => ({rang: i + 1, institut: d.institut, fin: d.fin, sondage: d.ecarts[cles2[0]] + gagnant.pct, erreur: d.erreur_moyenne})), {
  header: {rang: "Rang", institut: "Institut", fin: "Dernier sondage", sondage: `${gagnant.nom} dans le sondage (%)`, erreur: "Erreur (pt)"},
  format: {fin: dateCourte, sondage: (x) => x.toLocaleString("fr-FR", {maximumFractionDigits: 1}), erreur: (x) => x.toLocaleString("fr-FR", {minimumFractionDigits: 2})},
  layout: "auto"
}) : html``);
```

## Sources

```js
display(html`<p class="explication">Sondages : compilation <a href="${s.source.url}" target="_blank" rel="noopener">NSPPolls</a> (licence ${s.source.licence}), qui recense les sondages publiés et leurs notices. Liste de référence : <a href="${s.source.reference}" target="_blank" rel="noopener">Wikipédia, Liste de sondages sur l'élection présidentielle française de 2022</a>. Résultats : Ministère de l'Intérieur. Pour un même sondage testant plusieurs hypothèses de candidatures, on garde celle qui correspond aux candidats réellement présents.</p>`);
```
