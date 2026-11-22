---
title: Méthodologie
---

# Méthodologie

Ce site est **indépendant et non partisan**. Cette page explique d'où viennent les chiffres et quels choix ont été faits, pour que chacun puisse les vérifier.

## D'où viennent les données ?

Tous les résultats viennent du **Ministère de l'Intérieur**, rassemblés par data.gouv.fr dans le jeu de données [« Données des élections agrégées »](https://www.data.gouv.fr/datasets/donnees-des-elections-agregees) (Licence Ouverte). Les résultats y sont publiés **par bureau de vote** ; ce site les additionne pour obtenir les résultats par commune, par département et pour la France entière.

Scrutins couverts : présidentielles, législatives et européennes depuis 2012.

## Comment lire les chiffres ?

- **Participation** = votants ÷ inscrits.
- **Score d'un candidat** = ses voix ÷ suffrages exprimés. Les exprimés excluent les votes blancs et nuls : c'est la règle officielle de calcul des résultats.
- **« Autres »** regroupe les candidats ou listes qui font moins de 1 % au niveau national (et au-delà des 10 premiers). Cela concerne surtout les européennes, où il y a souvent plus de 30 listes.

## Choix et limites

- **Législatives :** les candidats sont différents dans chaque circonscription, donc les résultats sont regroupés par **nuance politique**, c'est-à-dire l'étiquette attribuée par le Ministère de l'Intérieur à chaque candidat. Les codes de nuance changent d'une élection à l'autre.
- **Seconds tours de législatives :** il n'y a pas de second tour partout (élu dès le 1er tour, ou pas de candidat qualifié), d'où des communes sans résultats.
- **Communes nouvelles et fusions :** une commune qui a fusionné peut apparaître sous un code différent selon l'année.
- **Pas de couleurs de partis :** tous les candidats sont affichés de la même couleur, triés par score, pour ne favoriser personne visuellement.

## Le code

Le pipeline de données (Python) et le site (Observable Framework) sont ouverts. Toute erreur signalée sera corrigée et documentée ici.
