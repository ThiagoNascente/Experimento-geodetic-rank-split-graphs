"""Benchmark reproduzível contra as funções originais, sem extrapolar a busca antiga."""

import argparse
from itertools import combinations
import random
from time import perf_counter

import networkx as nx

from convexity_geodetic import GeodeticConvexity, SearchStats
from grafo_diam_2 import construir_grafo
from prisms import prisma_complementar


def original_hull(graph, vertices):
    """Referência anterior à otimização; também usada nos testes de equivalência."""
    result = set(vertices)
    while True:
        expanded = set(result)
        for u, v in combinations(result, 2):
            if not nx.has_path(graph, u, v):
                continue
            for path in nx.all_shortest_paths(graph, u, v):
                expanded.update(path)
        if expanded == result:
            return result
        result = expanded


def original_rank(graph, vertices):
    vertices = set(vertices)
    for vertex in vertices:
        if vertex in original_hull(graph, vertices - {vertex}):
            return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--amostras", type=int, default=100)
    args = parser.parse_args(argv)
    if args.amostras < 1:
        parser.error("Use pelo menos uma amostra.")

    graph = prisma_complementar(construir_grafo(nx.relabel_nodes(nx.path_graph(5), str)))
    nodes = tuple(graph)
    rng = random.Random(20261117)
    samples = [tuple(rng.sample(nodes, 11)) for _ in range(args.amostras)]
    # Aquece o despacho de NetworkX antes das medições.
    original_rank(graph, samples[0])
    start = perf_counter()
    original_results = [original_rank(graph, sample) for sample in samples]
    original_seconds = perf_counter() - start

    start = perf_counter()
    context = GeodeticConvexity(graph)
    preparation_seconds = perf_counter() - start
    start = perf_counter()
    optimized_results = [context.is_independent(sample) for sample in samples]
    optimized_seconds = perf_counter() - start
    if original_results != optimized_results:
        raise AssertionError("Os resultados da amostra divergiram.")

    stats = SearchStats()
    for _ in context.independent_sets(11, stats=stats):
        pass
    if stats.resolved_combinations != stats.total_combinations:
        raise AssertionError("A busca não contabilizou todas as combinações.")

    print(f"Amostra reproduzível: {args.amostras} conjuntos de tamanho 11")
    print(f"Verificação original: {original_seconds:.6f} s")
    print(f"Pré-processamento: {preparation_seconds:.6f} s")
    print(f"Verificação otimizada: {optimized_seconds:.6f} s")
    print(f"Ganho na amostra, incluindo pré-processamento: {original_seconds / (preparation_seconds + optimized_seconds):.1f}x")
    print(f"Busca completa otimizada: {stats.elapsed_seconds:.6f} s")
    print(f"Extensões verificadas: {stats.extensions_tested}")
    print(f"Combinações resolvidas: {stats.resolved_combinations}")
    print(f"Conjuntos independentes: {stats.independent_sets}")


if __name__ == "__main__":
    main()
