"""Equivalência com a referência original e regressões da busca com poda."""

from contextlib import redirect_stdout
from io import StringIO
from itertools import combinations
from math import comb
import unittest

import networkx as nx

from benchmarks.benchmark_programa_2 import original_hull, original_rank
from convexity_geodetic import GeodeticConvexity, SearchStats, geodetic_hull, geodetic_rank
from grafo_diam_2 import construir_grafo
from prisms import prisma_complementar


class GeodeticConvexityTests(unittest.TestCase):
    def assert_equivalent(self, graph):
        context = GeodeticConvexity(graph)
        hulls = {}
        expected_by_size = [[] for _ in range(len(graph) + 1)]
        for size in range(len(graph) + 1):
            for subset in combinations(graph, size):
                hulls[subset] = original_hull(graph, subset)
                self.assertEqual(context.hull(subset), hulls[subset], (list(graph.edges()), subset))
                independent = all(
                    v not in hulls[tuple(u for u in subset if u != v)] for v in subset
                )
                self.assertEqual(context.is_independent(subset), independent, subset)
                if independent:
                    expected_by_size[size].append(subset)

        for size, expected in enumerate(expected_by_size):
            stats = SearchStats()
            actual = list(context.independent_sets(size, stats=stats))
            self.assertEqual(actual, expected, (list(graph.edges()), size))
            self.assertEqual(stats.independent_sets, len(expected))
            self.assertEqual(stats.total_combinations, comb(len(graph), size))
            self.assertEqual(stats.resolved_combinations, stats.total_combinations)

    def test_all_unlabeled_graphs_up_to_five_vertices(self):
        graphs = [graph for graph in nx.graph_atlas_g() if len(graph) <= 5]
        self.assertEqual(len(graphs), 53)
        for graph in graphs:
            with self.subTest(nodes=len(graph), edges=list(graph.edges())):
                self.assert_equivalent(graph)

    def test_random_graphs_with_seven_vertices(self):
        for seed in (7, 17):
            for probability in (0.15, 0.5, 0.85):
                with self.subTest(seed=seed, probability=probability):
                    self.assert_equivalent(nx.gnp_random_graph(7, probability, seed=seed))

    def test_closure_requires_multiple_rounds(self):
        graph = nx.complete_bipartite_graph(2, 3)
        # A primeira expansão de {2,3} adiciona {0,1}; I(0,1) adiciona 4.
        self.assertEqual(GeodeticConvexity(graph).hull([2, 3]), set(graph))
        self.assertFalse(GeodeticConvexity(graph).is_independent([2, 3, 4]))

    def test_disconnected_graph_with_mixed_labels(self):
        graph = nx.Graph()
        graph.add_edges_from([("a", ("b", 1)), (("b", 1), -3)])
        graph.add_nodes_from(["isolado", 42])
        self.assert_equivalent(graph)

    def test_wrappers_and_context_snapshot(self):
        graph = nx.path_graph(3)
        context = GeodeticConvexity(graph)
        for source in (graph, context):
            self.assertEqual(geodetic_hull(source, [0, 2]), {0, 1, 2})
            self.assertFalse(geodetic_rank(source, [0, 1, 2]))
            self.assertTrue(geodetic_rank(source, [0, 2, 2]))
        graph.add_edge(0, 2)
        self.assertEqual(context.hull([0, 2]), {0, 1, 2})
        self.assertEqual(geodetic_hull(graph, [0, 2]), {0, 2})

    def test_empty_oversized_invalid_and_missing_vertices(self):
        context = GeodeticConvexity(nx.empty_graph(0))
        stats = SearchStats()
        self.assertEqual(list(context.independent_sets(0, stats=stats)), [()])
        self.assertEqual(stats.resolved_combinations, 1)
        self.assertEqual(list(context.independent_sets(1, stats=stats)), [])
        self.assertEqual(stats.resolved_combinations, 0)
        self.assertEqual(stats.independent_sets, 0)
        with self.assertRaises(ValueError):
            list(context.independent_sets(-1))
        with self.assertRaises(ValueError):
            list(context.independent_sets(0, progress_interval=0))
        with self.assertRaises(nx.NodeNotFound):
            context.hull(["ausente"])
        with self.assertRaises(nx.NetworkXNotImplemented):
            GeodeticConvexity(nx.DiGraph())

    def test_progress_accounts_for_all_combinations(self):
        context = GeodeticConvexity(nx.path_graph(7))
        reports = []
        stats = SearchStats()
        list(context.independent_sets(3, stats=stats, progress=lambda s: reports.append(s.resolved_combinations)))
        self.assertTrue(reports)
        self.assertEqual(reports[-1], comb(7, 3))
        self.assertGreater(stats.pruned_combinations, 0)

    def test_target_experiment_and_positive_witness(self):
        graph = prisma_complementar(construir_grafo(nx.relabel_nodes(nx.path_graph(5), str)))
        context = GeodeticConvexity(graph)
        witness = tuple(v for v in graph if str(v).startswith("v(") and not str(v).endswith("c"))
        self.assertEqual(len(witness), 10)
        self.assertTrue(original_rank(graph, witness))
        self.assertTrue(context.is_independent(witness))
        self.assertIn(witness, list(context.independent_sets(10)))
        stats = SearchStats()
        self.assertEqual(list(context.independent_sets(11, stats=stats)), [])
        self.assertEqual(stats.total_combinations, 54627300)
        self.assertEqual(stats.pruned_combinations, stats.total_combinations)
        self.assertLess(stats.extensions_tested, 30000)

    def test_legacy_libs_import_and_program_entry_point(self):
        from libs import geodetic_rank as legacy_rank
        from Experimentos_diam_2.programa_2 import main

        self.assertTrue(legacy_rank(nx.path_graph(3), [0, 2]))
        output = StringIO()
        with redirect_stdout(output):
            stats = main(["--ordem", "2", "--k", "2"])
        self.assertGreater(stats.independent_sets, 0)
        self.assertIn("Conjunto independente encontrado:", output.getvalue())
        self.assertIn("Fecho:", output.getvalue())
        self.assertEqual(stats.resolved_combinations, stats.total_combinations)


if __name__ == "__main__":
    unittest.main()
