"""Equivalência e visita efetiva de todas as combinações no programa_3."""

from contextlib import redirect_stdout
from io import StringIO
from itertools import combinations, islice
from math import comb
import unittest
from unittest.mock import patch

import networkx as nx

from benchmarks.benchmark_programa_2 import original_hull, original_rank
from Experimentos_diam_2.programa_3 import CachedGeodeticConvexity, main, search_exhaustively
from grafo_diam_2 import construir_grafo
from prisms import prisma_complementar


class ExhaustiveSearchTests(unittest.TestCase):
    def test_equivalence_for_all_graphs_up_to_five_vertices(self):
        for graph in nx.graph_atlas_g():
            if len(graph) > 5:
                continue
            hulls = {}
            expected = [[] for _ in range(len(graph) + 1)]
            for size in range(len(graph) + 1):
                for subset in combinations(graph, size):
                    hulls[subset] = original_hull(graph, subset)
                    if all(v not in hulls[tuple(u for u in subset if u != v)] for v in subset):
                        expected[size].append(subset)
            for cache_size in (0, 3, 256):
                with self.subTest(edges=list(graph.edges()), cache_size=cache_size):
                    context = CachedGeodeticConvexity(graph, cache_size=cache_size)
                    for subset, hull in hulls.items():
                        self.assertEqual(context.hull(subset), hull)
                        self.assertEqual(context.is_independent(subset), subset in expected[len(subset)])
                    for size, independent in enumerate(expected):
                        found = []
                        stats = search_exhaustively(context, size, on_independent=found.append)
                        self.assertEqual(found, independent)
                        self.assertEqual(stats.checked_combinations, comb(len(graph), size))
                        self.assertEqual(stats.total_combinations, stats.checked_combinations)
                        self.assertEqual(stats.independent_sets, len(independent))
                    self.assertLessEqual(context.cache_info().currsize, cache_size)

    def test_every_candidate_is_checked_once_even_when_dependent(self):
        context = CachedGeodeticConvexity(nx.path_graph(4))
        with patch.object(context, "_is_independent_bits", wraps=context._is_independent_bits) as check:
            with patch.object(context, "independent_sets", side_effect=AssertionError("Busca com poda chamada")):
                stats = search_exhaustively(context, 3)
        visited = [tuple(bit.bit_length() - 1 for bit in call.args[0]) for call in check.call_args_list]
        self.assertEqual(visited, [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
        self.assertEqual(stats.checked_combinations, 4)
        self.assertEqual(stats.independent_sets, 0)

    def test_cache_reuses_complete_closures_and_respects_bound(self):
        context = CachedGeodeticConvexity(nx.complete_bipartite_graph(2, 3), cache_size=3)
        self.assertEqual(context.hull([2, 3]), set(context.nodes))
        before = context.cache_info()
        self.assertEqual(context.hull([2, 3]), set(context.nodes))
        after = context.cache_info()
        self.assertEqual(after.misses, before.misses)
        self.assertEqual(after.hits, before.hits + 1)
        for subset in combinations(context.nodes, 3):
            self.assertEqual(context.hull(subset), original_hull(nx.complete_bipartite_graph(2, 3), subset))
            self.assertLessEqual(context.cache_info().currsize, 3)
        self.assertFalse(context.is_independent([2, 3, 4]))

    def test_disabled_cache_and_mixed_labels(self):
        graph = nx.Graph()
        graph.add_edges_from([("a", ("b", 1)), (("b", 1), -3)])
        graph.add_node("isolado")
        context = CachedGeodeticConvexity(graph, cache_size=0)
        for subset in combinations(graph, 3):
            self.assertEqual(context.hull(subset), original_hull(graph, subset))
            self.assertEqual(context.is_independent(subset), original_rank(graph, subset))
        self.assertEqual(context.cache_info().hits, 0)
        self.assertEqual(context.cache_info().misses, 0)
        self.assertEqual(context.cache_info().currsize, 0)

    def test_empty_oversized_and_invalid_inputs(self):
        context = CachedGeodeticConvexity(nx.empty_graph(0))
        found = []
        stats = search_exhaustively(context, 0, on_independent=found.append)
        self.assertEqual(found, [()])
        self.assertEqual(stats.checked_combinations, 1)
        self.assertEqual(stats.independent_sets, 1)
        stats = search_exhaustively(context, 1)
        self.assertEqual(stats.total_combinations, 0)
        self.assertEqual(stats.checked_combinations, 0)
        with self.assertRaises(ValueError):
            CachedGeodeticConvexity(nx.Graph(), cache_size=-1)
        with self.assertRaises(ValueError):
            search_exhaustively(context, -1)
        with self.assertRaises(ValueError):
            search_exhaustively(context, 0, progress_interval=0)
        with self.assertRaises(nx.NodeNotFound):
            context.hull(["ausente"])

    def test_target_graph_has_an_independent_witness_of_size_ten(self):
        graph = prisma_complementar(construir_grafo(nx.relabel_nodes(nx.path_graph(5), str)))
        witness = tuple(v for v in graph if str(v).startswith("v(") and not str(v).endswith("c"))
        for cache_size in (0, 64):
            context = CachedGeodeticConvexity(graph, cache_size=cache_size)
            self.assertTrue(original_rank(graph, witness))
            self.assertTrue(context.is_independent(witness))
            for candidate in islice(combinations(graph, 11), 20):
                self.assertEqual(context.is_independent(candidate), original_rank(graph, candidate))

    def test_progress_and_main_report_actual_checks(self):
        context = CachedGeodeticConvexity(nx.complete_graph(5))
        reports = []
        stats = search_exhaustively(context, 3, progress=lambda s: reports.append(s.checked_combinations))
        self.assertEqual(stats.checked_combinations, 10)
        self.assertEqual(stats.independent_sets, 10)
        self.assertEqual(reports[-1], 10)
        output = StringIO()
        with redirect_stdout(output):
            result = main(["--ordem", "2", "--k", "2", "--cache-fechos", "3"])
        self.assertEqual(result.checked_combinations, 15)
        self.assertEqual(result.independent_sets, 15)
        self.assertIn("Combinações efetivamente verificadas: 15", output.getvalue())
        self.assertIn("Fecho:", output.getvalue())
        output = StringIO()
        with redirect_stdout(output):
            result = main(["--ordem", "2", "--k", "2", "--cache-fechos", "0"])
        self.assertEqual(result.checked_combinations, 15)
        self.assertIn("Cache de fechos: desativado.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
