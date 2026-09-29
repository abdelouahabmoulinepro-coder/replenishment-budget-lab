"""Exact, single-period replenishment allocation under a shared purchase budget."""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re


def integer(value, name, minimum=0, maximum=10**9):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return value


def validate(config):
    if not isinstance(config, dict):
        raise ValueError('Configuration must be an object')
    budget = integer(config.get('budget_cents'), 'budget_cents')
    products = config.get('products')
    if not isinstance(products, list) or not 1 <= len(products) <= 30:
        raise ValueError('Provide between 1 and 30 products')
    seen = set()
    for product in products:
        if not isinstance(product, dict) or not isinstance(product.get('sku'), str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', product['sku']):
            raise ValueError('Each product requires a short ASCII sku')
        if product['sku'] in seen:
            raise ValueError('Duplicate sku')
        seen.add(product['sku'])
        for field in ['stock', 'demand', 'max_packs', 'shortage_penalty_cents']:
            integer(product.get(field), field)
        for field in ['pack_size', 'pack_cost_cents']:
            integer(product.get(field), field, 1)
        if product['max_packs'] > 100:
            raise ValueError('At most 100 packs per product')
    return products, budget


def shortage(product, packs=0, demand=None):
    demand = product['demand'] if demand is None else demand
    return max(0, demand - product['stock'] - packs * product['pack_size'])


def benefit(product, packs):
    return (shortage(product) - shortage(product, packs)) * product['shortage_penalty_cents']


def limit(product, budget):
    needed = (shortage(product) + product['pack_size'] - 1) // product['pack_size']
    return min(product['max_packs'], needed, budget // product['pack_cost_cents'])


def optimize(products, budget, transition_limit=2_000_000):
    """Multiple-choice knapsack DP; dominated cost states are pruned exactly."""
    validate({'products': products, 'budget_cents': budget})
    states = {0: (0, ())}
    transitions = 0
    for product in products:
        next_states = {}
        for cost, (value, plan) in states.items():
            for packs in range(limit(product, budget - cost) + 1):
                transitions += 1
                if transitions > transition_limit:
                    raise ValueError('Exact solver complexity limit reached; reduce product count, packs or budget')
                new_cost = cost + packs * product['pack_cost_cents']
                candidate = (value + benefit(product, packs), plan + (packs,))
                previous = next_states.get(new_cost)
                if previous is None or candidate[0] > previous[0] or (candidate[0] == previous[0] and candidate[1] < previous[1]):
                    next_states[new_cost] = candidate
        # A more expensive state with no additional benefit cannot improve any continuation.
        states, best_value = {}, -1
        for cost in sorted(next_states):
            if next_states[cost][0] > best_value:
                states[cost] = next_states[cost]
                best_value = next_states[cost][0]
    best_cost = max(states, key=lambda cost: (states[cost][0], -cost))
    return list(states[best_cost][1])


def greedy(products, budget):
    """Buy the affordable next pack with the largest marginal benefit per cent."""
    validate({'products': products, 'budget_cents': budget})
    plan = [0] * len(products)
    remaining = budget
    while True:
        choices = []
        for i, product in enumerate(products):
            if plan[i] >= limit(product, budget) or product['pack_cost_cents'] > remaining:
                continue
            gain = benefit(product, plan[i] + 1) - benefit(product, plan[i])
            if gain > 0:
                choices.append((Fraction(gain, product['pack_cost_cents']), -i, i))
        if not choices:
            return plan
        i = max(choices)[2]
        plan[i] += 1
        remaining -= products[i]['pack_cost_cents']


def measure(products, plan, demands=None):
    if len(plan) != len(products) or (demands is not None and len(demands) != len(products)):
        raise ValueError('Plan and demand lengths must match product count')
    rows = []
    for i, (product, packs) in enumerate(zip(products, plan)):
        integer(packs, 'packs')
        if packs > product['max_packs']:
            raise ValueError('Plan exceeds supply limit')
        demand = product['demand'] if demands is None else integer(demands[i], 'scenario demand', maximum=1_200_000_000)
        missing = shortage(product, packs, demand)
        rows.append({'sku': product['sku'], 'packs': packs, 'ordered_units': packs * product['pack_size'],
                     'stock': product['stock'], 'demand': demand, 'shortage_units': missing,
                     'leftover_units': max(0, product['stock'] + packs * product['pack_size'] - demand),
                     'purchase_cents': packs * product['pack_cost_cents'],
                     'shortage_penalty_cents': missing * product['shortage_penalty_cents']})
    total_demand = sum(row['demand'] for row in rows)
    missing = sum(row['shortage_units'] for row in rows)
    return {'purchase_cents': sum(row['purchase_cents'] for row in rows), 'shortage_units': missing,
            'shortage_penalty_cents': sum(row['shortage_penalty_cents'] for row in rows),
            'fill_rate': (total_demand - missing) / total_demand if total_demand else None, 'products': rows}


def run(config):
    products, budget = validate(config)
    plans = {'no_purchase': [0] * len(products), 'greedy': greedy(products, budget), 'optimal': optimize(products, budget)}
    results = {name: measure(products, plan) for name, plan in plans.items()}
    stress = {}
    for name, numerator in [('low_minus_20pct', 8), ('base', 10), ('high_plus_20pct', 12)]:
        # Integer half-up rounding. Plans remain fixed; no hindsight reoptimization.
        demands = [(product['demand'] * numerator + 5) // 10 for product in products]
        stress[name] = {key: {k: v for k, v in measure(products, plan, demands).items() if k != 'products'} for key, plan in plans.items()}
    frontier = []
    for amount in sorted({budget * fraction // 4 for fraction in range(6)}):
        if amount > 10**9:
            continue
        metrics = measure(products, optimize(products, amount))
        frontier.append({'budget_cents': amount, **{k: v for k, v in metrics.items() if k != 'products'}})
    canonical = json.dumps(config, sort_keys=True, ensure_ascii=False).encode()
    return {'input_sha256': hashlib.sha256(canonical).hexdigest(), 'budget_cents': budget,
            'plans': results, 'fixed_plan_stress_tests': stress, 'budget_frontier': frontier}


def markdown(report):
    euro = lambda value: f'{value / 100:.2f} EUR'
    lines = ['# Replenishment Budget Lab', '', '> Simulation fictive sur une période. Les pénalités sont des hypothèses de modélisation, pas des économies réalisées.', '',
             f"Budget : **{euro(report['budget_cents'])}**", '',
             '| Méthode | Achats | Unités manquantes | Pénalité modélisée | Satisfaction en unités |', '|---|---:|---:|---:|---:|']
    for name, result in report['plans'].items():
        fill = 'N/A' if result['fill_rate'] is None else f"{result['fill_rate']:.1%}"
        lines.append(f"| {name} | {euro(result['purchase_cents'])} | {result['shortage_units']} | {euro(result['shortage_penalty_cents'])} | {fill} |")
    lines += ['', '## Commandes du plan optimal', '', '| Produit | Lots | Unités commandées | Achats | Manquants | Surplus |', '|---|---:|---:|---:|---:|---:|']
    for row in report['plans']['optimal']['products']:
        lines.append(f"| {row['sku']} | {row['packs']} | {row['ordered_units']} | {euro(row['purchase_cents'])} | {row['shortage_units']} | {row['leftover_units']} |")
    lines += ['', '## Sensibilité à la demande — plans inchangés', '', '| Scénario | Méthode | Manquants | Pénalité modélisée |', '|---|---|---:|---:|']
    for scenario, methods in report['fixed_plan_stress_tests'].items():
        for name, result in methods.items():
            lines.append(f"| {scenario} | {name} | {result['shortage_units']} | {euro(result['shortage_penalty_cents'])} |")
    lines += ['', '## Sensibilité au budget — réoptimisation', '', '| Budget | Achats | Manquants | Pénalité modélisée |', '|---|---:|---:|---:|']
    for row in report['budget_frontier']:
        lines.append(f"| {euro(row['budget_cents'])} | {euro(row['purchase_cents'])} | {row['shortage_units']} | {euro(row['shortage_penalty_cents'])} |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', default='data/scenario.json')
    parser.add_argument('--budget-cents', type=int)
    parser.add_argument('--output', default='build')
    args = parser.parse_args()
    try:
        source = Path(args.input).resolve()
        output = Path(args.output).resolve()
        if source in [output / name for name in ['results.json', 'report.md', 'purchase_plan.csv']]:
            raise ValueError('Output would overwrite input')
        config = json.loads(source.read_text(encoding='utf-8-sig'))
        if args.budget_cents is not None:
            config['budget_cents'] = args.budget_cents
        report = run(config)
        output.mkdir(parents=True, exist_ok=True)
        (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        (output / 'report.md').write_text(markdown(report), encoding='utf-8')
        rows = report['plans']['optimal']['products']
        with (output / 'purchase_plan.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        print(json.dumps({name: {k: v for k, v in result.items() if k != 'products'} for name, result in report['plans'].items()}, indent=2))
    except (ValueError, OSError, TypeError) as error:
        parser.exit(1, f'Input/solver error: {error}\n')


if __name__ == '__main__':
    main()
