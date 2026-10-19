from libs import *

"""
======================================== COMENTÁRIOS ========================================

Aqui testamos um caso onde o prisma complementar GGc do grafo split G tem rank no máximo 
possível, ou seja, o número 8. Observamos sempre o grafo complemento, pois o grafo induzido
Gc²[Cc] é um grafo conexo

=============================================================================================
"""

def space():
    print('\n==============================\n')


G = gerar_split_experimento_3() # GERANDO O GRAFO ESPECIFICO PARA ESSE EXPERIMENTO

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

S = ['C4c','C3c','C2c','I0c', 'I1c', 'I2c', 'I3c','I4'] # 8


space()

print('Fecho convexo de S.')
print(geodetic_hull(GGc, S))

space()

print(f'Verifica se {S} é convexamente independente.')
print(geodetic_rank(GGc, S))

plotar_grafo(G)