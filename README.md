# Replenishment Budget Lab

**Quels produits réapprovisionner lorsque le budget ne suffit pas ?** Un outil Python d'aide à la décision supply chain qui choisit des quantités par lots, respecte le budget et les limites fournisseurs, puis explique les ruptures restantes.

Projet **supply chain + optimisation + analyse de scénarios**. Fonctionnement local, Python standard uniquement, aucune clé API. Les données et pénalités sont entièrement fictives.

## Démonstration en une minute

Python 3.10+ ; vérifié avec Python 3.14.3 sous Windows.

```sh
git clone https://github.com/abdelouahabmoulinepro-coder/replenishment-budget-lab.git
cd replenishment-budget-lab
python planner.py --output build
python -m unittest discover -s tests -v
```

Lire `build/report.md`, puis consulter `build/purchase_plan.csv` pour le plan d'achat détaillé. Les résultats de référence sont aussi publiés dans [example/report.md](example/report.md).

Pour modifier le budget à **900 €** :

```sh
python planner.py --budget-cents 90000 --output build-900
```

## Résultats effectivement obtenus

Le scénario principal contient huit références et 711 unités de demande sur une période, avec un budget de **1 200 €**.

| Méthode | Achats | Unités manquantes | Satisfaction de la demande en unités | Pénalité modélisée |
|---|---:|---:|---:|---:|
| Aucun achat | 0 € | 555 | 21,9 % | 4 308,50 € |
| Règle gloutonne | 1 197 € | 94 | 86,8 % | 1 429 € |
| Optimisation exacte | 1 197 € | 94 | 86,8 % | 1 429 € |

**Ici, la règle gloutonne atteint déjà l'optimum.** Le solveur confirme ce résultat ; aucune amélioration artificielle n'est revendiquée. Il reste 3 € inutilisables pour acheter un lot supplémentaire. Les pénalités ne sont pas des pertes comptables mesurées, et leur réduction ne constitue pas une économie financière réalisée.

### Un petit cas où la règle gloutonne échoue

```sh
python planner.py data/greedy_trap.json --output build-trap
```

Ce cas est **construit à des fins pédagogiques** : budget 100 €, un article A à 60 € évitant 100 € de pénalité et deux unités B à 50 € chacune évitant 80 € de pénalité par unité. La règle gloutonne choisit A pour son meilleur ratio, puis ne peut plus acheter B. Le solveur choisit deux B.

| Méthode | Achats | Pénalité restante |
|---|---:|---:|
| Gloutonne : 1 A | 60 € | 160 € |
| Exacte : 2 B | 100 € | 100 € |

Le cas démontre l'effet des lots indivisibles et du budget résiduel, sans prétendre qu'un solveur exact améliorera systématiquement une bonne heuristique.

## Modèle métier

Toutes les commandes arrivent **avant le début d'une période unique**, à demande connue ou fournie comme prévision externe. Le stock et les quantités achetées sont disponibles pour satisfaire cette demande.

Pour chaque produit `i`, le nombre entier de lots `q_i` est borné par `max_packs`. Le solveur minimise :

```text
Somme [ max(0, demande_i − stock_i − q_i × taille_lot_i) × pénalité_unitaire_i ]
sous : Somme [ q_i × coût_lot_i ] ≤ budget
```

L'objectif est la **pénalité pondérée de rupture**, pas le nombre brut d'unités manquantes ni le profit net. Un produit plus critique peut être prioritaire. Les achats sont une contrainte de budget, pas un terme soustrait du bénéfice ; à pénalité égale, la dépense la plus faible est préférée. Aucune valeur n'est attribuée au surplus.

Une demande nulle donne un taux de satisfaction `null`. Les surplus dus aux tailles de lots sont affichés. Le programme ne commande pas de lots supplémentaires qui n'apporteraient aucune réduction de pénalité.

## Algorithmes

- **Référence gloutonne** : acheter à chaque étape le lot abordable ayant le meilleur ratio entre réduction marginale de pénalité et coût. Le dernier lot peut avoir un bénéfice partiel. Les ratios sont comparés exactement avec des fractions ; les ex æquo suivent l'ordre des produits.
- **Solveur exact** : programmation dynamique sur les choix de lots par produit. Chaque état conserve le bénéfice cumulé pour un coût donné. Les états plus coûteux sans bénéfice supplémentaire sont éliminés. Après traitement de tous les produits, la meilleure réduction de pénalité est retenue, puis le moindre coût. Les égalités restantes sont départagées par le vecteur des lots dans l'ordre du fichier.

