# unified_graph_builder.py
import networkx as nx
import json
from datetime import datetime

class UnifiedKnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_types = {
            'attractor', 'concept', 'agent', 'tool', 
            'anchor', 'metaphor', 'protocol'
        }
    
    def add_resonance_map(self, map_data):
        """Integruje mapę rezonansową z grafem"""
        for attractor in map_data['resonance_map']['attractors']:
            self.graph.add_node(
                attractor['id'],
                node_type='attractor',
                **attractor
            )
    
    def add_conversation_log(self, log_path):
        """Dodaje konwersacje jako ścieżki w grafie"""
        # Parsowanie logów i ekstrakcja relacji
        pass
    
    def calculate_resonance_paths(self, start_node, max_depth=3):
        """Znajduje ścieżki rezonansu między węzłami"""
        paths = []
        for target_type in ['attractor_light', 'anchor']:
            for node in self.graph.nodes(data=True):
                if node[1].get('type') == target_type:
                    try:
                        path = nx.shortest_path(
                            self.graph, start_node, node[0]
                        )
                        paths.append({
                            'path': path,
                            'length': len(path),
                            'target_energy': node[1].get('energy_metrics', {}).get('potential_energy', 1)
                        })
                    except nx.NetworkXNoPath:
                        continue
        
        return sorted(paths, key=lambda x: x['length'] + x['target_energy'])
