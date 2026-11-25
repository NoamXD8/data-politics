---
toc: false
---

```js
import {fmtPct, fmtNombre, court, slug, partDe, rangDe, raccourcir} from "../components/elections.js";
import {couleur, FAMILLES} from "../components/familles.js";
import {carteScore} from "../components/carte.js";
import {puces} from "../components/choix.js";

const elections = FileAttachment("../data/elections.json").json();
const france = FileAttachment("../data/france.json").json();
const departements = FileAttachment("../data/departements.json").json();
const contours = FileAttachment("../data/departements-contours.geojson").json();
```

```js
// Toutes les données de la page viennent des résultats officiels : même gabarit pour chaque candidat.
const s = observable.params.slug;
const presidentielles = elections.filter((e) => e.type === "pres");
const presences = presidentielles
  .map((e) => ({e, part: partDe(e, france.france[e.id], s), rang: rangDe(e, france.france[e.id], s)}))
  .filter((d) => d.part != null);
const anneeRef = presences.filter((d) => d.e.tour === 1).at(-1).e.annee;
const ref = presences.find((d) => d.e.annee === anneeRef && d.e.tour === 1);
const iRef = ref.e.noms.findIndex((n) => slug(n) === s);
const nom = ref.e.noms[iRef];
const famille = ref.e.familles[iRef];
const teinte = couleur(famille, dark);
const nomsDep = new Map(departements.map((d) => [d.code, d.nom]));
const voix = (d) => france.france[d.e.id][5 + d.e.noms.findIndex((n) => slug(n) === s)];
const t2 = presences.find((d) => d.e.annee === anneeRef && d.e.tour === 2);
```

<p class="explication"><a href="../">← Accueil</a></p>

# ${nom}

<p class="explication"><span style="display:inline-block;width:.8em;height:.8em;border-radius:2px;background:${teinte};margin-right:.4em"></span>${FAMILLES[famille].nom} · candidat·e à l'élection présidentielle ${anneeRef}. Toutes les pages candidats suivent le même modèle et ne contiennent que des résultats officiels.</p>

<div class="chiffres">
  <div class="card"><div class="valeur">${fmtPct(ref.part)}</div><div class="legende">1er tour ${anneeRef} · ${ref.rang}${ref.rang === 1 ? "er" : "e"} sur ${ref.e.noms.filter((n) => n !== "Autres").length}</div></div>
  <div class="card"><div class="valeur">${fmtNombre(voix(ref))}</div><div class="legende">voix au 1er tour</div></div>
  <div class="card"><div class="valeur">${t2 ? fmtPct(t2.part) : "–"}</div><div class="legende">${t2 ? `2nd tour ${anneeRef}` : "pas qualifié·e pour le 2nd tour"}</div></div>
</div>

## Ses résultats aux présidentielles

```js
display(Plot.plot({
  subtitle: "Part des suffrages exprimés, France entière",
  width: Math.min(width, 140 * presences.length + 60),
  height: 260,
  marginBottom: 40,
  x: {label: null, domain: presences.map((d) => court(d.e))},
  y: {axis: null, domain: [0, Math.max(0.3, ...presences.map((d) => d.part)) * 1.15]},
  marks: [
    Plot.barY(presences, {x: (d) => court(d.e), y: "part", fill: teinte, rx1: 4, insetLeft: 12, insetRight: 12,
      tip: {format: {x: false, y: false}, channels: {Scrutin: (d) => d.e.libelle, Score: (d) => fmtPct(d.part), Rang: (d) => `${d.rang}${d.rang === 1 ? "er" : "e"}`}}}),
    Plot.text(presences, {x: (d) => court(d.e), y: "part", text: (d) => fmtPct(d.part), dy: -10, fill: "currentColor"}),
    Plot.ruleY([0])
  ]
}));
```

## Où ${nom} a fait ses meilleurs scores

