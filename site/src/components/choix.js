// Sélecteurs du site : tous les choix se font avec des pastilles cliquables (règle de design du projet).
// Compatibles avec view() d'Observable Framework : propriété `value` + événement "input".
import {html} from "npm:htl";

/** Texte foncé ou blanc selon la clarté d'une couleur hexadécimale. */
function texteSur(couleur) {
  const m = /^#?([0-9a-f]{6})$/i.exec(couleur ?? "");
  if (!m) return "#fff";
  const [r, g, b] = m[1].match(/\w\w/g).map((h) => parseInt(h, 16) / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.55 ? "#1b1b1b" : "#fff";
}

/**
 * Pastilles de choix.
 * @param options     liste des valeurs possibles (objets, chaînes, nombres…)
 * @param value       valeur de départ (un élément, ou un tableau si multiple)
 * @param multiple    plusieurs choix possibles (sinon un seul)
 * @param format      libellé principal d'une option
 * @param detail      petit texte à droite (ex. un score), facultatif
 * @param couleur     couleur d'une option (hex) ; sinon couleur d'accent du site
 * @param groupe      range les options en lignes titrées (ex. type d'élection), facultatif
 * @param label       titre au-dessus des pastilles, facultatif
 * @param raccourcis  boutons rapides pour le choix multiple : [{label, valeur: [options]}]
 * @param min         nombre minimum d'options cochées en choix multiple (1 par défaut)
 */
export function puces(options, {value, multiple = false, format = String, detail, couleur, groupe, label, raccourcis = [], min = 1} = {}) {
  const choisis = new Set(multiple ? (value ?? []) : value === undefined ? [options[0]] : [value]);
  const bouton = (o, i) => {
    const c = couleur?.(o);
    return html`<button type="button" class="puce" data-i="${i}" style="${c ? `--c:${c};--t:${texteSur(c)}` : ""}">
      <span class="n">${format(o)}</span>${detail ? html`<span class="s">${detail(o)}</span>` : ""}
    </button>`;
  };
  let corps;
  if (groupe) {
    const groupes = [...new Set(options.map(groupe))];
    corps = html`<div class="groupes">${groupes.map((g) => html`<div class="groupe"><div class="titre-groupe">${g}</div>
      <div class="puces">${options.map((o, i) => (groupe(o) === g ? bouton(o, i) : null)).filter(Boolean)}</div></div>`)}</div>`;
  } else {
    corps = html`<div class="puces">${options.map(bouton)}</div>`;
  }
  const racine = html`<div class="choix">
    ${label ? html`<div class="etiquette">${label}</div>` : ""}
    ${raccourcis.length ? html`<div class="raccourcis">${raccourcis.map((r, j) => html`<button type="button" data-r="${j}">${r.label}</button>`)}</div>` : ""}
    ${corps}
  </div>`;
  const rafraichir = () => {
    for (const b of racine.querySelectorAll(".puce")) b.classList.toggle("on", choisis.has(options[+b.dataset.i]));
    racine.value = multiple ? options.filter((o) => choisis.has(o)) : [...choisis][0];
  };
  racine.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.r !== undefined) {
      choisis.clear();
      raccourcis[+b.dataset.r].valeur.forEach((o) => choisis.add(o));
    } else {
      const o = options[+b.dataset.i];
      if (!multiple) {
        if (choisis.has(o)) return;
        choisis.clear();
        choisis.add(o);
      } else if (choisis.has(o)) {
        if (choisis.size > min) choisis.delete(o);
      } else choisis.add(o);
    }
    rafraichir();
    racine.dispatchEvent(new Event("input", {bubbles: true}));
  });
  rafraichir();
  return racine;
}

/**
 * Recherche dans une longue liste (ex. les communes d'un département) : un champ de saisie,
 * des pastilles de suggestions, et la sélection en cours affichée comme une pastille active.
 * @param tous  option « tout » affichée quand rien n'est choisi (ex. « Tout le département »)
 */
export function recherche(options, {value, format = String, placeholder = "Rechercher…", tous, label, max = 8} = {}) {
  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[-'’]/g, " ").toLowerCase();
  const index = options.map((o) => norm(format(o)));
  let choisi = value ?? tous;
  const champ = html`<input type="search" class="champ" placeholder="${placeholder}" autocomplete="off">`;
  const actuel = html`<div class="puces"></div>`;
  const suggestions = html`<div class="puces suggestions"></div>`;
  const racine = html`<div class="choix">${label ? html`<div class="etiquette">${label}</div>` : ""}${actuel}${champ}${suggestions}</div>`;
  const rafraichir = () => {
    actuel.replaceChildren(html`<button type="button" class="puce on" data-a="1"><span class="n">${format(choisi)}</span>${
      choisi !== tous && tous !== undefined ? html`<span class="s" title="Revenir à « ${format(tous)} »">✕</span>` : ""}</button>`);
    racine.value = choisi;
  };
  const proposer = () => {
    const q = norm(champ.value.trim());
    if (q.length < 2) return suggestions.replaceChildren();
    const trouves = options.map((o, i) => [o, index[i]]).filter(([, t]) => t.includes(q))
      .sort((a, b) => (a[1].startsWith(q) ? 0 : 1) - (b[1].startsWith(q) ? 0 : 1) || a[1].localeCompare(b[1])).slice(0, max);
    suggestions.replaceChildren(...(trouves.length
      ? trouves.map(([o]) => html`<button type="button" class="puce" data-i="${options.indexOf(o)}"><span class="n">${format(o)}</span></button>`)
      : [html`<span class="vide">Aucun résultat</span>`]));
  };
  champ.addEventListener("input", (e) => { e.stopPropagation(); proposer(); });
  racine.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.a) {
      if (choisi === tous || tous === undefined) return;
      choisi = tous;
    } else choisi = options[+b.dataset.i];
    champ.value = "";
    suggestions.replaceChildren();
    rafraichir();
    racine.dispatchEvent(new Event("input", {bubbles: true}));
  });
  rafraichir();
  return racine;
}

/** Champ de saisie arrondi, assorti aux pastilles (pour les recherches libres). */
export function champ({placeholder = "Rechercher…", label} = {}) {
  const input = html`<input type="search" class="champ" placeholder="${placeholder}" autocomplete="off">`;
  if (!label) return input;
  const racine = html`<div class="choix"><div class="etiquette">${label}</div>${input}</div>`;
  racine.value = "";
  input.addEventListener("input", (e) => { e.stopPropagation(); racine.value = input.value; racine.dispatchEvent(new Event("input", {bubbles: true})); });
  return racine;
}

const TYPES = {pres: "Présidentielles", legi: "Législatives", euro: "Européennes", muni: "Municipales", regi: "Régionales", dpmt: "Départementales"};

/** Choix d'un scrutin : une ligne par type d'élection, une pastille par année et par tour. */
export function choixScrutin(elections, {value, label = "Scrutin"} = {}) {
  return puces(elections, {
    value, label,
    groupe: (e) => TYPES[e.type] ?? e.type,
    format: (e) => (e.type === "euro" ? `${e.annee}` : `${e.annee} · ${e.tour === 1 ? "1er" : "2nd"} tour`)
  });
}

/** Choix du tour (1er / 2nd). */
export function choixTour({value = 1, label} = {}) {
  return puces([1, 2], {value, label, format: (t) => (t === 1 ? "1er tour" : "2nd tour")});
}
