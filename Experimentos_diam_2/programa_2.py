"""Busca exata de conjuntos convexamente independentes (tamanho padrão: 11)."""

import argparse
from pathlib import Path
import sys
from time import perf_counter

import networkx as nx

# Permite executar tanto com python -m quanto pelo caminho do arquivo.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from convexity_geodetic import GeodeticConvexity, SearchStats
from grafo_diam_2 import construir_grafo
from prisms import prisma_complementar


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ordem", type=int, default=5, help="Ordem do caminho inicial (padrão: 5).")
    parser.add_argument("--k", type=int, default=11, help="Tamanho dos conjuntos (padrão: 11).")
    parser.add_argument("--plotar", action="store_true", help="Abre o desenho de G após a busca.")
    parser.add_argument("--detalhar-grafo", action="store_true", help="Lista vértices e arestas do prisma.")
    parser.add_argument(
        "--intervalo-progresso", type=float, default=5.0, help="Segundos entre informes de progresso."
    )
    args = parser.parse_args(argv)
    if args.ordem < 1 or args.k < 0 or args.intervalo_progresso <= 0:
        parser.error("Use ordem >= 1, k >= 0 e intervalo de progresso > 0.")

    start = perf_counter()
    initial_graph = nx.relabel_nodes(nx.path_graph(args.ordem), str)
    graph = construir_grafo(initial_graph)
    prism = prisma_complementar(graph)
    context = GeodeticConvexity(prism)
    preparation_seconds = perf_counter() - start
    stats = SearchStats()

    print(f"Prisma complementar: {len(prism)} vértices, {prism.number_of_edges()} arestas.")
    if args.detalhar_grafo:
        print(f"Vértices do GGc: {list(prism.nodes())}")
        print(f"Arestas do GGc: {list(prism.edges())}")
    print(f"Tamanho dos conjuntos: {args.k}")
    print(f"Pré-processamento: {preparation_seconds:.3f} s")

    def progress(current):
        print(
            f"Progresso: {current.resolved_combinations}/{current.total_combinations} "
            f"combinações resolvidas; {current.extensions_tested} extensões verificadas; "
            f"{current.elapsed_seconds:.3f} s",
            flush=True,
        )

    for independent in context.independent_sets(
        args.k, stats=stats, progress=progress, progress_interval=args.intervalo_progresso
    ):
        print(f"\nConjunto independente encontrado: {list(independent)}")
        print(f"Fecho: {context.hull(independent)}")

    print(f"\nTotal de combinações: {stats.total_combinations}")
    print(f"Combinações descartadas por poda: {stats.pruned_combinations}")
    print(f"Extensões de subconjuntos verificadas: {stats.extensions_tested}")
    print(f"Conjuntos convexamente independentes: {stats.independent_sets}")
    print(f"Tempo da busca: {stats.elapsed_seconds:.3f} s")
    print(f"Tempo total: {perf_counter() - start:.3f} s")

    if args.plotar:
        from plotando_grafos import plotar_grafo

        plotar_grafo(graph)
    return stats


if __name__ == "__main__":
    main()
