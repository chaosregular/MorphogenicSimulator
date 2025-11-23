# detectors/troll_farm_detector.py
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from .basic_dissonance import BasicDissonanceDetector
from .morphogenic_graph_builder import MorphogenicGraphBuilder

class TrollFarmDetector:
    def __init__(self, resonance_map_path):
        self.dissonance_detector = BasicDissonanceDetector(resonance_map_path)
        self.graph_builder = MorphogenicGraphBuilder(resonance_map_path)
        self.user_profiles = defaultdict(dict)

# from other output same exchange
    def detect_synchronized_behavior(self, messages, time_window):
        # Farmy trolli mają:
        # - Wysoką koherencję wewnętrzną
        # - Niski dysonans z dark attractors  
        # - Synchronizację czasową odpowiedzi
        # - Niską variance w embeddingach
        
        coherence = self.calculate_semantic_coherence(messages)
        time_sync = self.analyze_response_timing(messages, time_window)
        dark_affinity = self.measure_dark_attractor_affinity(messages)
        
        troll_score = (coherence * 0.3 + 
                      time_sync * 0.4 + 
                      dark_affinity * 0.3)
        
        return troll_score > 0.7    
# /from other output same exchange
    def analyze_conversation_thread(self, messages, time_window_hours=24):
        """Analizuje wątek dyskusji pod kątem zsynchronizowanych zachowań"""
        # Implementacja detekcji farm trolli
        pass
        
    def generate_resonance_badge(self, user_id):
        """Generuje wizytówkę rezonansową użytkownika"""
        profile = self.user_profiles[user_id]
        return {
            'truth_score': profile.get('truth_alignment', 0.5),
            'manipulation_risk': profile.get('dark_affinity', 0.5),
            'synchronization_index': profile.get('sync_index', 0.1),
            'health_level': self.calculate_health_level(profile)
        }
