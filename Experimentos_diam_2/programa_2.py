
from libs import *
from itertools import combinations
from math import comb

"""
======================================== COMENTÁRIOS ========================================

Testando hipótese - Conjuntos convexamente independentes de tamanho 11

=============================================================================================
"""

def space():
    print('\n==============================\n')


Gi = nx.path_graph(5)
Gi = nx.relabel_nodes(Gi, lambda v: str(v))

G = construir_grafo(Gi)
GGc = prisma_complementar(G)

print('Vértices do GGc')
print(GGc.nodes())

space()

print('Arestas do GGc')
print(GGc.edges())

space()

# Todos os vértices do prisma complementar
vertices = list(GGc.nodes())

# Tamanho dos conjuntos a serem testados
k = 11

total = comb(len(vertices), k)
contador = 0
independentes = 0

print(f'Total de combinações: {total}')

# Testar todas as combinações com 11 vértices
for S_tupla in combinations(vertices, k):
    S = list(S_tupla)
    contador += 1

    # Verificar se S é convexamente independente
    if geodetic_rank(GGc, S):
        independentes += 1

        print(f'\nConjunto independente encontrado: {S}')

        # Calcular o fecho geodético
        print(f'Fecho: {geodetic_hull(GGc, S)}')

    # Mostrar progresso a cada 100.000 combinações
    if contador % 1000 == 0:
        print(f'Progresso: {contador}/{total}')

space()

print(f'Total de conjuntos testados: {contador}')
print(f'Conjuntos convexamente independentes: {independentes}')

plotar_grafo(G)
