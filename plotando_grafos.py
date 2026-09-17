from libs import *

def plotar_grafo(G):
    pos = nx.shell_layout(G)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=800,
        font_size=10
    )

    plt.show()