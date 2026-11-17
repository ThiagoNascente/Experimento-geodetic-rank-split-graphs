from libs import *

def construir_grafo(G):
    H = G.copy()
    vertices = list(G.nodes())
    clique = []

    # Criar os vértices v(a,b)
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            a = vertices[i]
            b = vertices[j]

            v_ab = f"v({a},{b})"

            H.add_edge(v_ab, a)
            H.add_edge(v_ab, b)

            clique.append(v_ab)

    # Construir a clique com os novos vértices
    H.add_edges_from(nx.complete_graph(clique).edges())

    return H
