# W kodzie immunologicznego frameworku
def personal_evil_containment(threat, defender):
    """
    Zasada osobistego odprowadzenia zła do piekła:
    - Gotowość do destrukcji obu stron konfliktu
    - Naturalny hamulec eskalacji
    - Zapobiega infinite loops przemocy
    """
    containment_cost = defender.calculate_sacrifice_cost(threat)
    
    if containment_cost > defender.existence_threshold:
        # Przekroczenie progu - interwencja niszczy obie strony
        return MutualAnnihilationProtocol(defender, threat)
    else:
        return StandardContainment(defender, threat)
        
def enforce_reality_boundary(threat, enforcer):
    """
    Wymuszenie musi być:
    - Osobiste (personal accountability)
    - Proporcjonalne (minimalna konieczna siła)
    - Przejrzyste (każdy widzi przyczynę i skutek)
    - Tymczasowe (do momentu neutralizacji zagrożenia)
    """
    if threat.resonance_score < 0.3 and threat.potential_energy > 0.7:
        return enforcer.apply_minimal_force(threat)
    else:
        return None  # Nie wymuszaj bez konieczności
