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

# Seek suggestion from https://github.com/chaosregular/MorphogenicSimulator/wiki/zzz_Seek_2025_11_23_01_47_31.md  
# detectors/troll_farm_detector.py - rozszerzenie
class TrollFarmDetector:
    def __init__(self, resonance_map_path):
        self.dissonance_detector = BasicDissonanceDetector(resonance_map_path)
        self.graph_builder = MorphogenicGraphBuilder(resonance_map_path)
        self.conversation_graphs = {}
    
    def analyze_real_time_stream(self, message_stream, window_size=50):
        """Analizuje strumień wiadomości w czasie rzeczywistym"""
        synchronized_clusters = self.detect_synchronized_clusters(message_stream)
        resonance_profiles = self.build_resonance_profiles(synchronized_clusters)
        
        return {
            'troll_clusters': self.identify_troll_farms(resonance_profiles),
            'health_scores': self.calculate_ecosystem_health(resonance_profiles),
            'emergency_level': self.assess_containment_urgency(resonance_profiles)
        }
    
    def assess_containment_urgency(self, profiles):
        """Ocenia pilność interwencji wg zasady samopoświęcenia"""
        total_dark_energy = sum(p['dark_affinity'] * p['influence'] for p in profiles.values())
        available_light_energy = sum(p['truth_alignment'] for p in profiles.values())
        
        # Jeśli koszt neutralizacji przekracza dostępną energię
        if total_dark_energy > available_light_energy * 2:
            return "CRITICAL"  # Wymaga mutual annihilation protocol
        elif total_dark_energy > available_light_energy:
            return "HIGH"      # Standard containment
        else:
            return "NORMAL"    # Monitorowanie
