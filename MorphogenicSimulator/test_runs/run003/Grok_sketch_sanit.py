import json
import sys
import numpy as np
from collections import defaultdict

def grok_sanity_check(l2_5_graph_path, output_path):
    with open(l2_5_graph_path, 'r') as f:
        graph = json.load(f)
    
    enriched = defaultdict(list)
    for event in graph.get('events', []):
        # Heurystyka: 3 hipotezy agent-object swaps
        hypotheses = [
            {'agent': event.get('arguments', {}).get('agent'), 'object': event.get('arguments', {}).get('object'), 'energy': 0.0},
            {'agent': event.get('arguments', {}).get('object'), 'object': event.get('arguments', {}).get('agent'), 'energy': 0.0},  # Swap 1
            # Swap 2: neutral (np. environment as agent)
            {'agent': 'env', 'object': event.get('arguments', {}).get('agent'), 'energy': 0.0}
        ]
        
        # Semantic energy: niska entropia = niska energia (koherencja)
        for hyp in hypotheses:
            # Prosty score: match Morfeusz tags (np. subst dla agent)
            tag_match = 1.0 if 'subst' in str(hyp['agent']) else 0.5  # Placeholder
            entropy = np.log(len(str(hyp)))  # Mock entropia
            hyp['energy'] = tag_match - 0.1 * entropy  # Min energy = best
        
        # Wybierz top-1, dodaj uncertainty
        best_hyp = min(hypotheses, key=lambda h: h['energy'])
        event['sanity_hyp'] = best_hyp
        event['uncertainty'] = np.exp(-best_hyp['energy'])  # Decay-like
        enriched[event['id']].append(event)
    
    # RGB kompas: avg uncertainty → color
    avg_unc = np.mean([e['uncertainty'] for events in enriched.values() for e in events])
    rgb_state = 'G' if avg_unc < 0.3 else 'Y' if avg_unc < 0.7 else 'R'
    enriched['global_rgb'] = rgb_state
    
    with open(output_path, 'w') as f:
        json.dump(dict(enriched), f, indent=2)
    
    return f"Sanity done: RGB={rgb_state}, avg_unc={avg_unc:.2f}"

# Test: grok_sanity_check('l2_5_graph.json', 'enriched_l2_5.json')
# l2_5_graph_morfeusz_output_20251130_144520.json grenr_l2_5_graph_morfeusz_output_20251130_144520.json

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 grok_sanity_check.py l2_5_graph.json out_enriched_l2_5.json")
        sys.exit(1)
    # fin = sys.argv[1]; fout = sys.argv[2]
    # with open(fin, 'r', encoding='utf8') as f:
    #     data = json.load(f)
    # with open(fout, 'w', encoding='utf8') as f:
    #     json.dump(graph, f, ensure_ascii=False, indent=2)
    # print("Saved:", fout)
    grok_sanity_check(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()