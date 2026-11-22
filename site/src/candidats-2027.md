---
title: Candidats 2027
toc: false
---

```js
import {fmtPct, slug, partDe, rangDe, normaliser} from "./components/elections.js";
import {couleur, FAMILLES} from "./components/familles.js";

const fiches = FileAttachment("data/candidats-2027.json").json();
const elections = FileAttachment("data/elections.json").json();
const france = FileAttachment("data/france.json").json();
```

```js
// Regroupement politique repris de la source (République 2027), pas d'un classement maison
const GROUPES = ["Extrême gauche", "Gauche", "Écologistes", "Centre", "Droite", "Extrême droite", "Divers"];
const groupeDe = (c) => c.groupe ?? ({
  exg: "Extrême gauche", pcf: "Gauche", lfi: "Gauche", ug: "Gauche", ps: "Gauche", dvg: "Gauche",
  eco: "Écologistes", ens: "Centre", mdm: "Centre", udi: "Centre", dvc: "Centre",
  lr: "Droite", dvd: "Droite", souv: c.nom === "Florian Philippot" ? "Extrême droite" : "Droite",
  rn: "Extrême droite", uxd: "Extrême droite", rec: "Extrême droite"
}[c.famille] ?? "Divers");

const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
function dateFr(d) {
  if (!d) return "date non précisée";
  const [a, m, j] = d.split("-");
  if (!m) return a;
  return `${j ? `${+j === 1 ? "1er" : +j} ` : ""}${MOIS[+m - 1]} ${a}`;
}
const nomDeFamille = (nom) => nom.split(" ").slice(1).join(" ");

// Résultats aux présidentielles précédentes, calculés depuis les données officielles
const presidentielles = elections.filter((e) => e.type === "pres");
const derniere = presidentielles.filter((e) => e.tour === 1).at(-1);
const pages2022 = new Set(derniere.noms.map(slug));
function historique(nom) {
  const s = slug(nom);
  return presidentielles
    .map((e) => ({e, part: partDe(e, france.france[e.id], s), rang: rangDe(e, france.france[e.id], s)}))
    .filter((d) => d.part != null);
}
```

# Les candidat·es à la présidentielle 2027

<p class="explication">${fiches.regle} Liste arrêtée au ${dateFr(fiches.maj)} : <strong>${fiches.candidats.length} candidatures annoncées</strong>. Publication de la liste officielle le ${dateFr(fiches.liste_officielle)}, premier tour le 18 avril 2027.</p>

```js
const requete = view(Inputs.text({placeholder: "Chercher un nom ou un parti…", autocomplete: "off"}));
```

```js
const q = normaliser(requete.trim());
const visibles = fiches.candidats.filter((c) => !q || normaliser(`${c.nom} ${c.parti}`).includes(q));

function fiche(c) {
  const h = historique(c.nom);
  return html`<div class="card" style="margin:0;border-left:5px solid ${couleur(c.famille, dark)}">
    <h3 style="margin:0;font-size:1.15rem;font-weight:600;color:var(--theme-foreground)">${c.nom}</h3>
    <div style="color:var(--theme-foreground-muted);font-size:.9rem">${c.parti} · ${c.fonction}</div>
    <div style="font-size:.85rem;margin-top:.3rem">Candidature annoncée : ${dateFr(c.declaration)}</div>
    ${c.note ? html`<div style="font-size:.85rem;margin-top:.4rem;padding:.4rem .6rem;border-radius:6px;background:var(--theme-foreground-faintest)">${c.note}</div>` : ""}
    ${c.bio ? html`<p style="font-size:.9rem;margin:.6rem 0 0">${c.bio}</p>` : ""}
    ${h.length ? html`<div style="margin-top:.6rem;font-size:.85rem"><strong>Présidentielles précédentes</strong>
      <div style="display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.3rem">${h.map((d) => html`<span style="padding:.15rem .5rem;border:1px solid var(--theme-foreground-faintest);border-radius:999px">${d.e.annee} ${d.e.tour === 1 ? "T1" : "T2"} · ${fmtPct(d.part)} (${d.rang}${d.rang === 1 ? "er" : "e"})</span>`)}</div>
      ${pages2022.has(slug(c.nom)) ? html`<a href="./candidat/${slug(c.nom)}" style="display:inline-block;margin-top:.4rem">Ses résultats en détail →</a>` : ""}
    </div>` : ""}
  </div>`;
}

display(visibles.length === 0 ? html`<p class="explication">Aucun résultat.</p>` : html`${GROUPES.map((g) => {
  const liste = visibles.filter((c) => groupeDe(c) === g).sort((a, b) => nomDeFamille(a.nom).localeCompare(nomDeFamille(b.nom), "fr"));
  return liste.length ? html`<h2>${g} <small style="font-weight:400;color:var(--theme-foreground-muted)">(${liste.length})</small></h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.75rem">${liste.map(fiche)}</div>` : "";
})}`);
```

## Sources

<p class="explication">Les candidatures et fonctions viennent des sources ci-dessous. Les biographies se limitent aux mandats et fonctions publics. Les résultats aux présidentielles précédentes sont calculés à partir des données officielles du Ministère de l'Intérieur. Une erreur ? Elle sera corrigée et datée.</p>

```js
display(html`<ul>${fiches.sources.map((s) => html`<li><a href="${s.url}" target="_blank" rel="noopener">${s.titre}</a></li>`)}</ul>`);
```
