---
title: Sondages
toc: false
---

```js
import {fmtPct} from "./components/elections.js";
import {couleur} from "./components/familles.js";
import {puces} from "./components/choix.js";

const s = FileAttachment("data/sondages.json").json();
```

# Les sondages de la présidentielle

```js
if (!s) display(html`<div class="note">Les sondages ne sont pas encore préparés : lance <code>python -m pipeline.sondages</code> à la racine du projet, puis relance le site.</div>`);
```

```js
// Élection affichée : mémorisée dans l'URL (?annee=2017) pour pouvoir partager le lien
const depuisUrl = new URLSearchParams(location.search).get("annee");
const annees = s.annees;
const statut = (a) => (s[a].statut === "en_cours" ? "en cours" : `${s[a].t1.sondages.length} sondages`);
```

```js
const annee = view(puces(annees, {value: annees.includes(depuisUrl) ? depuisUrl : annees[0], label: "Élection",
  format: (a) => `Présidentielle ${a}`, detail: statut}));
```

```js
{
  const url = new URL(location.href);
  url.searchParams.set("annee", annee);
  history.replaceState(null, "", url);
}
const e = s[annee];
const enCours = e.statut === "en_cours";
```

```js
display(html`<p class="explication">${enCours
  ? html`Tous les sondages d'intentions de vote pour le 1er tour du ${jour(e.t1.vote).toLocaleDateString("fr-FR", {day: "numeric", month: "long", year: "numeric"})}, depuis ${jour(e.t1.sondages[0].fin).toLocaleDateString("fr-FR", {month: "long", year: "numeric"})}. Les candidatures ne sont pas encore officielles : les instituts testent plusieurs hypothèses. Un sondage n'est pas une prédiction : c'est une photographie de l'opinion à un moment donné, avec une marge d'erreur de l'ordre de 2 à 3 points pour les principaux candidats.`
  : html`Tous les sondages d'intentions de vote publiés jusqu'au dernier jour autorisé avant ${e.t2 ? "chaque tour" : "le 1er tour"}, comparés aux résultats officiels. Un sondage n'est pas une prédiction : c'est une photographie de l'opinion à un moment donné, avec une marge d'erreur de l'ordre de 2 à 3 points pour les principaux candidats.`}</p>`);
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
const derniereMoy = (tour, k) => tour.tendances[k]?.at(-1)?.moy;
const ordre = (tour) => Object.keys(tour.candidats)
  .filter((k) => tour.candidats[k].pct != null || tour.tendances[k]?.length)
  .sort((a, b) => (tour.candidats[b].pct ?? derniereMoy(tour, b)) - (tour.candidats[a].pct ?? derniereMoy(tour, a)));
```

```js
display(html`<h2>Le premier tour, sondage après sondage</h2>`);
const t1 = e.t1;
const cles1 = ordre(t1);
// « Emmanuel MACRON » → « Macron », « Marine LE PEN » → « Le Pen »
const nomDeFamille = (nom) => (nom.match(/(?:\s[A-ZÀ-Ý'-]{2,})+$/)?.[0] ?? nom).trim().toLowerCase()
  .replace(/(^|[\s-])(\p{L})/gu, (m, sep, l) => sep + l.toUpperCase());
```

```js
const choisis = view(puces(cles1, {multiple: true, value: cles1.slice(0, 5),
  format: (k) => nomDeFamille(t1.candidats[k].nom),
  detail: (k) => `${(t1.candidats[k].pct ?? derniereMoy(t1, k)).toLocaleString("fr-FR", {minimumFractionDigits: 1, maximumFractionDigits: 1})} %`,
  couleur: (k) => couleur(t1.candidats[k].famille, dark),
  raccourcis: [{label: "Top 5", valeur: cles1.slice(0, 5)}, {label: "Tous", valeur: cles1}]}));
```

```js
display(graphiqueSondages(t1, choisis, {titre: `Sondages de l'élection présidentielle ${annee} — 1er tour`,
  sousTitre: enCours ? `Moyenne lissée des sondages, tous instituts confondus. Dernier sondage : ${dateCourte(t1.dernier_jour)}.` : "Moyenne lissée des sondages, tous instituts confondus. Les losanges sont les résultats officiels.",
  source: e.source.nom}));
