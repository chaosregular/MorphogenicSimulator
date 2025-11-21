import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class BasicDissonanceDetector:
    def __init__(self, resonance_map_path):
        self.resonance_map = self.load_resonance_map(resonance_map_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Lekki model embeddingów
        
    def load_resonance_map(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_attractor_embeddings(self):
        """Tworzy embeddingi dla wszystkich atraktorów w mapie"""
        attractors = self.resonance_map['resonance_map']['attractors']
        texts = [f"{a['name']}. {a['description']}" for a in attractors]
        embeddings = self.model.encode(texts)
        
        return {attractors[i]['id']: embeddings[i] for i in range(len(attractors))}
    
    def analyze_text(self, text):
        """Analizuje tekst pod kątem dysonansu z atraktora w mapie"""
        text_embedding = self.model.encode([text])
        attractor_embeddings = self.get_attractor_embeddings()
        
        results = []
        for attractor_id, attr_embedding in attractor_embeddings.items():
            # Oblicz podobieństwo do atraktora
            similarity = cosine_similarity(text_embedding, [attr_embedding])[0][0]
            
            # Pobierz metryki atraktora
            attractor = next(a for a in self.resonance_map['resonance_map']['attractors'] 
                           if a['id'] == attractor_id)
            
            # Oblicz wynik dysonansu (odwrotność podobieństwa dla dark attractors)
            if attractor['type'] == 'dark':
                dissonance_score = 1 - similarity
            else:
                dissonance_score = similarity
                
            results.append({
                'attractor_id': attractor_id,
                'attractor_name': attractor['name'],
                'attractor_type': attractor['type'],
                'similarity_score': float(similarity),
                'dissonance_score': float(dissonance_score),
                'resonance_strength': attractor['energy_metrics']['resonance_strength']
            })
        
        # Sortuj wyniki
        results.sort(key=lambda x: x['dissonance_score'], reverse=True)
        return results
    
    def get_overall_dissonance(self, text):
        """Zwraca ogólny wynik dysonansu tekstu"""
        analysis = self.analyze_text(text)
        
        # Ważony wynik dysonansu (większa waga dla dark attractors)
        total_dissonance = 0
        total_weight = 0
        
        for result in analysis:
            weight = result['resonance_strength']
            if result['attractor_type'] == 'dark':
                weight *= 2  # Większa waga dla dark attractors
                
            total_dissonance += result['dissonance_score'] * weight
            total_weight += weight
            
        return total_dissonance / total_weight if total_weight > 0 else 0

# Przykład użycia
if __name__ == "__main__":
    detector = BasicDissonanceDetector('resonance_maps/first_prototype.json')
    
    test_text = "System korytowy jest najlepszym rozwiązaniem dla społeczeństwa."
    results = detector.analyze_text(test_text)
    overall_dissonance = detector.get_overall_dissonance(test_text)
    
    print(f"Tekst: '{test_text}'")
    print(f"Ogólny dysonans: {overall_dissonance:.3f}")
    print("\nSzczegółowa analiza:")
    for result in results[:3]:  # Top 3 wyniki
        print(f"  {result['attractor_name']} ({result['attractor_type']}): "
              f"dysonans={result['dissonance_score']:.3f}")
