# W kodzie immunologicznego frameworku
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
