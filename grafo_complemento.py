from libs import *

def gerar_complemento(G):
    """
        1   -> '1c'
        C1  -> 'C1c'
        I3  -> 'I3c'
    """

    G_complemento = nx.Graph()

    # Novos vértices
    for v in G.nodes():
        G_complemento.add_node(f"{v}c")

    vertices = list(G.nodes())

    # Adiciona_arestas
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            u = vertices[i]
            v = vertices[j]

            if not G.has_edge(u, v) and not G.has_edge(v, u):
                G_complemento.add_edge(f"{u}c", f"{v}c")

    return G_complemento