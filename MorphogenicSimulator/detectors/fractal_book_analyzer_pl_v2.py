# morphogenic_graph_builder.py
import networkx as nx
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer  # Z requirements
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity  # Dla wag

class MorphogenicGraphBuilder:
    def __init__(self, resonance_map_path, fractal_data_path=None):
        self.graph = nx.MultiDiGraph()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.resonance_map = self.load_resonance_map(resonance_map_path)
        self.node_types = {'attractor', 'concept', 'occurrence', 'triad', 'agent', 'tool', 'anchor', 'metaphor', 'protocol'}
        if fractal_data_path:
            self.fractal_data = self.load_fractal_data(fractal_data_path)
            self.integrate_fractal_data()
    
    def load_resonance_map(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_fractal_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)  # Zakładam JSON z test_out_niezw_001.txt
    
    def add_resonance_map(self):
        """Integruje mapę rezonansową z grafem (z szkicu Seeka)"""
        for attractor in self.resonance_map['resonance_map']['attractors']:
            self.graph.add_node(
                attractor['id'],
                node_type='attractor',
                **attractor,
                embedding=self.model.encode(attractor['name'] + ' ' + attractor['description'])
            )
    
    # def integrate_fractal_data(self):
    #     """Dodaje dane fraktalne z Lema: wystąpienia słów i triady jako węzły/krawędzie"""
    #     for word, data in self.fractal_data.get('themes', {}).items():
    #         for i, occ in enumerate(data['word_occurrences']):
    #             node_id = f"{word}_occ_{occ['global_pos']}"
    #             self.graph.add_node(node_id, node_type='occurrence',
    #                                 word=word, global_pos=occ['global_pos'],
    #                                 level=occ['level'], embedding=self.model.encode(word))
                
    #             # Dodaj triadę jako węzły i krawędzie
    #             if 'sample_triads' in data and i < len(data['sample_triads']):
    #                 triad = data['sample_triads'][i]
    #                 triad_id = f"triad_{node_id}"
    #                 self.graph.add_node(triad_id, node_type='triad', **triad,
    #                                     embedding=self.model.encode(f"{triad['cause']} {triad['core']} {triad['effect']}"))
                    
    #                 # Krawędzie triady z siłami (cosine + odległość #)
    #                 self.graph.add_edge(triad['cause'], triad_id, weight=1.0 / (abs(occ['global_pos'] - occ['global_pos']) + 1))
    #                 self.graph.add_edge(triad_id, triad['effect'], weight=1.0 / (abs(occ['global_pos'] - occ['global_pos']) + 1))
    

def integrate_fractal_data(self):
    # Teraz tylko themes, nie cały stdout
    for word, data in self.fractal_data.items():  # themes, nie fractal_data['themes']
        for i, triad in enumerate(data['sample_triads']):
            triad_id = f"CRT_{word}_{i}_{data['frequency']}"
            # ... reszta bez zmian ...
            self.graph.add_node(triad_id, node_type='triad', **triad,
                                embedding=self.model.encode(f"{triad['cause']} {triad['core']} {triad['effect']}"))

            self.graph.add_edge(triads['cause'], triad_id, weight=0.1, force='causal')
            self.graph.add_edge(triad_id, triads['effect'], weight=0.1, force='resonance')

    def calculate_dissonance_weights(self, node_id):
        """Oblicza wagi dysonansu dla węzła względem atraktorów (integracja z basic_dissonance)"""
        node_emb = self.graph.nodes[node_id]['embedding']
        weights = {}
        for attr_id, attr_emb in self.get_attractor_embeddings().items():
            sim = cosine_similarity([node_emb], [attr_emb])[0][0]
            attr = next(a for a in self.resonance_map['resonance_map']['attractors'] if a['id'] == attr_id)
            dissonance = 1 - sim if attr['type'] == 'dark' else sim
            weights[attr_id] = dissonance * attr['energy_metrics']['maintenance_cost']  # Waga energetyczna
        return weights
    
    def get_attractor_embeddings(self):
        """Embeddingi atraktorów"""
        return {a['id']: self.graph.nodes[a['id']]['embedding'] for a in self.resonance_map['resonance_map']['attractors']}
    
    def calculate_resonance_paths(self, start_node, max_depth=3):
        """Znajduje ścieżki rezonansu (z szkicu, z wagami dysonansu)"""
        self.add_resonance_map()  # Upewnij się, że atraktory są
        paths = []
        for target_type in ['attractor_light', 'anchor']:  # Z Trace: proto-light
            for node in self.graph.nodes(data=True):
                if node[1].get('node_type') == target_type.replace('_', '-'):  # Adaptacja
                    try:
                        # Ścieżka z wagami dysonansu (Gemini: semantic_velocity ≈ 1 / length)
                        path = nx.shortest_path(self.graph, start_node, node[0], weight='weight')
                        path_weight = sum(self.graph[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
                        paths.append({
                            'path': path,
                            'length': len(path),
                            'total_dissonance': path_weight,
                            'target_energy': node[1].get('energy_metrics', {}).get('potential_energy', 1),
                            'velocity': 1.0 / path_weight if path_weight > 0 else 0  # Semantic velocity
                        })
                    except nx.NetworkXNoPath:
                        continue
        return sorted(paths, key=lambda x: x['length'] + x['total_dissonance'] + x['target_energy'])
    
    def evolve_triads(self, triad_id, iterations=5, attractor_id='attractor_dark_koryto'):
        """Symulacja ewolucji triad (z Gemini: fizyka cząstek, flip_force)"""
        triad_node = self.graph.nodes[triad_id]
        current_emb = triad_node['embedding']
        for _ in range(iterations):
            # Siła od atraktora (short-range dla dark)
            attr_emb = self.graph.nodes[attractor_id]['embedding']
            force = (attr_emb - current_emb) * 0.1  # Prosta dynamika
            current_emb += force + np.random.normal(0, 0.01, current_emb.shape)  # Szum + flip
            triad_node['embedding'] = current_emb  # Update
        return triad_node  # Zwróć ewoluowaną triadę
    
    def visualize(self, output_path='lem_graph.html'):
        """Wizualizacja z PyVis (toroidalna orbita)"""
        try:
            from pyvis.network import Network
            net = Network(notebook=False, height='800px', width='100%', directed=True)
            net.from_nx(self.graph)
            net.show(output_path)
            print(f"Wizualizacja zapisana: {output_path}")
        except ImportError:
            print("Zainstaluj pyvis: pip install pyvis")

# Przykład użycia
if __name__ == "__main__":
    builder = MorphogenicGraphBuilder('first_prototype.json',
                                      'themes_niezwyciezony.json')  # Z Lema
    paths = builder.calculate_resonance_paths('ludzie_occ_512')  # Start od triady Lema
    print("Top rezonansowe ścieżki:", json.dumps(paths[:3], indent=2))
    builder.evolve_triads('triad_ludzie_occ_512', attractor_id='attractor_dark_koryto')
    builder.visualize()