Il s'agit d'une variante du problème du sac à dos avec plusieurs options par produit. Voir l'[introduction au problème du sac à dos de Google OR-Tools](https://developers.google.com/optimization/pack/knapsack) pour le principe général ; ce projet possède sa propre implémentation et n'utilise pas OR-Tools.

Un plafond de **2 millions de transitions par résolution** interrompt explicitement les cas trop grands. Le résultat n'est annoncé comme exact que si la résolution se termine. La comparaison de scénarios peut lancer plusieurs résolutions ; réduire le nombre de produits ou de lots si ce plafond est atteint.

## Contrat d'entrée

Le fichier JSON contient `budget_cents` et une liste `products` de 1 à 30 produits.

| Champ produit | Signification |
|---|---|
| `sku` | Identifiant ASCII unique, 1–40 lettres, chiffres, tirets ou underscores |
| `stock` | Stock disponible au début de la période |
| `demand` | Demande totale de la période, donnée externe au solveur |
| `pack_size` | Nombre d'unités dans un lot, strictement positif |
| `pack_cost_cents` | Prix total d'un lot en centimes, strictement positif |
| `max_packs` | Limite fournisseur, de 0 à 100 lots |
| `shortage_penalty_cents` | Pénalité hypothétique par unité manquante, positive ou nulle |

Tous les champs numériques sont des entiers non négatifs, au plus 1 milliard, sous réserve des bornes plus strictes du tableau. Les booléens et les décimaux sont refusés. Les montants agrégés sont calculés en entiers, sans arrondis monétaires intermédiaires. La devise de la démonstration est l'euro, sans conversion ni fiscalité.

## Deux analyses de sensibilité distinctes

1. **Demande −20 %, nominale et +20 %** : les quantités commandées restent celles décidées avec la demande nominale. La demande stressée est arrondie à l'unité, moitié vers le haut. Aucun réapprovisionnement n'est recalculé après observation du scénario.
2. **Budget de 0 à 125 % du budget initial par pas de 25 %** : le plan est réoptimisé pour chaque budget sur la même demande nominale. Les points dépassant le plafond d'entrée d'un milliard de centimes sont omis.

Ces scénarios sont des hypothèses déterministes, pas des prévisions probabilistes ni des résultats de backtest. Le projet ne contient pas de modèle de machine learning entraîné.

## Sorties

- `results.json` : plans, KPI, scénarios, budgets et empreinte SHA-256 du JSON d'entrée normalisé.
- `purchase_plan.csv` : lots à commander, coûts, demande, manquants et surplus du plan optimal.
- `report.md` : rapport comparatif lisible.

Les sorties sont remplacées à chaque exécution dans le dossier choisi. Utiliser des dossiers distincts pour conserver plusieurs analyses ou lancer des exécutions concurrentes. Code de sortie 0 en cas de succès, 1 en cas d'erreur d'entrée ou de résolution traitée, 2 en cas de syntaxe de commande invalide. Une exécution échouée ne valide jamais les anciens fichiers de sortie.

## Validation

**13 tests automatisés**, dont une comparaison à une énumération exhaustive indépendante sur **40 petits cas reproductibles**. La vérification porte sur la pénalité optimale et la dépense minimale, pas seulement sur le respect du budget. Les autres tests couvrent les lots partiels, limites fournisseurs, budgets nuls, pénalités nulles, demande maximale, taux de satisfaction, scénarios fixes, limite de complexité et sorties de la commande.

## Limites et origine des données

Les huit références et leurs paramètres sont inventés pour ce projet. Aucune donnée d'entreprise ni donnée personnelle n'est utilisée. Les prix et pénalités ne constituent pas des estimations de marché.

Le modèle suppose des livraisons ponctuelles avant consommation. Il ignore les délais variables, les commandes en cours, la capacité de stockage, les coûts fixes de commande, la péremption, les substitutions, les minimums fournisseurs et les périodes suivantes. Il ne calcule pas de stock de sécurité statistique. Le taux de satisfaction affiché est une proportion d'unités servies sur une période agrégée, pas une probabilité de non-rupture.

Avant une application opérationnelle, valider les pénalités et les hypothèses avec les équipes métier, puis intégrer les délais et évaluer la politique sur un historique distinct. Le programme génère un plan local ; il n'envoie aucune commande à un fournisseur.

Licence MIT : voir [LICENSE](LICENSE).
