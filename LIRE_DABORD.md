# LIRE D'ABORD — Projet SkyData (version finale v2, alignée)

Projet : Federated Learning in Multi-Agent Systems · Terrain : SkyData
Encadrant : Dr. Etienne Mauffret

## Les 3 résultats du projet (tous les livrables racontent la même histoire)

1. **La conscience familiale est le facteur décisif** : égoïste = regroupement
   + collisions ; family-aware = dispersion doublée, 0 collision.
2. **La coordination SkyWorker = une garantie de stabilité** dont la valeur
   croît avec la vue des agents (52/60 seeds à d=8 ; à vue étroite, résultat
   nul assumé) + coût de migration divisé par 4.
3. **Le Federated Learning divise par 2 le temps de découverte** : la qualité
   des harbours est inconnue, les familles l'estiment localement, le SkyWorker
   agrège (FedAvg pondéré) sans centraliser — erreur<0.05 en 8 tours vs 14.

## Les fichiers

- `Papier.pdf` / `.docx` — le papier (v3 : résultats corrigés, section FL
  réelle, positionnement gossip/participation partielle, 14 références)
- `Survey_FL_MAS.pdf` / `.docx` — l'état de l'art (v2, section intersection
  enrichie)
- `Presentation.pptx` — le PowerPoint (nouveaux chiffres, récit à 3 résultats)
- `SkyData_Notebook_Complet.ipynb` — simulateur v2 + expériences + démo,
  testé de bout en bout (Colab : Importer → Tout exécuter, ~5-8 min)
- `Interface_demo.html` — la démo seule (double-clic) ; `_rose` = version fun
- `RESULTS_v2.md` — tous les chiffres ; `FICHE_SOUTENANCE.md` — le récit,
  les chiffres à connaître, les réponses aux questions pièges
- `README_GITHUB.md` — à mettre comme README du repo
- `code/` — skydata_core.py + run_all.py (v2) + les 2 scripts d'ablation
- `figures/` — les 2 figures du papier

## À faire pour GitHub (répartition suggérée dans le README)

1. Remplacer le README du repo par `README_GITHUB.md`
2. Pousser `code/*` dans `src/`, le notebook dans `notebook/`,
   `Papier.pdf` + `Survey_FL_MAS.pdf` dans `paper/`, `RESULTS_v2.md` et
   `FICHE_SOUTENANCE.md` à la racine
3. Mettre à jour la démo Netlify si vous alignez les paramètres JS

## Rappels

- Preuve de concept dans NOTRE simulateur — pas une validation JADE. On le dit.
- Chacun doit pouvoir expliquer sa partie : la fiche de soutenance sert à ça.
- Ajoutez les noms du groupe sur le papier, le survey et le PPT.
