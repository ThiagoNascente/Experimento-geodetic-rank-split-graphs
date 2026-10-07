from libs import *

"""
======================================== COMENTÁRIOS ========================================

Aqui testamos para G²[I] desconexos, onde a condição de que somente um elemento correspondente
da clique que podemos selecionar para entrar em S, uma vez que se tivessem mais, quebrariam pois
configuram casos ruins observados em Gc. Interessante que sempre que desejamos fugir de uma
seleção em G, precisamos observar se ela não acontece no fecho em Gc. Isso dificulta...

=============================================================================================
"""

def space():
    print('\n==============================\n')


G = gerar_split_especifico_5()

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

S = ['C3', 'C4', 'C5', 'C6', 'I0', 'I1', 'I2', 'I3', 'I4', 'I5', 'C1c']

space()

print('Fecho convexo de S.')
print(geodetic_hull(GGc, S))

space()

print(f'Verifica se {S} é convexamente independente.')
print(geodetic_rank(GGc, S))

plotar_grafo(G)