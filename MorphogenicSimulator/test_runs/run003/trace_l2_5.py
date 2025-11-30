#!/usr/bin/env python3
# trace_l2_5.py
# L2.5 Composition Engine (Trace)
# - input: morfeusz-style JSON array (token entries with sentence_id, token, analyses)
# - output: event graph (JSON) with events, entities, relations, modality, sentence_index
#
# Heurystyki:
# - agent = nearest noun left of verb
# - object = nearest noun/right-adj right of verb
# - adjuncts = adv/prep/adj within +/-3 token window
# - relative pronouns attach clause verbs to antecedent noun (embedding)
# - modality: sentence-level markers (simple list)
#
# Save-file: run as:
# python3 trace_l2_5.py morfeusz_output.json out_graph.json

import json, sys, re
from collections import defaultdict

REL_PRONS = set(['który','którego','która','które','której','którym','których'])
MODAL_MARKERS = {
    'uncertainty': set(['chyba','zdawało się','zdaje się','jakby','może','może być']),
    'certainty': set(['wiedział','na pewno','z pewnością']),
    'necessity': set(['musiał','musiała','musieli','trzeba']),
}

def group_by_sentence(data):
    out = defaultdict(list)
    for i, tok in enumerate(data):
        out[tok['sentence_id']].append({'idx': i, **tok})
    return dict(sorted(out.items()))

def primary_analysis(analyses):
    if not analyses: return None
    for a in analyses:
        if a.get('pos') and a.get('pos') != 'interp':
            return a
    return analyses[0]

def is_verb_pos(pos):
    return pos in ('fin','praet','impt','imps','inf','verb','ger')

def is_noun_pos(pos):
    return pos in ('subst','depr','subst:sg')

def detect_modality_in_sentence(tokens):
    joined = " ".join([t['token'] for t in tokens]).lower()
    found = []
    for cat, markers in MODAL_MARKERS.items():
        for m in markers:
            if m in joined:
                found.append({'category': cat, 'marker': m})
    return found

def choose_agent_left(tokens, verb_index):
    for t in reversed(tokens[:verb_index]):
        a = primary_analysis(t['analyses'])
        if a and is_noun_pos(a.get('pos','')):
            return t
    return None

def choose_object_right(tokens, verb_index):
    for t in tokens[verb_index+1:]:
        a = primary_analysis(t['analyses'])
        if a and (is_noun_pos(a.get('pos','')) or a.get('pos')=='adj'):
            return t
    return None

def compose_l2_5(morfeusz_data):
    sentences = group_by_sentence(morfeusz_data)
    graph = {'events': [], 'entities': {}, 'relations': [], 'sentence_index': {}}
    eid_counter = 0
    # Extract entities (simple per-noun mention)
    for sid, toks in sentences.items():
        for t in toks:
            a = primary_analysis(t['analyses'])
            if a and is_noun_pos(a.get('pos','')):
                label = t['token'].strip(' ,.;:')
                eid = f"ENT{eid_counter}"
                graph['entities'][eid] = {
                    'label': label,
                    'sentence': sid,
                    'token_idx': t['idx'],
                    'lemma': a.get('base'),
                    'features': a.get('features')
                }
                eid_counter += 1
    # Extract events and attach args
    ev_counter = 0
    for sid, toks in sentences.items():
        modality = detect_modality_in_sentence(toks)
        sentence_events = []
        for i, t in enumerate(toks):
            a = primary_analysis(t['analyses'])
            if not a: continue
            if is_verb_pos(a.get('pos','')):
                ev_id = f"EV{ev_counter}"
                ev = {
                    'id': ev_id,
                    'sentence': sid,
                    'token_idx': t['idx'],
                    'token': t['token'],
                    'lemma': a.get('base'),
                    'features': a.get('features'),
                    'agent': None, 'object': None, 'adjuncts': [], 'embedded_in': None, 'modality': modality
                }
                agent_t = choose_agent_left(toks, i)
                if agent_t:
                    ev['agent'] = {'token': agent_t['token'], 'sentence': sid, 'token_idx': agent_t['idx'], 'lemma': primary_analysis(agent_t['analyses']).get('base')}
                obj_t = choose_object_right(toks, i)
                if obj_t:
                    ev['object'] = {'token': obj_t['token'], 'sentence': sid, 'token_idx': obj_t['idx'], 'lemma': primary_analysis(obj_t['analyses']).get('base')}
                # adjuncts within window
                adj = []
                for j in range(max(0,i-3), min(len(toks), i+4)):
                    if j==i: continue
                    pa = primary_analysis(toks[j]['analyses'])
                    if pa and pa.get('pos') in ('adv','prep','adj','conj'):
                        adj.append({'token': toks[j]['token'], 'pos': pa.get('pos'), 'token_idx': toks[j]['idx']})
                ev['adjuncts'] = adj
                graph['events'].append(ev)
                sentence_events.append(ev)
                ev_counter += 1
        # relative pronouns attachments
        for i, t in enumerate(toks):
            a = primary_analysis(t['analyses'])
            if a and a.get('base','').lower() in REL_PRONS:
                antecedent = None
                for j in range(i-1, -1, -1):
                    pa = primary_analysis(toks[j]['analyses'])
                    if pa and is_noun_pos(pa.get('pos','')):
                        antecedent = toks[j]; break
                clause_ev = None
                for k in range(i+1, len(toks)):
                    pa = primary_analysis(toks[k]['analyses'])
                    if pa and is_verb_pos(pa.get('pos','')):
                        # find graph event with matching token_idx
                        for ev in graph['events']:
                            if ev['token_idx'] == toks[k]['idx']:
                                clause_ev = ev; break
                        if clause_ev: break
                if antecedent and clause_ev:
                    clause_ev['embedded_in'] = {'entity_token': antecedent['token'], 'entity_token_idx': antecedent['idx'], 'sentence': sid}
                    graph['relations'].append({
                        'type': 'relative_clause_attachment',
                        'antecedent_token': antecedent['token'],
                        'antecedent_idx': antecedent['idx'],
                        'clause_event_id': clause_ev['id']
                    })
        graph['sentence_index'][sid] = {'tokens': [x['token'] for x in toks], 'events': [e['id'] for e in sentence_events], 'modality': modality}
    return graph

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 trace_l2_5.py morfeusz_output.json out_graph.json")
        sys.exit(1)
    fin = sys.argv[1]; fout = sys.argv[2]
    with open(fin, 'r', encoding='utf8') as f:
        data = json.load(f)
    graph = compose_l2_5(data)
    with open(fout, 'w', encoding='utf8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print("Saved:", fout)

if __name__ == "__main__":
    main()