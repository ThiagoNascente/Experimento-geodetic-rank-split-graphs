"""Verifica cada combinação de vértices, reutilizando intervalos e fechos."""

import argparse
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from math import comb
from pathlib import Path
import sys
from time import perf_counter

import networkx as nx

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from convexity_geodetic import GeodeticConvexity
from grafo_diam_2 import construir_grafo
from prisms import prisma_complementar


@dataclass
class ExhaustiveSearchStats:
    total_combinations: int = 0
    checked_combinations: int = 0
    independent_sets: int = 0
    elapsed_seconds: float = 0.0


class CachedGeodeticConvexity(GeodeticConvexity):
    """Acrescenta um cache LRU de fechos completos ao contexto geodético.

    A chave é a máscara do conjunto inicial; o valor é seu fecho completo.
    O limite conta entradas. Ao ficar cheio, o cache remove a entrada usada
    há mais tempo. Use cache_size=0 para desativá-lo.
    """

    def __init__(self, graph, cache_size=65536):
        if cache_size < 0:
            raise ValueError("O tamanho do cache deve ser não negativo.")
        super().__init__(graph)
        self.cache_size = cache_size
        self._cached_hull = lru_cache(maxsize=cache_size)(self._compute_hull)

    def _compute_hull(self, mask):
        if not mask:
            return 0
        # Retira o último vértice para reutilizar partes comuns às combinações
        # consecutivas. Fechar um fecho após uma adição produz o mesmo resultado
        # que fechar o conjunto original após essa adição.
        bit = 1 << (mask.bit_length() - 1)
        closed = self._cached_hull(mask ^ bit)
        if closed & bit:
            return closed
        return self._extend_hull(closed, bit)

    def _is_independent_bits(self, bits):
        mask = sum(bits)
        # Remover o último vértice primeiro favorece o reaproveitamento do
        # fecho: combinações consecutivas frequentemente compartilham o início.
        if self.cache_size:
            hull = self._cached_hull
            for bit in reversed(bits):
                if hull(mask ^ bit) & bit:
                    return False
        else:
            for bit in reversed(bits):
                if self._extend_hull(0, mask ^ bit, bit) & bit:
                    return False
        return True

    def is_independent(self, vertices):
        mask = self._mask(vertices)
        bits = tuple(bit for bit in self._bits if mask & bit)
        return self._is_independent_bits(bits)

    def hull(self, vertices):
        mask = self._mask(vertices)
        closed = self._cached_hull(mask) if self.cache_size else self._extend_hull(0, mask)
        return set(self._vertices(closed))

    def cache_info(self):
        return self._cached_hull.cache_info()


def search_exhaustively(context, size, *, on_independent=None, progress=None, progress_interval=5.0):
    """Visita cada uma das C(n, size) combinações e retorna os contadores reais.

    O laço não usa a busca com poda de independent_sets. A memória não cresce
    com o número de combinações: os resultados são entregues ao callback e
    apenas os fechos do cache limitado permanecem armazenados.
    """
    if size < 0:
        raise ValueError("O tamanho do conjunto deve ser não negativo.")
    if progress_interval <= 0:
        raise ValueError("O intervalo de progresso deve ser positivo.")
    stats = ExhaustiveSearchStats(total_combinations=comb(len(context.nodes), size))
    start = perf_counter()
    last_report = start

    def report(force=False):
        nonlocal last_report
        now = perf_counter()
        stats.elapsed_seconds = now - start
        if progress is not None and (force or now - last_report >= progress_interval):
            progress(stats)
            last_report = now

    try:
        # Cada tupla representa uma combinação dos vértices originais. As
        # máscaras evitam converter seus nomes a cada uma das verificações.
        for bits in combinations(context._bits, size):
            independent = context._is_independent_bits(bits)
            stats.checked_combinations += 1
            if independent:
                stats.independent_sets += 1
                if on_independent is not None:
                    on_independent(context._vertices(sum(bits)))
            if stats.checked_combinations % 16384 == 0:
                report()
    finally:
        report(force=True)

    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ordem", type=int, default=5, help="Ordem do caminho inicial (padrão: 5).")
    parser.add_argument("--k", type=int, default=11, help="Tamanho dos conjuntos (padrão: 11).")
    parser.add_argument(
        "--cache-fechos", type=int, default=65536,
        help="Máximo de fechos no cache; 0 desativa o cache (padrão: 65536).",
    )
    parser.add_argument("--plotar", action="store_true", help="Abre o desenho de G após a busca.")
    parser.add_argument("--detalhar-grafo", action="store_true", help="Lista vértices e arestas do prisma.")
    parser.add_argument(
        "--intervalo-progresso", type=float, default=5.0, help="Segundos entre informes de progresso."
    )
    args = parser.parse_args(argv)
    if args.ordem < 1 or args.k < 0 or args.cache_fechos < 0 or args.intervalo_progresso <= 0:
        parser.error("Use ordem >= 1, k >= 0, cache >= 0 e intervalo de progresso > 0.")

    start = perf_counter()
    initial_graph = nx.relabel_nodes(nx.path_graph(args.ordem), str)
    graph = construir_grafo(initial_graph)
    prism = prisma_complementar(graph)
    context = CachedGeodeticConvexity(prism, cache_size=args.cache_fechos)
    preparation_seconds = perf_counter() - start

    print(f"Prisma complementar: {len(prism)} vértices, {prism.number_of_edges()} arestas.")
    print("Modo: enumeração exaustiva, uma verificação por combinação.")
    print(f"Tamanho dos conjuntos: {args.k}")
    print(f"Total de combinações: {comb(len(prism), args.k)}")
    print(f"Limite de entradas no cache de fechos: {args.cache_fechos}")
    print(f"Pré-processamento: {preparation_seconds:.3f} s", flush=True)
    if args.detalhar_grafo:
        print(f"Vértices do GGc: {list(prism.nodes())}")
        print(f"Arestas do GGc: {list(prism.edges())}")

    def show_independent(vertices):
        print(f"\nConjunto independente encontrado: {list(vertices)}")
        print(f"Fecho: {context.hull(vertices)}", flush=True)

    def progress(current):
        print(
            f"Progresso: {current.checked_combinations}/{current.total_combinations} "
            f"combinações efetivamente verificadas; "
            f"{current.independent_sets} independentes; {current.elapsed_seconds:.3f} s",
            flush=True,
        )

    stats = search_exhaustively(
        context, args.k, on_independent=show_independent,
        progress=progress, progress_interval=args.intervalo_progresso,
    )
    cache = context.cache_info()
    print(f"\nTotal de combinações: {stats.total_combinations}")
    print(f"Combinações efetivamente verificadas: {stats.checked_combinations}")
    print(f"Conjuntos convexamente independentes: {stats.independent_sets}")
    if cache.maxsize:
        print(f"Consultas de fechos atendidas pelo cache: {cache.hits}")
        print(f"Consultas de fechos sem resultado no cache: {cache.misses}")
        print(f"Entradas finais no cache: {cache.currsize}/{cache.maxsize}")
    else:
        print("Cache de fechos: desativado.")
    print(f"Tempo da busca: {stats.elapsed_seconds:.3f} s")
    print(f"Tempo total: {perf_counter() - start:.3f} s")

    if args.plotar:
        from plotando_grafos import plotar_grafo

        plotar_grafo(graph)
    return stats


if __name__ == "__main__":
    main()
