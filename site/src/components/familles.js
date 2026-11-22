// Couleurs des familles politiques (palette validée le 22/11/2026).
// Le classement des candidats / listes / nuances se fait dans pipeline/familles.py.
// En mode sombre, les couleurs les plus foncées sont éclaircies pour rester visibles.

export const FAMILLES = {
  exg:  {nom: "Extrême gauche",          clair: "#8E1F1F", sombre: "#B84444"},
  pcf:  {nom: "PCF",                     clair: "#C4122F", sombre: "#D93A52"},
  lfi:  {nom: "LFI / Front de gauche",   clair: "#E2483D", sombre: "#E2483D"},
  ug:   {nom: "Union de la gauche",      clair: "#C2185B", sombre: "#D63B78"},
  ps:   {nom: "PS",                      clair: "#F48FB1", sombre: "#F48FB1"},
  dvg:  {nom: "Divers gauche",           clair: "#F7C5C9", sombre: "#F7C5C9"},
  eco:  {nom: "Écologistes",             clair: "#2E9E44", sombre: "#3DB356"},
  ens:  {nom: "Ensemble / Renaissance",  clair: "#F2B705", sombre: "#F2B705"},
  mdm:  {nom: "MoDem",                   clair: "#F28C28", sombre: "#F28C28"},
  udi:  {nom: "UDI / centre droit",      clair: "#3FA9E0", sombre: "#3FA9E0"},
  dvc:  {nom: "Divers centre",           clair: "#F6DD8A", sombre: "#F6DD8A"},
  lr:   {nom: "LR / UMP",                clair: "#1F5FBF", sombre: "#4A86E0"},
  dvd:  {nom: "Divers droite",           clair: "#8DB3E2", sombre: "#8DB3E2"},
  souv: {nom: "Souverainistes",          clair: "#5C6BC0", sombre: "#7E8BD6"},
  rn:   {nom: "RN / FN",                 clair: "#0B2560", sombre: "#2F4FA0"},
  uxd:  {nom: "Alliés du RN",            clair: "#3D4F8A", sombre: "#6A79B8"},
  rec:  {nom: "Reconquête",              clair: "#4A3326", sombre: "#8A6A55"},
  reg:  {nom: "Régionalistes",           clair: "#B8875A", sombre: "#C99B70"},
  div:  {nom: "Divers et autres",        clair: "#A3A3A3", sombre: "#8A8A8A"}
};

/** Couleur d'une famille selon le thème (dark = variable réactive d'Observable Framework). */
export function couleur(famille, dark = false) {
  const f = FAMILLES[famille] ?? FAMILLES.div;
  return dark ? f.sombre : f.clair;
}
