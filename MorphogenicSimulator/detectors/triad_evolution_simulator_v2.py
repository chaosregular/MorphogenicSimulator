import numpy as np
from alp_operator import ALPOperator

class TriadEvolutionSimulatorV2:
    def __init__(self, alp_operator):
        self.alp = alp_operator
        self.particles = {} 
        
        # Fizyka
        self.DAMPING = 0.90
        self.DT = 0.1
        self.FLIP_FORCE_MAG = 0.5  # Siła "prostowania" pojęć przez ALP

    def load_particles(self, graph_nodes):
        # (Logika ładowania z grafu bez zmian - jak w v1)
        pass

    def calculate_forces(self):
        for pid, p in self.particles.items():
            # 1. Siła od ALP (Operatora)
            # Zamiast ciągnąć do punktu, obliczamy gradient lokalny
            # "W którą stronę muszę zmienić znaczenie, by być bardziej Prawdziwym?"
            force_alp = self.alp.get_gradient(p['pos']) * self.FLIP_FORCE_MAG
            
            # 2. Siła bezwładności semantycznej (opór przed zmianą)
            # Im częstsze słowo (większa masa), tym trudniej je zmienić
            force_resist = -p['vel'] * p['mass'] * 0.1
            
            p['force'] = force_alp + force_resist

    def step(self):
        self.calculate_forces()
        
        for p in self.particles.values():
            acc = p['force'] / p['mass']
            p['vel'] = (p['vel'] + acc * self.DT) * self.DAMPING
            p['pos'] += p['vel'] * self.DT
            
            # Oblicz aktualne Δ(T,R,E) dla nowej pozycji
            p['current_delta'] = self.alp.evaluate_state(p['pos'])

    def get_state_report(self):
        """Raportuje które pojęcia dryfują w stronę światła, a które w mrok"""
        report = {}
        for pid, p in self.particles.items():
            report[pid] = {
                'velocity': np.linalg.norm(p['vel']),
                'delta_tre': p.get('current_delta', 0.5)
            }
        return report
