class DissonanceDetector:
    def __init__(self, resonance_map):
        self.resonance_map = resonance_map
        self.thresholds = {
            'high_dissonance': 0.7,
            'medium_dissonance': 0.4,
            'low_dissonance': 0.1
        }
    
    def analyze_statement(self, statement_text, context_attractors):
        """
        Analizuje wypowiedź pod kątem dysonansu z otaczającymi atraktora
        """
        statement_embedding = get_semantic_embedding(statement_text)
        
        dissonance_scores = []
        for attractor in context_attractors:
            # Oblicz odległość od każdego atraktora w przestrzeni semantycznej
            distance = cosine_distance(statement_embedding, attractor['semantic_center'])
            dissonance_scores.append(distance * attractor['resonance_strength'])
        
        return {
            'overall_dissonance': max(dissonance_scores),
            'closest_attractor': min(dissonance_scores),
            'dissonance_vector': dissonance_scores
        }
