from libs import *


def prisma_complementar(G):
    Gc = gerar_complemento(G)
    GGc = nx.compose(G, Gc)

    for i,j in zip(nx.nodes(G), nx.nodes(Gc)):
        GGc.add_edge(i, j)
    
    return GGc


