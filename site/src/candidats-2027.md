---
title: Candidats 2027
toc: false
---

```js
import {fmtPct, slug, partDe, rangDe, normaliser} from "./components/elections.js";
import {couleur, FAMILLES} from "./components/familles.js";
import {GROUPES, groupeDe, dateFr, nomDeFamille, portrait, historique} from "./components/candidats.js";
import {champ} from "./components/choix.js";

const fiches = FileAttachment("data/candidats-2027.json").json();
const photos = FileAttachment("data/photos.json").json();
const elections = FileAttachment("data/elections.json").json();
const france = FileAttachment("data/france.json").json();
```

```js
const derniere = elections.filter((e) => e.type === "pres" && e.tour === 1).at(-1);
```

# Les candidat·es à la présidentielle 2027

<p class="explication">${fiches.regle} Liste arrêtée au ${dateFr(fiches.maj)} : <strong>${fiches.candidats.length} candidatures annoncées</strong>. Publication de la liste officielle le ${dateFr(fiches.liste_officielle)}, premier tour le 18 avril 2027.</p>

```js
const requete = view(champ({placeholder: "Chercher un nom ou un parti…"}));
```

```js
const q = normaliser(requete.trim());
const visibles = fiches.candidats.filter((c) => !q || normaliser(`${c.nom} ${c.parti}`).includes(q));

function fiche(c) {
  const h = historique(c.nom, elections, france);
  const lien = `./candidat-2027/${slug(c.nom)}`;
  return html`<a href="${lien}" class="card fiche" style="margin:0;display:flex;flex-direction:column;text-decoration:none;color:inherit;border-left:5px solid ${couleur(c.famille, dark)}">
    <div style="display:flex;gap:.8rem;align-items:center">
      ${portrait(c, dark, 56, photos[c.nom])}
      <div>
        <h3 style="margin:0;font-size:1.15rem;font-weight:600;color:var(--theme-foreground)">${c.nom}</h3>
        <div style="color:var(--theme-foreground-muted);font-size:.9rem">${c.parti}</div>
      </div>
    </div>
    <div style="font-size:.9rem;margin-top:.5rem">${c.fonction}</div>
    <div style="font-size:.8rem;color:var(--theme-foreground-muted);margin-top:.2rem">Candidature annoncée : ${dateFr(c.declaration)}</div>
    ${c.note ? html`<div style="font-size:.8rem;margin-top:.4rem;padding:.3rem .5rem;border-radius:6px;background:var(--theme-foreground-faintest)">${c.note}</div>` : ""}
    ${h.length ? html`<div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.5rem;font-size:.75rem">${h.filter((d) => d.e.tour === 1).map((d) => html`<span style="padding:.1rem .45rem;border:1px solid var(--theme-foreground-faintest);border-radius:999px">${d.e.annee} · ${fmtPct(d.part)}</span>`)}</div>` : ""}
    <div style="margin-top:auto;padding-top:.6rem;font-size:.85rem;color:var(--theme-foreground-focus)">Voir la fiche →</div>
  </a>`;
}

display(visibles.length === 0 ? html`<p class="explication">Aucun résultat.</p>` : html`${GROUPES.map((g) => {
  const liste = visibles.filter((c) => groupeDe(c) === g).sort((a, b) => nomDeFamille(a.nom).localeCompare(nomDeFamille(b.nom), "fr"));
  return liste.length ? html`<h2>${g} <small style="font-weight:400;color:var(--theme-foreground-muted)">(${liste.length})</small></h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.75rem">${liste.map(fiche)}</div>` : "";
})}`);
```

## Candidatures retirées ou non retenues

```js
display(html`<ul>${fiches.retraits.sort((a, b) => b.date.localeCompare(a.date)).map((r) => html`<li><strong>${r.nom}</strong> (${r.parti}) · ${r.motif}, ${dateFr(r.date)}</li>`)}</ul>`);
```

## Sources

<p class="explication">${fiches.regroupement} Les candidatures et fonctions viennent des sources ci-dessous. Les biographies se limitent aux mandats et fonctions publics. Les résultats aux présidentielles précédentes sont calculés à partir des données officielles du Ministère de l'Intérieur. Une erreur ? Elle sera corrigée et datée.</p>

```js
display(html`<ul>${fiches.sources.map((s) => html`<li><a href="${s.url}" target="_blank" rel="noopener">${s.titre}</a></li>`)}</ul>`);
```
