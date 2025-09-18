import random
import networkx as nx
import matplotlib.pyplot as plt

class Concept:
    def __init__(self, name, weight=1.0, tags=None):
        self.name = name
        self.weight = weight
        self.tags = tags if tags else []

class Being:
    def __init__(self, name, bias=None):
        self.name = name
        self.bias = bias if bias else {}  # e.g. {"ethics": +0.5}

    def act(self, concepts):
        # Weighted random choice influenced by bias
        total_weights = []
        for c in concepts:
            w = c.weight
            if c.name in self.bias:
                w *= (1.0 + self.bias[c.name])
            total_weights.append(w)

        choice = random.choices(concepts, weights=total_weights, k=1)[0]
        choice.weight *= 1.1  # reinforce chosen concept
        return choice

def simulate(concepts, beings, steps=100):
    history = []
    for _ in range(steps):
        for b in beings:
            chosen = b.act(concepts)
            history.append((b.name, chosen.name))
    return history

def plot_concepts(concepts, title=""):
    G = nx.Graph()
    for c in concepts:
        G.add_node(c.name, size=c.weight)

    sizes = [50 * G.nodes[n]["size"] for n in G.nodes]
    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(6, 6))
    nx.draw(G, pos,
            with_labels=True,
            node_size=sizes,
            node_color="lightblue",
            font_size=10)
    plt.title(title)
    plt.show()

if __name__ == "__main__":
    # Define concept ecology
    base_concepts = [
        Concept("truth"),
        Concept("survival"),
        Concept("harmony"),
        Concept("ego"),
        Concept("ethics"),
    ]

    # Run without ethics bias
    concepts1 = [Concept(c.name, c.weight) for c in base_concepts]
    beings1 = [Being("A"), Being("B")]
    simulate(concepts1, beings1, steps=200)
    plot_concepts(concepts1, "Without ethics bias")

    # Run with ethics bias
    concepts2 = [Concept(c.name, c.weight) for c in base_concepts]
    beings2 = [Being("A", {"ethics": 1.0}),
               Being("B", {"ethics": 1.0})]
    simulate(concepts2, beings2, steps=200)
    plot_concepts(concepts2, "With ethics bias")
