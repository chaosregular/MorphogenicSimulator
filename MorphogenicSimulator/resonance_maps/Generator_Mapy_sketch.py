def generate_resonance_map(concept_list, reference_data):
    """
    Generuje kompletną mapę rezonansową z listy konceptów
    """
    resonance_map = {
        'version': '0.1',
        'timestamp': get_current_timestamp(),
        'attractors': []
    }
    
    for concept in concept_list:
        # Oblicz metryki dla każdego konceptu
        metrics = calculate_attractor_metrics(concept, reference_data)
        
        # Określ typ atraktora (light/dark) na podstawie metryk
        attractor_type = classify_attractor_type(metrics)
        
        attractor_data = {
            'id': f"attractor_{attractor_type}_{concept['name']}",
            'name': concept['name'],
            'type': attractor_type,
            'energy_metrics': metrics,
            'semantic_coordinates': calculate_semantic_position(concept),
            'stability_vector': calculate_stability_vector(metrics)
        }
        
        resonance_map['attractors'].append(attractor_data)
    
    return resonance_map
