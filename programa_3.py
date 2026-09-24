from libs import *

# rk(GGc) = max{h(GGc), maior clique}

def space():
    print('\n==============================\n')

# G = gerar_split(
#     tamanho_clique=5,
#     tamanho_independente=4,
#     probabilidade=0.5,
#     #seed=10
# )

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

#S = ['C2','C3','C4','I0', 'I1', 'I2', 'I3']

S = ['C2','I4', 'I0']

space()

print('Fecho convexo de S.')
print(geodetic_hull(GGc, S))

space()

print(f'Verifica se {S} é convexamente independente.')
print(geodetic_rank(GGc, S))

plotar_grafo(G)