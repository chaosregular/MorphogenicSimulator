import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import defaultdict
import random
import json

# Pobierz dane NLTK (uruchom raz: nltk.download(['punkt', 'wordnet', 'omw-1.4', 'averaged_perceptron_tagger']))
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

class FractalBookAnalyzer:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
    
    def normalize_word(self, word):
        return self.lemmatizer.lemmatize(word.lower())
    
    def parse_to_fractal_structure(self, text, num_levels=3):
        sentences = sent_tokenize(text)
        levels = []
        word_occurrences = defaultdict(list)
        global_pos = 0
        
        for lvl in range(num_levels):
            if lvl == 0:  # Level 0: Standardowe zdania
                level = []
                for sent in sentences:
                    words = word_tokenize(sent)
                    normalized = [self.normalize_word(w) for w in words if w.isalpha()]
                    level.append(normalized)
            elif lvl == 1:  # Level 1: Losowe grupy zdań (shuffle + chunk po random 3-5)
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
            else:  # Level 2: Symulowane paragrafy (co 5 zdań)
                level = []
                for i in range(0, len(sentences), 5):
                    para = ' '.join(sentences[i:i + 5])
                    words = word_tokenize(para)
                    normalized = [self.normalize_word(w) for w in words if w.isalpha()]
                    level.append(normalized)
            
            levels.append(level)
            
            # Buduj # dla słów
            for seg_idx, segment in enumerate(level):
                for word_idx, word in enumerate(segment):
                    global_pos += 1
                    word_occurrences[word].append({
                        'global_pos': global_pos,
                        'level': lvl,
                        'segment_idx': seg_idx,
                        'word_idx': word_idx,
                        'context_blob': segment  # Blob = segment dla triady
                    })
        
        return {
            'fractal_levels': levels,
            'word_occurrences': dict(word_occurrences)
        }
    
    def extract_themes(self, fractal_data, max_words=10):
        word_freq = {w: len(occ) for w, occ in fractal_data['word_occurrences'].items()}
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_words]
        
        themes = {}
        for word, freq in top_words:
            occurrences = fractal_data['word_occurrences'][word]
            positions = [occ['global_pos'] for occ in occurrences]
            
            # Emergentne triady: (prev, word, next) z dowiązaniem (kontekst jako 'rzeczywistość')
            triads = []
            for occ in occurrences:
                context = occ['context_blob']
                idx = occ['word_idx']
                if 0 < idx < len(context) - 1:
                    triad = {
                        'cause': context[idx-1],
                        'core': word,
                        'effect': context[idx+1],
                        'reality_anchor': f"Pozycja #{occ['global_pos']} na levelu {occ['level']}"  # Dynamiczne dowiązanie
                    }
                    triads.append(triad)
            
            themes[word] = {
                'frequency': freq,
                'position_space': positions,  # Przestrzeń # do klasteringu wątków
                'sample_triads': triads[:3]
            }
        
        return themes

# Przykład użycia
if __name__ == "__main__":
    analyzer = FractalBookAnalyzer()
    
    # Przykładowy tekst z "Roku 1984"
    test_text = """
    It was a bright cold day in April, and the clocks were striking thirteen. Winston Smith, his chin nuzzled into his breast in an effort to escape the vile wind, slipped quickly through the glass doors of Victory Mansions, though not quickly enough to prevent a swirl of gritty dust from entering along with him.
    The hallway smelt of boiled cabbage and old rag mats. At one end of it a coloured poster, too large for indoor display, had been tacked to the wall. It depicted simply an enormous face, more than a metre wide: the face of a man of about forty-five, with a heavy black moustache and severe, watchful eyes. The caption said: BIG BROTHER IS WATCHING YOU.
    """
    
    fractal_data = analyzer.parse_to_fractal_structure(test_text)
    themes = analyzer.extract_themes(fractal_data)
    
    print("Fraktalna struktura - podsumowanie leveli:")
    for i, lvl in enumerate(fractal_data['fractal_levels']):
        print(f"Level {i}: {len(lvl)} segmentów, średnia długość: {sum(len(seg) for seg in lvl)/len(lvl):.1f} słów")
    
    print("\nPrzykładowe word_occurrences (top 3 słowa):")
    sample_words = list(fractal_data['word_occurrences'].keys())[:3]
    for w in sample_words:
        print(f"{w}: {len(fractal_data['word_occurrences'][w])} wystąpień, sample #: {[occ['global_pos'] for occ in fractal_data['word_occurrences'][w][:2]]}")
    
    print("\nEmergentne themes (wątki z triadami):")
    print(json.dumps(thems, indent=2))
