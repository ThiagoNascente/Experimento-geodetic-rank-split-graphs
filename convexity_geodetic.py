from libs import *

def geodetic_hull(G, S):
    R = set(S.copy())

    while True:
        novo_R = set(R)

        # Analisa cada par de vértices atualmente no conjunto
        for u, v in combinations(R, 2):

            # Pode não existir caminho se G for desconexo
            if not nx.has_path(G, u, v):
                continue

            # Obtém todos os caminhos mínimos entre u e v
            for caminho in nx.all_shortest_paths(G, u, v):
                novo_R.update(caminho)

        # Se nenhum vértice novo foi acrescentado,
        # encontramos o fecho
        if novo_R == R:
            break

        R = novo_R

    return R


def geodetic_rank(G,S):
    S_set = set(S)
    fecho_base = geodetic_hull(G, S)
    for i in S:
        copia = S_set.copy()
        copia.remove(i)
        #print(copia)
        fecho = geodetic_hull(G, copia)
        if fecho == fecho_base:
            print(i)
            return False

    return True