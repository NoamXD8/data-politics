---
toc: false
---

```js
import {fmtPct, slug} from "../components/elections.js";
import {couleur, FAMILLES} from "../components/familles.js";
import {dateFr, groupeDe, portrait, historique, graphiqueHistorique} from "../components/candidats.js";

const fiches = FileAttachment("../data/candidats-2027.json").json();
const photos = FileAttachment("../data/photos.json").json();
const elections = FileAttachment("../data/elections.json").json();
const france = FileAttachment("../data/france.json").json();
```

```js
// Même gabarit pour chaque candidature : identité, parcours, programme, résultats passés.
const c = fiches.candidats.find((d) => slug(d.nom) === observable.params.slug);
const teinte = couleur(c.famille, dark);
const h = historique(c.nom, elections, france);
const derniere = elections.filter((e) => e.type === "pres" && e.tour === 1).at(-1);
const aUnePage = derniere.noms.some((n) => slug(n) === slug(c.nom));
```

<p class="explication"><a href="../candidats-2027">← Toutes les candidatures 2027</a></p>

```js
display(html`<div style="display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap;margin:1rem 0">
  ${portrait(c, dark, 110, photos[c.nom])}
  <div style="min-width:220px;flex:1">
    <h1 style="margin:0">${c.nom}</h1>
    <div style="color:var(--theme-foreground-muted)">${c.parti} · ${groupeDe(c)}</div>
    <div style="margin-top:.3rem">${c.fonction}</div>
    <div style="font-size:.9rem;margin-top:.3rem">Candidature annoncée : ${dateFr(c.declaration)}</div>
  </div>
</div>
${c.note ? html`<div class="note">${c.note}</div>` : ""}`);
```

## Parcours

```js
if (c.parcours?.length) display(html`<ul>${c.parcours.map((p) => html`<li><strong>${p.periode}</strong> · ${p.fonction}</li>`)}</ul>`);
display(c.bio
  ? html`<p style="max-width:640px">${c.bio}</p>`
  : html`<p class="explication">Pas encore de biographie détaillée : seule la fonction déclarée par la source est indiquée.</p>`);
```

## Programme

```js
const themes = [...new Set((c.programme ?? []).map((p) => p.theme))];
display(themes.length
  ? html`<p class="explication">Propositions publiées par le ou la candidat·e, résumées et sourcées.</p>
    ${themes.map((t) => html`<h3>${t}</h3><ul>${c.programme.filter((p) => p.theme === t).map((p) =>
      html`<li>${p.proposition}${p.source ? html` <a href="${p.source}" target="_blank" rel="noopener" style="font-size:.8rem">(source)</a>` : ""}</li>`)}</ul>`)}`
  : html`<p class="explication">Programme pas encore référencé ici.${c.site ? html` Site de campagne : <a href="${c.site}" target="_blank" rel="noopener">${c.site}</a>` : ""}</p>`);
```

## Résultats aux présidentielles précédentes

```js
display(h.length
  ? html`${graphiqueHistorique(h, teinte, width)}
    ${aUnePage ? html`<p><a href="../candidat/${slug(c.nom)}">Voir la carte de ses scores et ses meilleurs départements en ${derniere.annee} →</a></p>` : ""}`
  : html`<p class="explication">Aucune candidature à une présidentielle depuis ${elections.find((e) => e.type === "pres").annee} dans les données officielles.</p>`);
```

<p class="explication" style="margin-top:2rem">Fiche mise à jour le ${dateFr(fiches.maj)}. <a href="../methodologie">Méthodologie et sources</a></p>
