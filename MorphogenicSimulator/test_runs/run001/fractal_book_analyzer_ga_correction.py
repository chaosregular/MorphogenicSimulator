import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer  # Pamiętaj: ten jest słaby dla polskiego!
from collections import defaultdict
import random
import json

# Nadal pobieramy punkt, bo polski model punkt go potrzebuje
nltk.download('punkt', quiet=True) 
# Te poniższe są nadal głównie angielskie, ale zostawiamy dla spójności klasy
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

class FractalBookAnalyzer:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
    
    def normalize_word(self, word):
        # Ta funkcja jest największym problemem dla języka polskiego.
        # NLTK WordNetLemmatizer wymaga podania części mowy (verb/noun/etc),
        # a i tak działa tylko dla angielskiego WordNetu.
        # Dla polskiego słowa "książki" nie zwróci "książka".
        return self.lemmatizer.lemmatize(word.lower())
    
    def parse_to_fractal_structure(self, text, num_levels=5):
        # TUTAJ JEST ZMIANA: Używamy 'polish' language parameter
        sentences = sent_tokenize(text, language='polish') 
        levels = []
        word_occurrences = defaultdict(list)
        global_pos = 0
        
        for lvl in range(num_levels):
            if lvl == 0:  # Level 0: Standardowe zdania
                level = []
                for sent in sentences:
                    # Tokenizacja słów jest mniej zależna od języka niż tokenizacja zdań
                    words = word_tokenize(sent)
                    normalized = [self.normalize_word(w) for w in words if w.isalpha()]
                    level.append(normalized)
            elif lvl == 1:  # Level 1: Losowe grupy zdań
                shuffled_sents = sentences[:]
                random.shuffle(shuffled_sents)
                level = []
                i = 0
                while i < len(shuffled_sents):
                    chunk_size = random.randint(3, 5)
                    group = shuffled_sents[i:i + chunk_size]
                    group_text = ' '.join(group)
                    words = word_tokenize(group_text)
                    normalized = [self.normalize_word(w) for w in words if w.isalpha()]
                    level.append(normalized)
                    i += chunk_size
            else:  # Level 2: Symulowane paragrafy
                level = []
                for i in range(0, len(sentences), 5):
                    para = ' '.join(sentences[i:i + 5])
                    words = word_tokenize(para)
                    normalized = [self.normalize_word(w) for w in words if w.isalpha()]
                    level.append(normalized)
            
            levels.append(level)
            
            # Buduj # dla słów (reszta bez zmian)
            for seg_idx, segment in enumerate(level):
                for word_idx, word in enumerate(segment):
                    global_pos += 1
                    word_occurrences[word].append({
                        'global_pos': global_pos,
                        'level': lvl,
                        'segment_idx': seg_idx,
                        'word_idx': word_idx,
                        'context_blob': segment
                    })
        
        return {
            'fractal_levels': levels,
            'word_occurrences': dict(word_occurrences)
        }
    
    # ... (metoda extract_themes bez zmian, działa na słownikach Pythona) ...
    def extract_themes(self, fractal_data, max_words=100):
        # ... (implementacja extract_themes) ...
        word_freq = {w: len(occ) for w, occ in fractal_data['word_occurrences'].items()}
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_words]
        
        themes = {}
        for word, freq in top_words:
            occurrences = fractal_data['word_occurrences'][word]
            positions = [occ['global_pos'] for occ in occurrences]
            
            triads = []
            for occ in occurrences:
                context = occ['context_blob']
                idx = occ['word_idx']
                if 0 < idx < len(context) - 1:
                    triad = {
                        'cause': context[idx-1],
                        'core': word,
                        'effect': context[idx+1],
                        'reality_anchor': f"Pozycja #{occ['global_pos']} na levelu {occ['level']}"
                    }
                    triads.append(triad)
            
            themes[word] = {
                'frequency': freq,
                'position_space': positions,
                'sample_triads': triads[:3]
            }
        
        return themes


# Przykład użycia
if __name__ == "__main__":
    analyzer = FractalBookAnalyzer()
    
    # Używamy polskiego tekstu testowego
    test_text = """
    Był to jasny, zimny dzień w kwietniu, a zegary biły trzynastą. Winston Smith, wciskając podbródek w pierś, by uchronić się przed wiatrem, przemknął przez szklane drzwi Bloku Zwycięstwa, choć nie dość szybko, by zapobiec wessaniu się wraz z nim kłębu żrącego pyłu.
    Korytarz cuchnął gotowaną kapustą i starymi wycieraczkami. Na jednym końcu wisiał zbyt duży plakat, przypięty do ściany. Przedstawiał tylko ogromną twarz, ponad metrowej szerokości: twarz mężczyzny około czterdziestu pięciu lat, z ciężkim czarnym wąsem i surowymi, czujnymi oczami. Podpis głosił: WIELKI BRAT PATRZY.
    """
    
    # Jeśli chcesz analizować plik z Lema, musisz wczytać jego zawartość:
    try:
        with open('Stanisław_Lem_Niezwyciezony_utf8.txt', 'r', encoding='utf-8') as f:
            lem_text = f.read()
    except FileNotFoundError:
        print("Plik Lema nie znaleziony, używam tekstu zastępczego.")
        lem_text = test_text # fallback
    
    fractal_data = analyzer.parse_to_fractal_structure(lem_text)
    
    # fractal_data = analyzer.parse_to_fractal_structure(test_text)
    themes = analyzer.extract_themes(fractal_data)
    
    print("Fraktalna struktura - podsumowanie leveli:")
    for i, lvl in enumerate(fractal_data['fractal_levels']):
        print(f"Level {i}: {len(lvl)} segmentów, średnia długość: {sum(len(seg) for seg in lvl)/len(lvl):.1f} słów")
    
    print("\nPrzykładowe word_occurrences (top 3 słowa):")
    sample_words = list(fractal_data['word_occurrences'].keys())[:3]
    for w in sample_words:
        print(f"{w}: {len(fractal_data['word_occurrences'][w])} wystąpień, sample #: {[occ['global_pos'] for occ in fractal_data['word_occurrences'][w][:2]]}")
    
    print("\nEmergentne themes (wątki z triadami):")
    print(json.dumps(themes, indent=2)) # Poprawiona zmienna 'themes'
