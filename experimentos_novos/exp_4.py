from libs import *

"""
======================================== COMENTÁRIOS ========================================

teste

=============================================================================================
"""

def space():
    print('\n==============================\n')


G = gerar_split_experimento_4() # GERANDO O GRAFO ESPECIFICO PARA ESSE EXPERIMENTO
Gc = gerar_complemento(G)

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

S = ['I0', 'I1', 'I2', 'I3', 'I4', 'C4', 'C5','C1c','C2c']


space()

print('Fecho convexo de S.')
print(geodetic_hull(GGc, S))

space()

print(f'Verifica se {S} é convexamente independente.')
print(geodetic_rank(GGc, S))

plotar_grafo(G)
plotar_grafo(Gc)