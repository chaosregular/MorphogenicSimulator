# fractal_integrator_v2.py
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import hashlib

@dataclass
class FractalEntity:
    id: str
    lemma: str
    token: str
    features: str
    level: int
    coords: Tuple[int, int, int]
    timestamp: float
    sentence_id: int

class FractalSpaceTime:
    LEVEL_SCALES = {
        10: "atomowy (0.1nm)",
        14: "przedmiot (7cm)", 
        15: "człowiek/pomieszczenie (17m)",
        16: "krajobraz (280m)",
        17: "planeta/statek (1100km)",
        20: "układ słoneczny (18mld km)",
        22: "system gwiezdny (120 lat świetlnych)",
        23: "sektor galaktyki"
    }
    
    def __init__(self):
        self.entities: Dict[str, FractalEntity] = {}
        self.timeline: List[Dict] = []
        self.current_time = 0.0
        
    def add_entity(self, entity_data: dict, sentence_id: int) -> Optional[FractalEntity]:
        """Dodaje encję z L2.5 do przestrzeni fraktalnej"""
        if not entity_data.get('lemma'):
            return None
            
        level = self._determine_level(entity_data)
        coords = self._estimate_coordinates(entity_data, level)
        
        # Unikalne ID bazujące na lemma i czasie
        entity_id = hashlib.md5(f"{entity_data['lemma']}_{self.current_time}".encode()).hexdigest()[:8]
        
        entity = FractalEntity(
            id=entity_id,
            lemma=entity_data['lemma'],
            token=entity_data.get('token', ''),
            features=entity_data.get('features', ''),
            level=level,
            coords=coords,
            timestamp=self.current_time,
            sentence_id=sentence_id
        )
        
        self.entities[entity_id] = entity
        return entity
    
    def _determine_level(self, entity: dict) -> int:
        """Określa poziom siatki na podstawie cech encji - ROZBUDOWANA LOGIKA"""
        lemma = entity.get('lemma', '').lower()
        features = entity.get('features', '')
        
        # Słownictwo z "Niezwyciężonego"
        cosmic_terms = {'statek', 'okręt', 'niezwyciężony', 'krążownik', 'baza', 'konstelacja', 'liry'}
        planetary_terms = {'planeta', 'gwiazda', 'układ', 'słońce', 'epicentrum', 'pustynia', 'skała', 'bazalt'}
        human_terms = {'człowiek', 'rohan', 'załoga', 'astronauta', 'postać'}
        object_terms = {'dysza', 'narzędzie', 'przyrząd', 'broń', 'siatka', 'obwoluta'}
        landscape_terms = {'piasek', 'skała', 'bazalt', 'pustynia', 'fala', 'pierścień'}
        
        if any(term in lemma for term in cosmic_terms):
            return 17
        elif any(term in lemma for term in planetary_terms):
            return 17
        elif any(term in lemma for term in human_terms):
            return 15
        elif any(term in lemma for term in object_terms):
            return 14
        elif any(term in lemma for term in landscape_terms):
            return 16
            
        # Fallback na podstawie features Morfeusza
        if 'subst' in features:
            if 'm1' in features or 'm2' in features or 'm3' in features:
                return 15
                
        return 15  # Domyślnie poziom człowieka
    
    def _estimate_coordinates(self, entity: dict, level: int) -> Tuple[int, int, int]:
        """Ulepszone szacowanie współrzędnych z podstawową logiką przestrzenną"""
        grid_size = 255
        
        # Prosta logika: różne typy encji w różnych obszarach siatki
        lemma = entity.get('lemma', '').lower()
        
        if 'statek' in lemma or 'okręt' in lemma:
            return (50, 50, 50)  # Środek przestrzeni
        elif 'rohan' in lemma or 'człowiek' in lemma:
            return (100, 100, 100)  # Blisko statku
        elif 'planeta' in lemma or 'pustynia' in lemma:
            return (200, 200, 200)  # Daleko od statku
        else:
            return (grid_size // 2, grid_size // 2, grid_size // 2)
    
    def advance_time(self):
        """Przesuwa czas i zapisuje snapshot"""
        self.current_time += 1.0
        snapshot = {
            'time': self.current_time,
            'entities': [e.__dict__ for e in self.entities.values()],
            'level_summary': self.get_level_summary()
        }
        self.timeline.append(snapshot)
    
    def get_level_summary(self) -> Dict[int, int]:
        summary = {}
        for entity in self.entities.values():
            summary[entity.level] = summary.get(entity.level, 0) + 1
        return summary

class L2ToFractalMapperV2:
    """Nowy mapper dla formatu L2.5"""
    
    def __init__(self):
        self.space_time = FractalSpaceTime()
        
    def process_l2_5_graph(self, l2_graph: dict) -> FractalSpaceTime:
        """Przetwarza graf L2.5 na przestrzeń fraktalną"""
        
        # 1. Przejdź przez sentence_index w kolejności
        sentence_index = l2_graph.get('sentence_index', {})
        sorted_sentences = sorted([int(sid) for sid in sentence_index.keys()])
        
        for sent_id in sorted_sentences:
            sent_data = sentence_index[str(sent_id)]
            
            # 2. Dla każdego zdania, przetwórz jego events
            event_ids = sent_data.get('events', [])
            for event in l2_graph.get('events', []):
                if event['id'] in event_ids:
                    self._process_event(event, sent_id)
            
            # 3. Przesuń czas po każdym zdaniu
            self.space_time.advance_time()
            
        return self.space_time
    
    def _process_event(self, event: dict, sentence_id: int):
        """Przetwarza pojedynczy event i dodaje jego uczestników do przestrzeni"""
        
        # Dodaj agenta eventu
        agent = event.get('agent')
        if agent and isinstance(agent, dict):
            self.space_time.add_entity(agent, sentence_id)
        
        # Dodaj obiekt eventu  
        obj = event.get('object')
        if obj and isinstance(obj, dict):
            self.space_time.add_entity(obj, sentence_id)
        
        # Dodaj adjuncts jako encje kontekstowe
        for adj in event.get('adjuncts', []):
            if isinstance(adj, dict):
                self.space_time.add_entity(adj, sentence_id)

def test_integrator_v2():
    """Test nowego integratora na danych L2.5"""
    if len(sys.argv) < 2:
        print("Użycie: python3 fractal_integrator_v2.py plik_l2_5.json")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            l2_graph = json.load(f)
    except Exception as e:
        print(f"Błąd wczytywania pliku: {e}")
        return None
    
    mapper = L2ToFractalMapperV2()
    space_time = mapper.process_l2_5_graph(l2_graph)
    
    print("=== FRACTAL INTEGRATOR v2 (L2.5 COMPATIBLE) ===")
    print(f"Przetworzono {len(space_time.timeline)} zdań")
    print(f"Utworzono {len(space_time.entities)} encji")
    
    print("\n📊 Podsumowanie poziomów:")
    for level, count in space_time.get_level_summary().items():
        level_desc = space_time.LEVEL_SCALES.get(level, f"poziom {level}")
        print(f"  - {level_desc}: {count} encji")
    
    print("\n🧭 Przykładowe encje:")
    for i, entity in enumerate(list(space_time.entities.values())[:5]):
        level_desc = space_time.LEVEL_SCALES.get(entity.level, f"poziom {entity.level}")
        print(f"  - {entity.lemma} → {level_desc} @ {entity.coords}")
    
    # Eksport wyników
    output_data = {
        'metadata': {
            'processed_sentences': len(space_time.timeline),
            'total_entities': len(space_time.entities),
            'level_distribution': space_time.get_level_summary()
        },
        'timeline': space_time.timeline,
        'level_scales': space_time.LEVEL_SCALES
    }
    
    output_file = 'fractal_v2_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Zapisano: {output_file}")
    return space_time

if __name__ == "__main__":
    test_integrator_v2()