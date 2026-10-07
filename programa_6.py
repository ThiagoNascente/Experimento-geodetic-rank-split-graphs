from libs import *

"""
======================================== COMENTÁRIOS ========================================

Aqui tentaremos testar a configuração ótima para o menor conjunto de envoltória em um grafo split
onde G²[I] é conexo.

=============================================================================================
"""

def space():
    print('\n==============================\n')


G = gerar_split_especifico_3()

GGc = prisma_complementar(G)

space()

print('Considere G um grafo split qualquer.')
print('Não consideramos que a clique ou independet set são máximos!\nDevido a aleatoriedade, um vértice do independent set pode se conectar com toda a clique.')

space()

print('Vértices do GGc')
print(GGc.nodes())

space()

print('Arestas do GGc')
print(GGc.edges())

S = ['C2','C3', 'C4', 'C5', 'C6', 'I0', 'I1', 'I2', 'I3', 'I4', 'C0c', 'C1c']

space()

print('Fecho convexo de S.')
print(geodetic_hull(GGc, S))

space()

print(f'Verifica se {S} é convexamente independente.')
print(geodetic_rank(GGc, S))

plotar_grafo(G)