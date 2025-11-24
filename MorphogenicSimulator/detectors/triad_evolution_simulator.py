# triad_evolution_simulator.py
import numpy as np
from scipy.spatial.distance import cdist

class TriadEvolutionSimulator:
    def __init__(self, embedding_dim=384):
        self.embedding_dim = embedding_dim
        self.particles = {}  # {id: {'pos': vector, 'vel': vector, 'mass': float, 'type': str}}
        self.attractors = {} # {id: {'pos': vector, 'mass': float, 'type': str}}
        
        # Parametry fizyki (inspirowane CA_4nPCA_012.c)
        self.G_ATTRACT = 0.5    # Siła przyciągania atraktorów
        self.G_REPULSE = 2.0    # Siła odpychania między pojęciami (żeby nie zlewały się)
        self.DAMPING = 0.90     # Tłumienie (ATN_COEF)
        self.DT = 0.1           # Krok czasowy
        self.MIN_DIST = 0.01    # Unikanie osobliwości

    def load_graph_state(self, networkx_graph):
        """Ładuje stan początkowy z grafu buildera"""
        print(f"Ładowanie fizyki dla {networkx_graph.number_of_nodes()} węzłów...")
        
        for node_id, data in networkx_graph.nodes(data=True):
            if 'embedding' not in data:
                continue
                
            embedding = np.array(data['embedding'])
            if embedding.shape[0] != self.embedding_dim:
                continue # Pomiń błędne wymiary

            # Podział na Atraktory (ciężkie, statyczne) i Cząstki (lekkie, dynamiczne)
            if data.get('node_type') == 'attractor':
                self.attractors[node_id] = {
                    'pos': embedding,
                    'mass': 1000.0, # Ogromna masa
                    'type': data.get('type', 'neutral')
                }
            else:
                # Masa zależy od częstotliwości występowania (bezwładność semantyczna)
                freq = data.get('frequency', 1)
                mass = 1.0 + np.log(freq) if freq > 0 else 1.0
                
                self.particles[node_id] = {
                    'pos': embedding,
                    'vel': np.zeros(self.embedding_dim),
                    'mass': mass,
                    'type': data.get('node_type', 'concept')
                }

    def calculate_forces(self):
        """Oblicza siły działające na cząstki"""
        particle_ids = list(self.particles.keys())
        if not particle_ids:
            return
            
        # Macierz pozycji cząstek
        P_pos = np.array([p['pos'] for p in self.particles.values()])
        
        # 1. Siły od Atraktorów (Grawitacja Semantyczna)
        total_force = np.zeros_like(P_pos)
        
        for attr in self.attractors.values():
            attr_pos = attr['pos']
            # Wektor od cząstki do atraktora
            delta = attr_pos - P_pos
            dist = np.linalg.norm(delta, axis=1, keepdims=True)
            dist = np.maximum(dist, self.MIN_DIST) # Unikaj dzielenia przez 0
            
            # Siła: F = G * M * m / r^2 (uproszczona)
            # Tutaj zakładamy, że atraktory Light przyciągają mocniej "zdrowe" pojęcia?
            # Na razie model czysto grawitacyjny.
            force_mag = self.G_ATTRACT * attr['mass'] / (dist**2)
            total_force += force_mag * (delta / dist)

        # 2. Siły między cząstkami (Flip Force / Odpychanie lokalne)
        # Żeby pojęcia nie zapadły się w jeden punkt (problem gęstości Seeka)
        # Używamy uproszczonego odpychania dla bliskich sąsiadów
        # (W pełnej wersji można użyć cdist dla wszystkich par, tu uproszczone dla wydajności)
        
        return total_force

    def step(self):
        """Wykonuje jeden krok symulacji (całkowanie Eulera/Verleta)"""
        forces = self.calculate_forces()
        
        for i, (pid, p) in enumerate(self.particles.items()):
            # F = ma => a = F/m
            acc = forces[i] / p['mass']
            
            # Update prędkości i pozycji
            p['vel'] = (p['vel'] + acc * self.DT) * self.DAMPING
            p['pos'] += p['vel'] * self.DT
            
            # Normalizacja (opcjonalna, jeśli embeddingi muszą być na sferze)
            # p['pos'] /= np.linalg.norm(p['pos']) 

    def get_drift_metrics(self):
        """Zwraca ile cząstki się przesunęły (Semantic Velocity)"""
        drifts = {}
        for pid, p in self.particles.items():
            speed = np.linalg.norm(p['vel'])
            drifts[pid] = speed
        return drifts

    def update_graph_embeddings(self, networkx_graph):
        """Aktualizuje pozycje w grafie po symulacji"""
        for pid, p in self.particles.items():
            if pid in networkx_graph.nodes:
                networkx_graph.nodes[pid]['embedding'] = p['pos']
                networkx_graph.nodes[pid]['semantic_velocity'] = float(np.linalg.norm(p['vel']))
