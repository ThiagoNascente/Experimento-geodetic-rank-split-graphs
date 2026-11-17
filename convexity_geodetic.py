"""Fechos geodéticos e busca exata de conjuntos convexamente independentes."""

from dataclasses import dataclass
from math import comb
from time import perf_counter

import networkx as nx

__all__ = [
    "GeodeticConvexity",
    "SearchStats",
    "geodetic_hull",
    "geodetic_rank",
    "geodetic_rank_antiga",
]


@dataclass
class SearchStats:
    total_combinations: int = 0
    extensions_tested: int = 0
    pruned_combinations: int = 0
    independent_sets: int = 0
    elapsed_seconds: float = 0.0

    @property
    def resolved_combinations(self):
        return self.pruned_combinations + self.independent_sets


class GeodeticConvexity:
    """Pré-calcula intervalos de um grafo não direcionado, sem pesos.

    Cada conjunto é representado internamente por uma máscara de bits. A
    instância representa o grafo no momento da criação: crie outra instância
    se suas arestas ou seus vértices forem alterados.
    """

    def __init__(self, graph):
        if graph.is_directed():
            raise nx.NetworkXNotImplemented("Use um grafo não direcionado.")

        self.nodes = tuple(graph)
        self._index = {node: i for i, node in enumerate(self.nodes)}
        self._bits = tuple(1 << i for i in range(len(self.nodes)))
        self._all_nodes = (1 << len(self.nodes)) - 1

        distances = dict(nx.all_pairs_shortest_path_length(graph))
        interiors = [[0] * len(self.nodes) for _ in self.nodes]
        partners = [0] * len(self.nodes)
        for i, u in enumerate(self.nodes):
            for j in range(i + 1, len(self.nodes)):
                v = self.nodes[j]
                distance = distances[u].get(v)
                if distance is None or distance <= 1:
                    continue

                # w pertence a I(u, v) sse d(u,w) + d(w,v) = d(u,v).
                # Os extremos já estão no fecho; armazenamos só o interior.
                interior = 0
                for w, duw in distances[u].items():
                    dwv = distances[v].get(w)
                    if w != u and w != v and dwv is not None and duw + dwv == distance:
                        interior |= self._bits[self._index[w]]
                interiors[i][j] = interiors[j][i] = interior
                if interior:
                    partners[i] |= self._bits[j]
                    partners[j] |= self._bits[i]

        self._interiors = tuple(tuple(row) for row in interiors)
        self._partners = tuple(partners)

    def _mask(self, vertices):
        mask = 0
        for vertex in vertices:
            if vertex not in self._index:
                raise nx.NodeNotFound(f"Vértice ausente do grafo: {vertex!r}")
            mask |= self._bits[self._index[vertex]]
        return mask

    def _vertices(self, mask):
        return tuple(node for i, node in enumerate(self.nodes) if mask & self._bits[i])

    def _extend_hull(self, closed, additions, target=0):
        """Fecha um conjunto já fechado após adições.

        Com target, pode terminar assim que esse vértice for alcançado. Nesse
        caso o resultado parcial só deve ser usado para testar dependência.
        """
        processed = closed
        pending = additions & ~closed
        closed |= pending
        if closed & target:
            return closed

        while pending:
            bit = pending & -pending
            pending ^= bit
            index = bit.bit_length() - 1
            others = processed & self._partners[index]
            row = self._interiors[index]
            while others:
                other = others & -others
                others ^= other
                extra = row[other.bit_length() - 1] & ~closed
                if extra:
                    closed |= extra
                    if closed & target:
                        return closed
                    pending |= extra
            processed |= bit

        return closed

    def hull(self, vertices):
        """Retorna o fecho como set, incluindo todas as iterações necessárias."""
        return set(self._vertices(self._extend_hull(0, self._mask(vertices))))

    def is_independent(self, vertices):
        mask = self._mask(vertices)
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            if self._extend_hull(0, mask ^ bit, bit) & bit:
                return False
        return True

    def independent_sets(self, size, *, stats=None, progress=None, progress_interval=5.0):
        """Gera exatamente os conjuntos independentes do tamanho solicitado.

        A independência é hereditária: se T é dependente, todo S contendo T
        também é dependente. Cada ramo descartado contabiliza C(r, k-|T|)
        combinações, sem precisar enumerá-las. A ordem dos resultados é a
        mesma de itertools.combinations(graph.nodes(), size).
        """
        if size < 0:
            raise ValueError("O tamanho do conjunto deve ser não negativo.")
        if progress_interval <= 0:
            raise ValueError("O intervalo de progresso deve ser positivo.")
        if stats is None:
            stats = SearchStats()
        stats.total_combinations = comb(len(self.nodes), size)
        stats.extensions_tested = 0
        stats.pruned_combinations = 0
        stats.independent_sets = 0
        stats.elapsed_seconds = 0.0
        start = perf_counter()
        last_report = start

        def report(force=False):
            nonlocal last_report
            now = perf_counter()
            stats.elapsed_seconds = now - start
            if progress is not None and (force or now - last_report >= progress_interval):
                progress(stats)
                last_report = now

        def search(chosen, candidates, hull, deletion_hulls, needed):
            # x em hull(S) implica que S + {x} é dependente.
            available = candidates & ~hull
            stats.pruned_combinations += (
                comb(candidates.bit_count(), needed) - comb(available.bit_count(), needed)
            )
            candidates = available
            while candidates.bit_count() >= needed:
                bit = candidates & -candidates
                candidates ^= bit
                stats.extensions_tested += 1
                if stats.extensions_tested % 512 == 0:
                    report()

                new_deletions = []
                for old_bit, old_hull in zip(chosen, deletion_hulls):
                    # hull(hull(S - {v}) + {x}) = hull((S - {v}) + {x}).
                    updated = self._extend_hull(old_hull, bit, old_bit)
                    if updated & old_bit:
                        stats.pruned_combinations += comb(candidates.bit_count(), needed - 1)
                        break
                    new_deletions.append(updated)
                else:
                    new_chosen = (*chosen, bit)
                    if needed == 1:
                        stats.independent_sets += 1
                        yield tuple(self.nodes[b.bit_length() - 1] for b in new_chosen)
                    else:
                        new_hull = self._extend_hull(hull, bit)
                        yield from search(
                            new_chosen,
                            candidates,
                            new_hull,
                            (*new_deletions, hull),
                            needed - 1,
                        )

        try:
            if size == 0:
                stats.independent_sets = 1
                yield ()
            elif size <= len(self.nodes):
                yield from search((), self._all_nodes, 0, (), size)
        finally:
            report(force=True)


def _context(graph):
    return graph if isinstance(graph, GeodeticConvexity) else GeodeticConvexity(graph)


def geodetic_hull(G, S):
    """Aceita um grafo ou um GeodeticConvexity reutilizável."""
    return _context(G).hull(S)


def geodetic_rank(G, S):
    """Verifica independência; aceita um contexto pré-calculado reutilizável."""
    return _context(G).is_independent(S)


def geodetic_rank_antiga(G, S):
    context = _context(G)
    vertices = set(S)
    base_hull = context.hull(vertices)
    for vertex in vertices:
        if context.hull(vertices - {vertex}) == base_hull:
            print(vertex)
            return False
    return True