```

```js
// Infobulle maison : trait vertical, un point par courbe et une carte avec tous les candidats du jour
function infobulle(svg, {T, R, fins, vote, aVenir = false, coul, initiales, pctTxt}) {
  const x = svg.scale("x"), y = svg.scale("y");
  const parDate = d3.group(T, (d) => +d.d);
  const dates = [...parDate.keys()].sort(d3.ascending);
  const derniers = new Map(fins.map((f) => [f.nom, f.v]));
  const calque = d3.select(svg).append("g").attr("pointer-events", "none").style("display", "none");
  const trait = calque.append("line").attr("stroke", "currentColor").attr("stroke-opacity", 0.35).attr("stroke-dasharray", "2 3")
    .attr("y1", y.apply(y.domain[1])).attr("y2", y.apply(y.domain[0]));
  const bulle = html`<div class="bulle-sondage" hidden></div>`;
  const jourFr = (d) => {
    const t = d.toLocaleDateString("fr-FR", {weekday: "long", day: "numeric", month: "long", year: "numeric"});
    return t.charAt(0).toUpperCase() + t.slice(1);
  };
  const ligne = (n, valeur, detail) => `<div class="ligne"><span class="pastille" style="background:${coul(n)}">${initiales(n)}</span>
    <span class="nom">${n}</span><span class="valeur" style="color:${coul(n)}">${valeur}</span>${detail ? `<span class="detail">${detail}</span>` : ""}</div>`;
  const xMin = x.apply(dates[0]), xVote = x.apply(+vote);
  function montrer(event) {
    const [mx, my] = d3.pointer(event, svg);
    if (mx < xMin - 10 || mx > xVote + (aVenir ? 6 : 24)) return cacher();
    let px, lignes, titre;
    if (!aVenir && mx > xVote - 10) {
      // Sur les résultats
      px = xVote;
      lignes = [...R].sort((a, b) => b.pct - a.pct);
      titre = `Résultat du ${vote.toLocaleDateString("fr-FR", {day: "numeric", month: "long", year: "numeric"})}`;
      bulle.innerHTML = `<div class="titre">${titre}</div>` + lignes.map((r) => ligne(r.nom, pctTxt(r.pct),
        derniers.has(r.nom) ? `sondages : ${pctTxt(derniers.get(r.nom))}` : "")).join("");
      calque.selectAll("circle").data(lignes).join("circle").attr("cx", px).attr("cy", (r) => y.apply(r.pct)).attr("r", 5)
        .attr("fill", (r) => coul(r.nom)).attr("stroke", "var(--theme-background-alt)").attr("stroke-width", 2);
    } else {
      const t = x.invert(mx);
      const i = d3.bisectCenter(dates, +t);
      const d = dates[i];
      px = x.apply(d);
      lignes = [...parDate.get(d)].sort((a, b) => b.moy - a.moy);
      bulle.innerHTML = `<div class="titre">${jourFr(new Date(d))}</div><div class="sous">moyenne des sondages</div>` +
        lignes.map((l) => ligne(l.nom, pctTxt(l.moy), `${l.bas.toLocaleString("fr-FR", {maximumFractionDigits: 1})} – ${l.haut.toLocaleString("fr-FR", {maximumFractionDigits: 1})}`)).join("");
      calque.selectAll("circle").data(lignes).join("circle").attr("cx", px).attr("cy", (l) => y.apply(l.moy)).attr("r", 5)
        .attr("fill", (l) => coul(l.nom)).attr("stroke", "var(--theme-background-alt)").attr("stroke-width", 2);
    }
    calque.style("display", null);
    trait.attr("x1", px).attr("x2", px);
    bulle.hidden = false;
    const largeur = svg.clientWidth || +svg.getAttribute("width");
    const bw = bulle.offsetWidth, bh = bulle.offsetHeight;
    const gauche = px + 18 + bw > largeur ? px - 18 - bw : px + 18;
    bulle.style.left = `${Math.max(0, gauche)}px`;
    bulle.style.top = `${Math.max(0, Math.min(my - bh / 2, (svg.clientHeight || 500) - bh))}px`;
  }
  function cacher() {
    calque.style("display", "none");
    bulle.hidden = true;
  }
  svg.addEventListener("pointermove", montrer);
  svg.addEventListener("pointerleave", cacher);
  return bulle;
}
```

```js
// Graphique façon « moyenne de sondages » : courbes lissées + bande d'incertitude, sondages en points,
// résultats en losanges, étiquettes à droite décalées pour ne pas se chevaucher.
function graphiqueSondages(tour, cles, {titre, sousTitre, yMin = 0, reperes = [], debut = null, source}) {
  // Élection à venir : pas de résultat, les étiquettes se placent au bout des courbes
  const aVenir = cles.every((k) => tour.candidats[k].pct == null);
  const vote = jour(aVenir ? tour.dernier_jour : tour.vote);
  const coul = (k) => couleur(tour.candidats[k].famille, dark);
  const nom = (k) => nomDeFamille(tour.candidats[k].nom);
  // Une courbe est coupée en segments là où il manque des jours (trop peu de sondages autour)
  const T = cles.flatMap((k) => {
    let seg = 0, prec = null;
    return (tour.tendances[k] ?? []).map((p) => {
      const d = jour(p.date);
      if (prec && d - prec > 3 * 864e5) seg++;
      prec = d;
      return {...p, d, k, nom: nom(k), seg: `${k}-${seg}`};
    });
  });
  const depuis = debut ? jour(debut) : null;
  if (depuis) T.splice(0, T.length, ...T.filter((d) => d.d >= depuis));
  const P = lignesDe(tour).filter((d) => cles.includes(d.cle) && (!depuis || d.date >= depuis)).map((d) => ({...d, nom: nom(d.cle)}));
  const R = aVenir ? [] : cles.map((k) => ({k, nom: nom(k), d: vote, pct: tour.candidats[k].pct}));
  const fins = cles.map((k) => {const t = tour.tendances[k]; const f = t?.at(-1); return f && {k, nom: nom(k), d: jour(f.date), v: f.moy};}).filter(Boolean);

  const etroit = width < 640;
  const largeur = width - 42; // marge intérieure de la carte
  const hauteur = etroit ? 430 : 520, haut = 36, bas = 34;
  const yMax = Math.ceil((Math.max(...T.map((d) => d.haut), ...R.map((d) => d.pct)) + 2) / 5) * 5;
  // Étiquettes : on part de la valeur finale et on écarte les voisines d'au moins 26 px
  const ecart = ((etroit ? 30 : 26) / (hauteur - haut - bas)) * (yMax - yMin);
  const etiquettes = (aVenir ? fins : R.map((r) => ({...r, v: r.pct}))).map((r) => ({...r})).sort((a, b) => b.v - a.v);
  etiquettes.forEach((e, i) => (e.y = i === 0 ? Math.min(e.v, yMax - ecart / 2) : Math.min(e.v, etiquettes[i - 1].y - ecart)));
  for (let i = etiquettes.length - 1; i >= 0; i--) if (etiquettes[i].y < yMin + ecart / 2) etiquettes[i].y = i === etiquettes.length - 1 ? yMin + ecart / 2 : etiquettes[i + 1].y + ecart;
  const xEtiquette = new Date(+vote + (etroit ? 12 : 6) * 864e5);
  const periodeCourte = vote - d3.min(T, (d) => d.d) < 150 * 864e5;
  const initiales = (n) => n.split(/\s+/).map((m) => m[0]).join("").slice(0, 2);
  const pctTxt = (v) => `${v.toLocaleString("fr-FR", {minimumFractionDigits: 1, maximumFractionDigits: 1})} %`;

  const plot = Plot.plot({
    width: largeur,
    height: hauteur,
    marginTop: haut,
    marginBottom: bas,
    marginRight: etroit ? 128 : 190,
    marginLeft: 30,
    style: {background: "transparent"},
    x: {type: "time", label: null, ticks: etroit ? 3 : periodeCourte ? 5 : 6,
      tickFormat: (d) => d.toLocaleDateString("fr-FR", periodeCourte ? {day: "numeric", month: "short"} : etroit ? {month: "short", year: "2-digit"} : {day: "numeric", month: "short", year: "numeric"})},
    y: {domain: [yMin, yMax], grid: true, label: "Score (%)", labelAnchor: "top", labelArrow: "none", ticks: 7},
    color: {domain: cles.map(nom), range: cles.map(coul)},
    marks: [
      aVenir ? null : Plot.ruleX([vote], {stroke: "currentColor", strokeOpacity: 0.35, strokeDasharray: "3 4"}),
      // Repères supplémentaires (ex. date du 1er tour sur le graphique du 2nd tour)
      Plot.ruleX(reperes, {x: (r) => jour(r.date), stroke: "currentColor", strokeOpacity: 0.35, strokeDasharray: "3 4"}),
      Plot.text(reperes, {x: (r) => jour(r.date), frameAnchor: "top", dy: -14, dx: -4, text: "texte", fontWeight: 600, textAnchor: "end", fill: "currentColor"}),
      aVenir ? null : Plot.text([vote], {x: (d) => d, frameAnchor: "top", dy: -14, dx: reperes.length ? 4 : 0, text: () => `Résultat du ${vote.toLocaleDateString("fr-FR", {day: "numeric", month: "long"})}`, fontWeight: 600, textAnchor: reperes.length ? "start" : "end", fill: "currentColor"}),
      Plot.areaY(T, {x: "d", y1: "bas", y2: "haut", z: "seg", fill: "nom", fillOpacity: 0.16, curve: "basis"}),
      Plot.dot(P, {x: "date", y: "pct", fill: "nom", r: 1.6, fillOpacity: 0.35}),
      Plot.line(T, {x: "d", y: "moy", z: "seg", stroke: "nom", strokeWidth: 3.2, curve: "basis"}),
      Plot.dot(R, {x: "d", y: "pct", fill: "nom", symbol: "diamond2", r: 6, stroke: "var(--theme-background-alt)", strokeWidth: 1.5}),
      Plot.dot(fins, {x: "d", y: "v", fill: "nom", r: 4.5, stroke: "var(--theme-background-alt)", strokeWidth: 1.5}),
      Plot.link(etiquettes, {x1: "d", y1: "v", x2: () => xEtiquette, y2: "y", stroke: "nom", strokeWidth: 1.2, strokeOpacity: 0.8, insetLeft: 0}),
      Plot.dot(etiquettes, {x: () => xEtiquette, y: "y", fill: "nom", r: 10, dx: 14}),
      Plot.text(etiquettes, {x: () => xEtiquette, y: "y", text: (d) => initiales(d.nom), dx: 14, fill: "white", fontWeight: 700, fontSize: 9}),
      Plot.text(etiquettes, {x: () => xEtiquette, y: "y", text: (d) => (etroit ? `${pctTxt(d.v)}\n${d.nom}` : `${pctTxt(d.v)}  ${d.nom}`), dx: 30, textAnchor: "start", fill: "nom", fontWeight: 700, fontSize: etroit ? 11 : 13, lineHeight: 1.1}),
    ]
  });
  const bulle = infobulle(plot, {T, R, fins, vote, aVenir, coul: (n) => coul(cles.find((k) => nom(k) === n)), initiales, pctTxt});
  return html`<div class="carte-sondages">
    <div class="titre">${titre}</div>
    <div class="sous-titre">${sousTitre}</div>
    <div style="position:relative">${plot}${bulle}</div>
    <div class="pied">Sources : sondages publiés (compilation ${source})${aVenir ? "" : ", résultats du Ministère de l'Intérieur"} · Data Politics</div>
  </div>`;
}
```

```js
const ecarts = enCours ? [] : cles1.map((cle) => {
  const c = t1.candidats[cle];
  const sondage = t1.moyenne_finale[cle];
  return {cle, nom: c.nom, famille: c.famille, resultat: c.pct, sondage, ecart: c.pct - sondage};
}).filter((d) => d.sondage != null);
const plusSurpris = [...ecarts].sort((a, b) => Math.abs(b.ecart) - Math.abs(a.ecart))[0];
```

```js
if (ecarts.length) {
display(html`<h2>L'écart entre les derniers sondages et le résultat</h2>
<p class="explication">Moyenne du dernier sondage publié par chaque institut avant l'interdiction de publication (${dateCourte(t1.dernier_jour)}), comparée au résultat. Le plus grand écart concerne <strong>${plusSurpris.nom}</strong> : ${fmtPct(plusSurpris.sondage / 100)} dans les derniers sondages, ${fmtPct(plusSurpris.resultat / 100)} dans les urnes (${pts(plusSurpris.ecart)}).</p>`);
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
} else display(document.createComment("")); // sans display, Framework laisse l'ancien contenu
```

```js
const inst1 = t1.instituts;
if (inst1.length) {
display(html`<h2>Quel institut a le mieux prédit le 1er tour ?</h2>
<p class="explication">Pour chaque institut, on prend son dernier sondage publié et on calcule l'erreur moyenne : l'écart moyen, en points, entre ses intentions de vote et le résultat, sur les ${cles1.length} candidats. Plus le chiffre est bas, plus le sondage était proche du résultat. Attention : un institut dont le dernier sondage est plus ancien est comparé à une opinion qui a eu plus de temps pour bouger.</p>`);
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
    Plot.tip(inst1, Plot.pointerY({y: "institut", x: "erreur_moyenne", title: (d) => `${d.institut}, sondage terminé le ${dateCourte(d.fin)}${d.echantillon ? ` (${d.echantillon} personnes)` : ""}\nErreur moyenne : ${d.erreur_moyenne.toLocaleString("fr-FR")} pt\nPlus gros écart : ${d.pire.nom} (${pts(-d.pire.ecart)} dans les urnes)`}))
  ]
}));
display(Inputs.table(inst1.map((d, i) => ({rang: i + 1, institut: d.institut, fin: d.fin, echantillon: d.echantillon, erreur: d.erreur_moyenne, pire: `${d.pire.nom} (${pts(-d.pire.ecart)})`})), {
  header: {rang: "Rang", institut: "Institut", fin: "Dernier sondage", echantillon: "Échantillon", erreur: "Erreur moyenne (pt)", pire: "Plus gros écart (résultat − sondage)"},
  format: {fin: dateCourte, echantillon: (x) => (x ? x.toLocaleString("fr-FR") : "–"), erreur: (x) => x.toLocaleString("fr-FR", {minimumFractionDigits: 2})},
  layout: "auto"
}));
} else display(document.createComment("")); // sans display, Framework laisse l'ancien contenu
```

```js
// Élection à venir : liste des derniers sondages avec un lien vers leur notice officielle
if (enCours) {
  display(html`<h2>Les derniers sondages</h2><p class="explication">Chaque sondage publié doit être déposé auprès de la Commission des sondages, avec sa notice technique (échantillon, méthode, questions posées). Score moyen de chaque personnalité sur les hypothèses testées par le sondage.</p>`);
  const derniers = [...t1.sondages].reverse();
  const principaux = cles1.slice(0, 6);
  display(Inputs.table(derniers.map((p) => ({fin: p.fin, institut: p.institut, echantillon: p.echantillon, ...Object.fromEntries(principaux.map((k) => [k, p.scores[k]])), source: p.source})), {
    columns: ["fin", "institut", "echantillon", ...principaux, "source"],
    header: {fin: "Fin du terrain", institut: "Institut", echantillon: "Échantillon", source: "Notice", ...Object.fromEntries(principaux.map((k) => [k, nomDeFamille(t1.candidats[k].nom)]))},
    format: {fin: dateCourte, echantillon: (x) => x.toLocaleString("fr-FR"), source: (u) => (u ? html`<a href="${u}" target="_blank" rel="noopener">voir</a>` : ""),
      ...Object.fromEntries(principaux.map((k) => [k, (x) => (x == null ? "–" : `${x.toLocaleString("fr-FR", {maximumFractionDigits: 1})} %`)]))},
    layout: "auto", rows: 12
  }));
} else display(document.createComment("")); // sans display, Framework laisse l'ancien contenu
```

```js
const t2 = e.t2;
const cles2 = t2 ? ordre(t2) : [];
if (t2) {
  display(html`<h2>Le second tour</h2>`);
  display(graphiqueSondages(t2, cles2, {titre: `Sondages de l'élection présidentielle ${annee} — 2nd tour`, sousTitre: "Intentions de vote en duel, moyenne lissée. Les losanges sont les résultats officiels.", yMin: 30,
    reperes: [{date: t1.vote, texte: "1er tour"}], debut: t2.debut_graphique, source: (e.source_t2 ?? e.source).nom}));
} else if (!enCours) {
  display(html`<p class="note">Pas de série ouverte de sondages du 2nd tour pour ${annee} : seul le 1er tour est présenté.</p>`);
} else display(document.createComment("")); // sans display, Framework laisse l'ancien contenu
const gagnant = t2?.candidats[cles2[0]];
```

```js
if (t2?.instituts.length) display(Inputs.table(t2.instituts.map((d, i) => ({rang: i + 1, institut: d.institut, fin: d.fin, sondage: d.ecarts[cles2[0]] + gagnant.pct, erreur: d.erreur_moyenne})), {
  header: {rang: "Rang", institut: "Institut", fin: "Dernier sondage", sondage: `${gagnant.nom} dans le sondage (%)`, erreur: "Erreur (pt)"},
  format: {fin: dateCourte, sondage: (x) => x.toLocaleString("fr-FR", {maximumFractionDigits: 1}), erreur: (x) => x.toLocaleString("fr-FR", {minimumFractionDigits: 2})},
  layout: "auto"
}));
else display(document.createComment(""));
```

## Sources

```js
const lien = (src) => html`<a href="${src.url}" target="_blank" rel="noopener">${src.nom}</a> (${src.licence})`;
display(html`<p class="explication">Sondages ${annee} : compilation ${lien(e.source)}${e.source_t2 ? html` pour le 1er tour, ${lien(e.source_t2)} pour le 2nd` : ""}, qui recense les sondages publiés et leurs notices.${e.source.reference ? html` Liste de référence : <a href="${e.source.reference}" target="_blank" rel="noopener">Wikipédia, Liste de sondages sur l'élection présidentielle française de ${annee}</a>.` : ""}${enCours ? "" : " Résultats : Ministère de l'Intérieur."} ${e.methode}</p>`);
```
