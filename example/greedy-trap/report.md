# Replenishment Budget Lab

> Simulation fictive sur une période. Les pénalités sont des hypothèses de modélisation, pas des économies réalisées.

Budget : **100.00 EUR**

| Méthode | Achats | Unités manquantes | Pénalité modélisée | Satisfaction en unités |
|---|---:|---:|---:|---:|
| no_purchase | 0.00 EUR | 3 | 260.00 EUR | 0.0% |
| greedy | 60.00 EUR | 2 | 160.00 EUR | 33.3% |
| optimal | 100.00 EUR | 1 | 100.00 EUR | 66.7% |

## Commandes du plan optimal

| Produit | Lots | Unités commandées | Achats | Manquants | Surplus |
|---|---:|---:|---:|---:|---:|
| A | 0 | 0 | 0.00 EUR | 1 | 0 |
| B | 2 | 2 | 100.00 EUR | 0 | 0 |

## Sensibilité à la demande — plans inchangés

| Scénario | Méthode | Manquants | Pénalité modélisée |
|---|---|---:|---:|
| low_minus_20pct | no_purchase | 3 | 260.00 EUR |
| low_minus_20pct | greedy | 2 | 160.00 EUR |
| low_minus_20pct | optimal | 1 | 100.00 EUR |
| base | no_purchase | 3 | 260.00 EUR |
| base | greedy | 2 | 160.00 EUR |
| base | optimal | 1 | 100.00 EUR |
| high_plus_20pct | no_purchase | 3 | 260.00 EUR |
| high_plus_20pct | greedy | 2 | 160.00 EUR |
| high_plus_20pct | optimal | 1 | 100.00 EUR |

## Sensibilité au budget — réoptimisation

| Budget | Achats | Manquants | Pénalité modélisée |
|---|---:|---:|---:|
| 0.00 EUR | 0.00 EUR | 3 | 260.00 EUR |
| 25.00 EUR | 0.00 EUR | 3 | 260.00 EUR |
| 50.00 EUR | 50.00 EUR | 2 | 180.00 EUR |
| 75.00 EUR | 60.00 EUR | 2 | 160.00 EUR |
| 100.00 EUR | 100.00 EUR | 1 | 100.00 EUR |
| 125.00 EUR | 110.00 EUR | 1 | 80.00 EUR |
