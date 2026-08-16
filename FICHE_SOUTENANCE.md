# Fiche de soutenance — SkyData Family-Aware Federated Coordination

## Le récit en 60 secondes

Dans SkyData, chaque réplica d'une donnée est un agent autonome ; les réplicas
d'une même donnée forment une famille qui doit se DISPERSER (une famille
regroupée meurt d'une seule panne). Nous avons montré trois choses, dans un
simulateur contrôlé, après avoir audité et corrigé notre propre implémentation :

1. **La conscience familiale est le facteur décisif** : égoïste = regroupement
   et collisions (2.1/famille) ; family-aware = dispersion doublée, 0 collision.
2. **La coordination par SkyWorker est une garantie de stabilité** dont la
   valeur croît avec la vue des agents : équivalente au naïf quand la vue est
   étroite (résultat nul assumé), décisive quand la vue s'élargit (20/20 seeds
   à d=8), toujours sans collision, et 4x moins chère en coût de migration.
3. **Le Federated Learning est réel et quantifié** : la qualité des harbours
   est inconnue, chaque famille l'estime par observations locales bruitées, et
   le SkyWorker agrège les estimations (FedAvg pondéré) sans centraliser les
   données. La fédération divise par ~2 le temps de découverte collective
   (erreur<0.05 en 7.8 tours vs 14.1 en local ; meilleur sur 20/20 seeds au
   tour 10).

## Les chiffres à connaître par cœur

| Quoi | Valeur |
|---|---|
| Selfish : dispersion / collisions | 0.305 / 2.13 |
| Family-aware : dispersion / collisions | ~0.62 / 0.00 |
| d=8 : Coordonné bat Naïf | 20/20 seeds |
| d=all : Naïf s'effondre | 0.570, collisions 0.44 |
| Coût migration : Naïf vs Coordonné | 154 vs 36 (~4x) |
| Prix : messages SKW | ~2 500 |
| FL : erreur<0.05 | 7.8 tours (fédéré) vs 14.1 (local) |
| FL : placement final | 0.682 (≈ oracle 0.690) |

## Questions probables et réponses

**« Où est le Federated Learning ? »**
Section 4.3/5.3 : estimation fédérée de la qualité des harbours. Données
locales = observations bruitées d'un réplica ; modèle = estimation par famille ;
agrégation = SkyWorker, moyenne pondérée par compteurs d'observations ; rien de
brut n'est centralisé. Bénéfice mesuré : découverte 2x plus rapide. Le SKW joue
exactement le rôle que Mauffret lui donne (« gather models to aggregate them »).

**« Pourquoi le fédéré n'est-il pas meilleur que le local à la fin ? »**
Avec assez de temps, une famille apprend seule — les deux convergent vers
l'oracle. La valeur de la fédération est la VITESSE de découverte, ce qui compte
dans un système dynamique où les conditions changent. C'est un résultat honnête,
pas une faiblesse.

**« Votre coordination n'apporte presque rien vs le naïf ? »**
À d=4, oui — résultat nul que nous assumons (notre première lecture était
faussée par des poids inégaux ; nous l'avons corrigé nous-mêmes). Mais à vue
large, le naïf s'effondre (collisions de re-synchronisation) et le coordonné
reste stable : 20/20 seeds à d=8. Plus le bonus inattendu : 4x moins de coût de
migration. La coordination est une assurance de stabilité.

**« Pourquoi un simulateur et pas JADE ? »**
Pas encore d'accès. Le simulateur isole proprement les variables (une seule
chose change à la fois, seeds appariés). Le portage JADE est l'étape suivante
— c'est notre demande du jour.

**« Qu'est-ce qui est de vous ? »**
Le recentrage familial, le SKW coordinateur temporaire par réservation, la
relecture critique interne qui a corrigé le score et les poids, la couche
d'estimation fédérée, et toutes les expériences/ablations. Les baselines
(Random, Power-of-Choice) viennent de l'encadrant.

**« Limites ? »**
Simulateur maison (preuve de concept) ; couche message grossière ; qualité des
harbours statique (le dynamique amplifierait la valeur du FL — future work) ;
poids de score fixés à la main.

## La phrase de conclusion

« La conscience familiale fait le gros du travail ; la coordination garantit la
stabilité et économise le mouvement ; la fédération achète la vitesse de la
connaissance. Le tout sans aucune autorité centrale permanente — fidèle à
SkyData. »
