from libs import *


def gerar_split(tamanho_clique, tamanho_independente, probabilidade=0.5, seed=None):
    if probabilidade == None:
        probabilidade = random.random()
    random.seed(seed)

    G = nx.Graph()

    # Vértices da clique e do conjunto independente
    clique = [f"C{i}" for i in range(tamanho_clique)]
    independente = [f"I{i}" for i in range(tamanho_independente)]

    G.add_nodes_from(clique, tipo="clique")
    G.add_nodes_from(independente, tipo="independente")

    # Forma a clique
    for i in range(tamanho_clique):
        for j in range(i + 1, tamanho_clique):
            G.add_edge(clique[i], clique[j])

    # Arestas arbitrárias entre a clique e o conjunto independente
    for u in clique:
        for v in independente:
            if random.random() < probabilidade:
                G.add_edge(u, v)

    return G