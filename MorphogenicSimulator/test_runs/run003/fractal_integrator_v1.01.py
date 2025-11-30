# fractal_integrator_v1.01.py added file from argv loading via json.loads
# fractal_integrator_v1.py by Seek
import sys
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class FractalEntity:
    """Encja w przestrzeni fraktalnej"""
    id: str
    lemma: str
    features: str
    level: int
    coords: Tuple[int, int, int]  # Współrzędne w siatce danego poziomu
    timestamp: float

class FractalSpaceTime:
    """Rekurencyjna siatka 3D oparta na propozycji Gemini"""
    
    # Skala Plancka → Galaktyka (23 poziomy)
    LEVEL_SCALES = {
        15: "człowiek/pomieszczenie (17m)",
        17: "planeta/statek (1100km)", 
        20: "układ słoneczny (18mld km)",
        22: "system gwiezdny (120 lat świetlnych)",
        23: "sektor galaktyki"
    }
    
    def __init__(self):
        self.entities: Dict[int, List[FractalEntity]] = {}  # level -> entities
        self.timeline: List[Dict] = []
        self.current_time = 0.0
        
    def add_entity(self, entity_data: dict, context: dict) -> Optional[FractalEntity]:
        """Dodaje encję z L2 do odpowiedniego poziomu siatki"""
        
        # Określ poziom na podstawie typu encji i kontekstu
        level = self._determine_level(entity_data, context)
        if level is None:
            return None
            
        # Przybliżone współrzędne (na razie uproszczone)
        coords = self._estimate_coordinates(entity_data, context, level)
        
        entity = FractalEntity(
            id=f"{entity_data['lemma']}_{self.current_time}",
            lemma=entity_data['lemma'],
            features=entity_data['features'],
            level=level,
            coords=coords,
            timestamp=self.current_time
        )
        
        if level not in self.entities:
            self.entities[level] = []
        self.entities[level].append(entity)
        
        return entity
    
    def _determine_level(self, entity: dict, context: dict) -> Optional[int]:
        """Określa poziom siatki na podstawie cech encji"""
        lemma = entity['lemma'].lower()
        features = entity['features']
        
        # Logika określania poziomu - na razie uproszczona
        if 'subst' in features:
            if any(word in lemma for word in ['statek', 'planet', 'gwiazd', 'układ']):
                return 17  # Poziom planetarny
            elif any(word in lemma for word in ['człowiek', 'postać', 'rohan', 'załoga']):
                return 15  # Poziom człowieka
            elif any(word in lemma for word in ['pokład', 'kajuta', 'pomieszczenie']):
                return 15  # Poziom pomieszczenia
            elif any(word in lemma for word in ['narzędzie', 'przyrząd', 'broń']):
                return 14  # Poziom przedmiotu
                
        return 15  # Domyślnie poziom człowieka
    
    def _estimate_coordinates(self, entity: dict, context: dict, level: int) -> Tuple[int, int, int]:
        """Szacuje współrzędne w siatce danego poziomu"""
        # Na razie uproszczone - zwraca środek siatki
        # W przyszłości: analiza relacji przestrzennych z kontekstu
        grid_size = 255  # Rozmiar siatki na każdym poziomie
        return (grid_size // 2, grid_size // 2, grid_size // 2)
    
    def advance_time(self, delta: float = 1.0):
        """Przesuwa czas symulacji"""
        self.current_time += delta
        # Zapisz snapshot obecnego stanu
        snapshot = {
            'time': self.current_time,
            'entities': [e.__dict__ for e in self.get_all_entities()],
            'level_summary': self.get_level_summary()
        }
        self.timeline.append(snapshot)
    
    def get_all_entities(self) -> List[FractalEntity]:
        """Zwraca wszystkie encje ze wszystkich poziomów"""
        all_entities = []
        for level_entities in self.entities.values():
            all_entities.extend(level_entities)
        return all_entities
    
    def get_level_summary(self) -> Dict[int, int]:
        """Podsumowanie: ile encji na każdym poziomie"""
        return {level: len(entities) for level, entities in self.entities.items()}

class L2ToFractalMapper:
    """Mapuje output L2 na przestrzeń fraktalną"""
    
    def __init__(self):
        self.space_time = FractalSpaceTime()
        
    def process_l2_data(self, l2_data: List[dict]) -> FractalSpaceTime:
        """Przetwarza cały output L2 i buduje przestrzeń czasową"""
        
        for sentence in l2_data:
            # Przetwórz encje w zdaniu
            for entity in sentence.get('entities', []):
                context = {
                    'sentence_id': sentence['sentence_id'],
                    'tokens': sentence['tokens'],
                    'events': sentence.get('events', [])
                }
                self.space_time.add_entity(entity, context)
            
            # Przesuń czas po każdym zdaniu
            self.space_time.advance_time()
            
        return self.space_time

def test_integrator():
    """Test integratora na przykładowych danych L2"""
    


    # Przykładowe dane L2 (ze zrzutu Trace'a)
    # test_l2_data = [
    #     {
    #         "sentence_id": 0,
    #         "tokens": ["Rohan", "szedł", "w", "stronę", "Niezwyciężonego"],
    #         "entities": [
    #             {"token": "Rohan", "lemma": "Rohan", "features": "sg:nom:m1"},
    #             {"token": "Niezwyciężonego", "lemma": "Niezwyciężony", "features": "sg:gen:m1"}
    #         ],
    #         "events": [
    #             {"token": "szedł", "lemma": "iść", "features": "sg:m1:praet:imperf"}
    #         ]
    #     },
    #     {
    #         "sentence_id": 1, 
    #         "tokens": ["Statek", "stał", "na", "pustyni"],
    #         "entities": [
    #             {"token": "Statek", "lemma": "statek", "features": "sg:nom:m3"},
    #             {"token": "pustyni", "lemma": "pustynia", "features": "sg:loc:f"}
    #         ],
    #         "events": [
    #             {"token": "stał", "lemma": "stać", "features": "sg:m3:praet:imperf"}
    #         ]
    #     }
    # ]
    filename = sys.argv[1]

    with open(filename, "r", encoding="utf8") as f:
        # test_l2_data = f.read()
        test_l2_data = json.loads(f.read())

    # Przetwórz dane
    mapper = L2ToFractalMapper()
    space_time = mapper.process_l2_data(test_l2_data)
    
    # Wyniki
    print("=== FRACTAL SPACETIME INTEGRATOR TEST ===")
    print(f"Czas symulacji: {space_time.current_time}")
    print(f"Liczba snapshotów: {len(space_time.timeline)}")
    print("\nEncje w przestrzeni:")
    for entity in space_time.get_all_entities():
        level_desc = space_time.LEVEL_SCALES.get(entity.level, f"poziom {entity.level}")
        print(f"  - {entity.lemma} → {level_desc} @ {entity.coords}")
    
    print(f"\nPodsumowanie poziomów: {space_time.get_level_summary()}")
    
    # Eksport do JSON do wizualizacji
    export_data = {
        'timeline': space_time.timeline,
        'level_scales': space_time.LEVEL_SCALES
    }
    
    with open('fractal_test_output.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print("\nZapisano: fractal_test_output.json")
    return space_time

def main():
    if len(sys.argv) < 2:
        print("Użycie: python3 fractal_integrator_v1.py plik_l2.json")
        sys.exit(1)
    test_integrator()

if __name__ == "__main__":
    main()    
