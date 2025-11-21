def calculate_attractor_metrics(concept_data, reference_library):
    """
    Oblicza metryki stabilności dla konceptu na podstawie kotwic w reference_library
    """
    metrics = {}
    
    # 1. Obliczanie kosztu utrzymania
    # Im więcej wyjątków i specjalnych reguł, tym wyższy koszt
    maintenance_cost = len(concept_data['exceptions']) / len(concept_data['core_rules'])
    
    # 2. Siła rezonansu - korelacja z innymi zdrowymi konceptami
    resonance_strength = calculate_correlation(concept_data, reference_library.healthy_concepts)
    
    # 3. Gęstość sprzeczności
    contradiction_density = detect_internal_contradictions(concept_data['logic_graph'])
    
    return {
        'maintenance_cost': maintenance_cost,
        'resonance_strength': resonance_strength,
        'contradiction_density': contradiction_density
    }
