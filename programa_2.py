from libs import *

"""
======================================== COMENTÁRIOS ========================================

Aqui testamos a segunda hipótese, a de que selecionamos o rank de Gi e um vértice que chamo de
ponte, um dos representantes que possui adjacência com todos do conjunto independente selecionado
para o maior conjunto convexamente independente do split Gi. Lembrando que somos obrigados a
observar somente o split com cada componente conexa de G²[I].

=============================================================================================
"""

def space():
    print('\n==============================\n')


G = gerar_split_especifico_2()

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

S = ['C2','C3', 'C4', 'C5', 'C6', 'I0', 'I1', 'I2', 'I3', 'I4', 'C0c']

space()

print('Fecho convexo de S.')
print(geodetic_hull(GGc, S))

space()

print(f'Verifica se {S} é convexamente independente.')
print(geodetic_rank(GGc, S))

plotar_grafo(G)