```js
const tours = presences.filter((d) => d.e.annee === anneeRef);
const choix = view(puces(tours, {format: (d) => (d.e.tour === 1 ? "1er tour" : "2nd tour"), value: tours[0]}));
```

```js
const valeurs = new Map(departements.map((d) => [d.code, partDe(choix.e, france.departements[d.code]?.[choix.e.id], s)]));
const classement = [...valeurs].filter(([, p]) => p != null).map(([code, part]) => ({code, nom: nomsDep.get(code), part})).sort((a, b) => b.part - a.part);
display(carteScore({contours, noms: nomsDep, valeurs, teinte, dark, width: Math.min(width, 700)}));
```

```js
const liste = (items) => html`<ol style="margin:.25rem 0;padding-left:1.4rem">${items.map((d) => html`<li><a href="../departement/${d.code}">${d.nom}</a> · <strong>${fmtPct(d.part)}</strong></li>`)}</ol>`;
display(html`<div class="grid grid-cols-2">
  <div class="card"><h3>Meilleurs départements</h3>${liste(classement.slice(0, 5))}</div>
  <div class="card"><h3>Départements les plus difficiles</h3>${liste(classement.slice(-5).reverse())}</div>
</div>`);
```

```js
// Évolution depuis la présidentielle précédente (1er tour), si le ou la candidat·e s'était déjà présenté·e
const avant = presences.filter((d) => d.e.tour === 1 && d.e.annee < anneeRef).at(-1);
let evolution = null;
if (avant) {
  const deltas = departements.map((d) => {
    const a = partDe(avant.e, france.departements[d.code]?.[avant.e.id], s);
    const b = partDe(ref.e, france.departements[d.code]?.[ref.e.id], s);
    return a == null || b == null ? null : {code: d.code, nom: d.nom, delta: b - a};
  }).filter(Boolean).sort((x, y) => y.delta - x.delta);
  evolution = {avant, deltas, national: ref.part - avant.part};
}
const pts = (x) => `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toLocaleString("fr-FR", {maximumFractionDigits: 1, minimumFractionDigits: 1})} pt`;
```

```js
const listePts = (items) => html`<ol style="margin:.25rem 0;padding-left:1.4rem">${items.map((d) => html`<li><a href="../departement/${d.code}">${d.nom}</a> · <strong>${pts(d.delta)}</strong></li>`)}</ol>`;
display(evolution
  ? html`<h2>Évolution depuis ${evolution.avant.e.annee}</h2>
    <p class="explication">Au 1er tour, ${nom} passe de ${fmtPct(evolution.avant.part)} en ${evolution.avant.e.annee} à ${fmtPct(ref.part)} en ${anneeRef}, soit <strong>${pts(evolution.national)}</strong> au niveau national. Écart en points de pourcentage, département par département :</p>
    <div class="grid grid-cols-2">
      <div class="card"><h3>Plus forte progression</h3>${listePts(evolution.deltas.slice(0, 5))}</div>
      <div class="card"><h3>Plus fort recul</h3>${listePts(evolution.deltas.slice(-5).reverse())}</div>
    </div>`
  : html`<h2>Évolution</h2><p class="explication">Première candidature à la présidentielle depuis ${presidentielles[0].annee} : pas de comparaison possible avec l'élection précédente.</p>`);
```

## Les autres candidat·es de ${anneeRef}

```js
display(html`<div style="display:flex;flex-wrap:wrap;gap:.5rem">${ref.e.noms.map((n, i) => [n, ref.e.familles[i]]).filter(([n]) => n !== "Autres" && slug(n) !== s).map(([n, f]) =>
  html`<a href="./${slug(n)}" style="display:inline-flex;align-items:center;gap:.4em;padding:.3rem .7rem;border:1px solid var(--theme-foreground-faintest);border-radius:999px;text-decoration:none;color:inherit;font-size:.9rem"><span style="width:.7em;height:.7em;border-radius:2px;background:${couleur(f, dark)}"></span>${n}</a>`)}</div>`);
```
