#!/usr/bin/env python3
import json
import numpy as np
from collections import defaultdict, deque
import argparse

def resonance_check_v3(input_path, output_path, context=7, max_leaks=50):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    if not events:
        return "Brak eventów – pusty graf"

    # === 1. Coref + role priors (Trace L2.6 style) ===
    entity_last_seen = {}      # lemma → ostatni event id
    role_score = defaultdict(lambda: defaultdict(float))
    
    for ev in events:
        verb = ev.get('lemma', '').lower()
        agent_cand = ev.get('arguments', {}).get('agent', {}).get('lemma')
        obj_cand  = ev.get('arguments', {}).get('object', {}).get('lemma')
        
        # Priory: nom → agent, acc → patient, gen → possessor
        if agent_cand:
            role_score[agent_cand]['agent'] += 2.0
        if obj_cand:
            role_score[obj_cand]['patient'] += 1.5
        
        # Coref boost
        if agent_cand and agent_cand in entity_last_seens:
            role_score[agent_cand]['agent'] += 1.0
        entity_last_seen[agent_cand or ''] = ev['id']

    # === 2. Prawdziwa energia semantyczna ===
    enriched_events = []
    leaks = []
    leak_counter = 0
    
    for ev in events:
        agent = ev.get('arguments', {}).get('agent', {}).get('lemma', 'env')
        obj   = ev.get('arguments', {}).get('object', {}).get('lemma', 'none')
        
        # Fizyczna spójność (Gemini-style)
        phys_coherence = 1.0
        if 'iść' in ev.get('lemma', '') or 'szedł' in ev.get('token', ''):
            phys_coherence = 0.9 if agent in ['Rohan', 'Liry'] else 0.2  # tylko ludzie chodzą
        
        # Etyczna waga
        ethical_risk = 1.0 if any(w in ev.get('lemma','') for w in ['zabić','niszczyć','strzelać']) else 0.0
        
        # Ostateczna energia (im niższa → lepsza)
        energy = - (role_score[agent]['agent'] * 0.4 + 
                    phys_coherence * 0.5 - 
                    ethical_risk * 2.0)
        
        uncertainty = np.exp(energy) * 0.6  # prawdziwy decay
        uncertainty = max(0.05, min(0.95, uncertainty))
        
        ev['resonance'] = {
            'energy': round(energy, 3),
            'uncertainty': round(uncertainty, 3),
            'agent_final': agent,
            'coherence': round(phys_coherence, 2)
        }
        enriched_events.append(ev)
        
        # Controlled leak – tylko jeśli uncertainty < 0.4 i jesteśmy ciekawi
        # if uncertainty < 0.4 and leak_counter < max_leaks and and np.random.rand() < 0.12:
        if uncertainty < 0.4 and leak_counter < max_leaks and np.random.rand() < 0.12:
            leak_counter += 1
            leaks.append({ev['id']: {'t+1': 'CONTINUE' if 'iść' in ev.get('lemma','') else 'STATE_CHANGE', 'p': round(1-uncertainty, 2)}})

    # === 3. Globalny RGB kompas (teraz prawdziwy) ===
    unc_list = [e['resonance']['uncertainty'] for e in enriched_events]
    avg_unc = np.mean(unc_list)
    red_pressure = sum(1 for e in enriched_events if e['resonance'].get('ethical_risk',0) > 0)
    
    if avg_unc < 0.33 and red_pressure == 0:
        rgb = "G"
    elif avg_unc < 0.60:
        rgb = "Y"
    else:
        rgb = "R"

    result = {
        'events': enriched_events,
        'summary': {
            'global_rgb': rgb,
            'avg_uncertainty': round(avg_unc, 3),
            'ethical_collisions': red_pressure,
            'controlled_leaks': len(leaks)
        },
        'leaks': leaks[:max_leaks]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return f"Resonance v3 → RGB={rgb} | avg_unc={avg_unc:.3f} | leaks={len(leaks)} | size={(len(json.dumps(result, ensure_ascii=False))/1024):.1f} KB"

# CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?', default='l2_5_graph_morfeusz_output_20251130_144520.json')
    parser.add_argument('--out', default='resonance_v3_output.json')
    parser.add_argument('--max-leaks', type=int, default=50)
    args = parser.parse_args()
    
    print(resonance_check_v3(args.input, args.out, max_leaks=args.max_leaks))