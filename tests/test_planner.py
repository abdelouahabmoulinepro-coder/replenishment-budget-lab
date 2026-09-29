import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from planner import greedy, measure, optimize, run, validate


def product(sku='A', **changes):
    return dict(sku=sku, stock=0, demand=10, pack_size=5, pack_cost_cents=100,
                max_packs=3, shortage_penalty_cents=50) | changes


class PlannerTests(unittest.TestCase):
    def test_exact_budget_and_known_totals(self):
        products = [product()]
        plan = optimize(products, 200)
        self.assertEqual(plan, [2])
        result = measure(products, plan)
        self.assertEqual(result['purchase_cents'], 200)
        self.assertEqual(result['shortage_units'], 0)
        self.assertEqual(result['fill_rate'], 1)

    def test_greedy_counterexample(self):
        products = [product('A', demand=1, pack_size=1, pack_cost_cents=60, max_packs=1, shortage_penalty_cents=100),
                    product('B', demand=2, pack_size=1, pack_cost_cents=50, max_packs=2, shortage_penalty_cents=80)]
        self.assertEqual(greedy(products, 100), [1, 0])
        self.assertEqual(optimize(products, 100), [0, 2])
        self.assertEqual(measure(products, [0, 2])['shortage_penalty_cents'], 100)

    def test_exhaustive_oracle_on_40_seeded_instances(self):
        rng = random.Random(73)
        for case in range(40):
            products = [product(str(i), stock=rng.randrange(6), demand=rng.randrange(14),
                                pack_size=rng.randint(1, 6), pack_cost_cents=rng.randint(1, 20),
                                max_packs=rng.randint(0, 3), shortage_penalty_cents=rng.randrange(10)) for i in range(4)]
            budget = rng.randrange(80)
            feasible = []
            # Independent oracle: enumerate even surplus-producing choices.
            for plan in itertools.product(*(range(p['max_packs'] + 1) for p in products)):
                cost = sum(q * p['pack_cost_cents'] for p, q in zip(products, plan))
                penalty = sum(max(0, p['demand'] - p['stock'] - q*p['pack_size']) * p['shortage_penalty_cents'] for p, q in zip(products, plan))
                if cost <= budget:
                    feasible.append((penalty, cost))
            result = measure(products, optimize(products, budget))
            self.assertEqual((result['shortage_penalty_cents'], result['purchase_cents']), min(feasible), f'case {case}')

    def test_zero_and_unaffordable_budget(self):
        self.assertEqual(optimize([product()], 0), [0])
        self.assertEqual(optimize([product()], 99), [0])

    def test_supplier_cap_and_partial_last_pack(self):
        products = [product(demand=7, max_packs=1)]
        self.assertEqual(measure(products, optimize(products, 1000))['shortage_units'], 2)
        products = [product(demand=7)]
        result = measure(products, optimize(products, 1000))
        self.assertEqual(result['products'][0]['leftover_units'], 3)
        self.assertEqual(result['purchase_cents'], 200)

    def test_zero_penalty_and_sufficient_stock_do_not_spend(self):
        self.assertEqual(optimize([product(shortage_penalty_cents=0)], 1000), [0])
        self.assertEqual(optimize([product(stock=10)], 1000), [0])

    def test_zero_demand_fill_rate(self):
        self.assertIsNone(measure([product(demand=0)], [0])['fill_rate'])

    def test_invalid_inputs(self):
        for bad in [-1, True, 1.5, '100']:
            with self.assertRaises(ValueError):
                validate({'products': [product()], 'budget_cents': bad})
        for changes in [{'pack_size': 0}, {'pack_cost_cents': 0}, {'max_packs': 101}, {'demand': -1}, {'sku': '=A1'}]:
            with self.assertRaises(ValueError):
                validate({'products': [product(**changes)], 'budget_cents': 100})
        with self.assertRaises(ValueError):
            optimize([product(), product()], 100)

    def test_complexity_limit_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'complexity'):
            optimize([product()], 100, transition_limit=1)

    def test_budget_frontier_and_stress(self):
        config = {'budget_cents': 200, 'products': [product()]}
        report = run(config)
        penalties = [row['shortage_penalty_cents'] for row in report['budget_frontier']]
        self.assertEqual(penalties, sorted(penalties, reverse=True))
        for scenario in report['fixed_plan_stress_tests'].values():
            self.assertEqual(scenario['optimal']['purchase_cents'], 200)
        self.assertEqual(report['fixed_plan_stress_tests']['high_plus_20pct']['optimal']['shortage_units'], 2)
        self.assertEqual(report, run(config))

    def test_cli_demo_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            process = subprocess.run([sys.executable, 'planner.py', '--output', folder], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            report = json.loads((Path(folder) / 'results.json').read_text())
            self.assertLessEqual(report['plans']['optimal']['purchase_cents'], report['budget_cents'])
            self.assertLessEqual(report['plans']['optimal']['shortage_penalty_cents'], report['plans']['greedy']['shortage_penalty_cents'])
            self.assertTrue((Path(folder) / 'purchase_plan.csv').exists())
            self.assertTrue((Path(folder) / 'report.md').exists())

    def test_invalid_plan_lengths(self):
        with self.assertRaises(ValueError):
            measure([product()], [])
        with self.assertRaises(ValueError):
            measure([product()], [4])

    def test_maximum_demand_stress_remains_valid(self):
        report = run({'budget_cents': 0, 'products': [product(demand=10**9, max_packs=0)]})
        self.assertEqual(report['fixed_plan_stress_tests']['high_plus_20pct']['optimal']['shortage_units'], 1_200_000_000)


if __name__ == '__main__':
    unittest.main()
