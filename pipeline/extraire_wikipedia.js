// Extraction des tableaux de sondages Wikipédia → data/sondages/wikipedia-AAAA-tN.csv
//
// Wikipédia n'est pas toujours joignable depuis un script et sa mise en page change souvent :
// les tableaux sont donc extraits une fois, à la main, puis versionnés (licence CC BY-SA 4.0).
//
// Mode d'emploi : ouvrir la page « Liste de sondages sur l'élection présidentielle française de AAAA »,
// coller ce fichier dans la console du navigateur, puis appeler par exemple :
//   copy(extraire([[0, "2017"], [2, "2017"]], ["Emmanuel Macron", "Marine Le Pen"]))
// (indices des tableaux « wikitable » de la page, avec l'année à utiliser quand la date n'en a pas).
// `tableaux()` liste les tableaux de la page avec leur titre et leurs colonnes.
//
// Tableaux utilisés (novembre 2026) :
//   2017 2nd tour : 0 (entre les deux tours) et 2 (« Sondages entre Emmanuel Macron et Marine Le Pen »)
//   2012 1er tour : 0 à 3 (avril, mars, février, janvier 2012)
//   2012 2nd tour : 10 (2012) et 11 (2011, année « 2011 »)

const MOIS = {janvier: 1, "février": 2, mars: 3, avril: 4, mai: 5, juin: 6, juillet: 7, "août": 8, septembre: 9, octobre: 10, novembre: 11, "décembre": 12};

// Tableau HTML → grille de textes, en dépliant les cellules fusionnées (rowspan / colspan)
function grille(t) {
  const g = [];
  [...t.rows].forEach((r, i) => {
    g[i] = g[i] || [];
    let j = 0;
    [...r.cells].forEach((c) => {
      while (g[i][j] !== undefined) j++;
      const x = c.cloneNode(true);
      x.querySelectorAll("sup,style,.mw-ref").forEach((s) => s.remove());
      const txt = x.textContent.replace(/\s+/g, " ").trim();
      for (let a = 0; a < (c.rowSpan || 1); a++)
        for (let b = 0; b < (c.colSpan || 1); b++) {
          g[i + a] = g[i + a] || [];
          g[i + a][j + b] = txt;
        }
      j += c.colSpan || 1;
    });
  });
  return g;
}

// « 18 au 21 avril 2017 », « 30 avril - 1 mai », « 2-5 mai » → date de fin au format AAAA-MM-JJ
function finDate(s, annee) {
  const re = /(\d{1,2})(?:er)?\s*(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)(?:\s+(\d{4}))?/g;
  let m, dernier = null;
  while ((m = re.exec(s))) dernier = m;
  if (!dernier) return null;
  const y = dernier[3] || (s.match(/\d{4}/) || [annee])[0];
  return `${y}-${String(MOIS[dernier[2]]).padStart(2, "0")}-${String(dernier[1]).padStart(2, "0")}`;
}

// « 60,5 % » → 60.5 ; « < 0,5 % » → 0.25 ; « – » → vide
function valeur(s) {
  if (!s) return "";
  s = s.replace(/\[.*?\]/g, "").trim();
  if (/^<\s*0,5/.test(s)) return "0.25";
  const m = s.match(/^(\d+(?:[,.]\d+)?)\s*%?$/);
  return m ? m[1].replace(",", ".") : "";
}

const nom = (h) => h.replace(/\[.*?\]/g, "").replace(/\s*\(.*$/, "").trim();
const wikitables = () => [...document.querySelectorAll("table.wikitable")];

function tableaux() {
  let titre = null;
  const out = [];
  document.querySelectorAll("h2,h3,h4,table.wikitable").forEach((el) => {
    if (el.tagName !== "TABLE") return void (titre = el.textContent.trim());
    out.push(`${out.length} · ${titre} · ${grille(el)[1]?.map(nom).join(" | ")}`);
  });
  return out.join("\n");
}

function extraire(tables, candidats) {
  const lignes = [["fin", "institut", "echantillon", ...candidats].join(";")];
  for (const [i, annee] of tables) {
    const g = grille(wikitables()[i]);
    const entete = g[1].map(nom);
    const iEchantillon = g[0].findIndex((h) => /chantillon/.test(h));
    const colonnes = candidats.map((c) => entete.indexOf(c));
    for (const r of g.slice(2)) {
      // lignes d'événements (cellule fusionnée sur toute la largeur) et résultats officiels ignorés
      if (r.length < entete.length || new Set(r).size < 3 || /^Résultats|tour \[/.test(r[0])) continue;
      const fin = finDate(r[1], annee);
      if (!fin) continue;
      const vals = colonnes.map((j) => (j < 0 ? "" : valeur(r[j])));
      if (vals.filter(Boolean).length < 2) continue;
      const echantillon = iEchantillon < 0 ? "" : (r[iEchantillon] || "").replace(/\D/g, "");
      lignes.push([fin, r[0].replace(/\s*\[archive\]/, "").replace(/[«»]/g, "").trim(), echantillon, ...vals].join(";"));
    }
  }
  return lignes.join("\n");
}
