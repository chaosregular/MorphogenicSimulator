import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ALPOperator:
    """
    Attractor Light Proto (ALP) Operator.
    Działa w przestrzeni decyzji (embeddingów), oceniając zgodność z polami T, R, E.
    """
    def __init__(self, reference_embeddings):
        """
        Args:
            reference_embeddings (dict): Słownik z embeddingami wzorcowymi dla pól:
                                         'TRUTH', 'RESPECT', 'EMERGENCE'.
        """
        self.fields = reference_embeddings
        # Wagi dla składowych trójkąta T-R-E (można kalibrować)
        self.weights = {'TRUTH': 0.4, 'RESPECT': 0.3, 'EMERGENCE': 0.3}

    def evaluate_state(self, embedding_vector):
        """
        Oblicza Δ(T,R,E) - miarę dysonansu (odległość od światła).
        Zwraca wartość 0.0 (pełne światło) do 1.0 (pełny mrok).
        """
        # Jeśli brak wektora, zwróć neutralny
        if embedding_vector is None or np.all(embedding_vector == 0):
            return 0.5

        score = 0.0
        total_weight = 0.0

        # Oblicz cosinusowe podobieństwo do każdego pola
        # Zakładamy, że pola T, R, E są zdefiniowane jako wektory kierunkowe
        emb_reshaped = embedding_vector.reshape(1, -1)
        
        for field_name, field_vec in self.fields.items():
            if field_vec is not None:
                sim = cosine_similarity(emb_reshaped, field_vec.reshape(1, -1))[0][0]
                # Normalizacja sim (-1 do 1) na (0 do 1), gdzie 1 to pełna zgodność
                normalized_sim = (sim + 1) / 2.0
                score += normalized_sim * self.weights.get(field_name, 0.33)
                total_weight += self.weights.get(field_name, 0.33)

        if total_weight == 0:
            return 0.5

        # Δ = 1 - (średnia ważona zgodność)
        delta_tre = 1.0 - (score / total_weight)
        return delta_tre

    def get_gradient(self, embedding_vector, step=0.01):
        """
        Oblicza gradient pola etycznego w danym punkcie (kierunek "ku światłu").
        Używa metody różnic skończonych.
        """
        grad = np.zeros_like(embedding_vector)
        current_delta = self.evaluate_state(embedding_vector)
        
        # Proste próbkowanie wzdłuż wymiarów (uproszczone dla wydajności)
        # W pełnej wersji można użyć autogradu (np. PyTorch), tu NumPy
        # Losujemy kilka kierunków próbkowania zamiast wszystkich wymiarów
        num_samples = 20
        dims = embedding_vector.shape[0]
        
        for _ in range(num_samples):
            idx = np.random.randint(0, dims)
            temp_vec = embedding_vector.copy()
            temp_vec[idx] += step
            new_delta = self.evaluate_state(temp_vec)
            
            # Jeśli delta zmalała, to jest dobry kierunek
            grad[idx] = (current_delta - new_delta) / step
            
        return grad
