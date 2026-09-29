# Replenishment Budget Lab

> Simulation fictive sur une période. Les pénalités sont des hypothèses de modélisation, pas des économies réalisées.

Budget : **1200.00 EUR**

| Méthode | Achats | Unités manquantes | Pénalité modélisée | Satisfaction en unités |
|---|---:|---:|---:|---:|
| no_purchase | 0.00 EUR | 555 | 4308.50 EUR | 21.9% |
| greedy | 1197.00 EUR | 94 | 1429.00 EUR | 86.8% |
| optimal | 1197.00 EUR | 94 | 1429.00 EUR | 86.8% |

## Commandes du plan optimal

| Produit | Lots | Unités commandées | Achats | Manquants | Surplus |
|---|---:|---:|---:|---:|---:|
| COFFEE | 6 | 72 | 360.00 EUR | 6 | 0 |
| TEA | 3 | 60 | 150.00 EUR | 0 | 1 |
| FILTERS | 2 | 100 | 64.00 EUR | 35 | 0 |
| MUGS | 2 | 12 | 84.00 EUR | 22 | 0 |
| BOTTLES | 5 | 50 | 375.00 EUR | 3 | 0 |
| SPOONS | 2 | 48 | 56.00 EUR | 12 | 0 |
| SUGAR | 3 | 120 | 108.00 EUR | 0 | 0 |
| KETTLES | 0 | 0 | 0.00 EUR | 16 | 0 |

## Sensibilité à la demande — plans inchangés

| Scénario | Méthode | Manquants | Pénalité modélisée |
|---|---|---:|---:|
| low_minus_20pct | no_purchase | 413 | 3228.00 EUR |
| low_minus_20pct | greedy | 26 | 870.00 EUR |
| low_minus_20pct | optimal | 26 | 870.00 EUR |
| base | no_purchase | 555 | 4308.50 EUR |
| base | greedy | 94 | 1429.00 EUR |
| base | optimal | 94 | 1429.00 EUR |
| high_plus_20pct | no_purchase | 697 | 5389.00 EUR |
| high_plus_20pct | greedy | 235 | 2503.00 EUR |
| high_plus_20pct | optimal | 235 | 2503.00 EUR |

## Sensibilité au budget — réoptimisation

| Budget | Achats | Manquants | Pénalité modélisée |
|---|---:|---:|---:|
| 0.00 EUR | 0.00 EUR | 555 | 4308.50 EUR |
| 300.00 EUR | 300.00 EUR | 271 | 3496.50 EUR |
| 600.00 EUR | 600.00 EUR | 231 | 2776.50 EUR |
| 900.00 EUR | 897.00 EUR | 154 | 2089.00 EUR |
| 1200.00 EUR | 1197.00 EUR | 94 | 1429.00 EUR |
| 1500.00 EUR | 1475.00 EUR | 37 | 876.00 EUR |
