from libs import *

"""
======================================== COMENTÁRIOS ========================================

Testando hipótese

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

S = ['v(0,1)', 'v(0,2)', 'v(0,3)', 'v(0,4)', 'v(1,2)', 'v(1,3)', 'v(1,4)', 'v(2,3)', 'v(2,4)', 'v(3,4)']

space()

print('Fecho convexo de S.')
print(geodetic_hull(GGc, S))

space()

print(f'Verifica se {S} é convexamente independente.')
print(geodetic_rank(GGc, S))

plotar_grafo(G)