#!/usr/bin/env python3
# l1_l2_demonstrator.py
# L1: lightweight syntactic heuristics (relative clause attachments)
# L2: rule-based coreference resolution (pronouns -> nearest compatible entity)
# Input: morfeusz-style JSON list (token entries with sentence_id, token, analyses)
# For quick test you can embed small sample_data as in the demo.

import json, re
from collections import defaultdict

def group_by_sentence(data):
    out = defaultdict(list)
    for tok in data:
        out[tok['sentence_id']].append(tok)
    return dict(sorted(out.items()))

def get_primary_analysis(analyses):
    for a in analyses:
        if a.get('pos') and a.get('pos') != 'interp':
            return a
    return analyses[0] if analyses else None

def parse_gender_number(features):
    gender = None
    number = None
    if not features:
        return gender, number
    parts = features.split(':')
    for p in parts:
        if p in ('sg','pl'):
            number = p
        if p in ('m','f','n','m1','m2','m3'):
            gender = p
    return gender, number

def extract_entities(data):
    sentences = group_by_sentence(data)
    entities = {}
    eid = 0
    mentions = []
    for sid, toks in sentences.items():
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok.get('analyses', []))
            token_text = tok['token'].strip(' ,.;:')
            if not token_text:
                continue
            if a and (a.get('pos') == 'subst' or re.match(r'^[A-ZĄĆĘŁŃÓŚŻŹ]', token_text)):
                gender, number = parse_gender_number(a.get('features',''))
                label = token_text
                eid_str = f"E{eid}"
                entities[eid_str] = {'label': label, 'lemmas': [a.get('base')], 'gender': gender, 'number': number, 'mentions': [(sid, idx, token_text)]}
                mentions.append({'sentence': sid, 'token_idx': idx, 'entity': eid_str, 'text': token_text})
                eid += 1
    # merge identical labels
    label_map = {}
    for e, v in list(entities.items()):
        lab = v['label']
        if lab in label_map:
            existing = label_map[lab]
            entities[existing]['mentions'].extend(v['mentions'])
            entities[existing]['lemmas'].extend([x for x in v['lemmas'] if x not in entities[existing]['lemmas']])
            del entities[e]
        else:
            label_map[lab] = e
    return entities, mentions

def resolve_relative_clauses(data, mentions):
    sentences = group_by_sentence(data)
    rel_prons = set(['który','która','które','którego','której','którym','których'])
    attachments = []
    for sid, toks in sentences.items():
        token_entity_map = {m['token_idx']: m['entity'] for m in mentions if m['sentence']==sid}
        for idx, tok in enumerate(toks):
            base = get_primary_analysis(tok.get('analyses',[])).get('base','').lower()
            if base in rel_prons:
                antecedent = None
                for j in range(idx-1, -1, -1):
                    if j in token_entity_map and token_entity_map[j] is not None:
                        antecedent = token_entity_map[j]; break
                clause_verb_idx = None; clause_verb_lemma = None
                for k in range(idx+1, len(toks)):
                    a = get_primary_analysis(toks[k].get('analyses',[]))
                    if a and a.get('pos') in ('fin','verb','praet','impt','imps','ger'):
                        clause_verb_idx = k
                        clause_verb_lemma = a.get('base')
                        break
                if antecedent and clause_verb_idx is not None:
                    attachments.append({'sentence': sid, 'rel_token_idx': idx, 'antecedent_entity': antecedent, 'clause_verb_idx': clause_verb_idx, 'clause_verb_lemma': clause_verb_lemma})
    return attachments

def coreference_resolution(data, entities, mentions):
    sentences = group_by_sentence(data)
    pronouns = {'on':('m','sg'), 'ona':('f','sg'), 'oni':('m','pl'), 'one':('n','pl'),
                'jego':('m','sg'), 'jej':('f','sg'),'ich':('pl','pl'),'nim':('m','sg'),'nią':('f','sg'),
                'tamten':('m','sg'),'ten':(None,None),'to':(None,None),'ono':('n','sg')}
    resolved = []
    # build ordered entity list by position
    entity_list = []
    for eid, v in entities.items():
        for m in v['mentions']:
            entity_list.append((m[0], m[1], eid, v))
    entity_list.sort()
    for sid, toks in sentences.items():
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok.get('analyses',[]))
            base = a.get('base','').lower()
            if base in pronouns:
                desired_gender, desired_number = pronouns[base]
                cand = None
                for s, t, eid, ent in reversed(entity_list):
                    if s > sid or (s==sid and t >= idx):
                        continue
                    # simple compatibility: if entity has gender and matches pronoun gender (loose)
                    g = ent.get('gender'); n = ent.get('number')
                    if desired_gender is None:
                        cand = eid; break
                    if g and desired_gender and desired_gender.startswith(str(g)[0]):
                        cand = eid; break
                    # fallback: accept if number matches roughly
                    if n and desired_number and n==desired_number:
                        cand = eid; break
                if cand:
                    resolved.append({'pronoun': base, 'sentence': sid, 'token_idx': idx, 'resolved_entity': cand})
    return resolved

def enhanced_event_extraction(data, entities, mentions, attachments, corefs):
    sentences = group_by_sentence(data)
    events = []
    for sid, toks in sentences.items():
        verb_candidates = []
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok.get('analyses',[]))
            if a and a.get('pos') in ('fin','verb','praet','impt','imps','ger'):
                verb_candidates.append((idx, a.get('base')))
        main_verb = None
        if verb_candidates:
            for idx, lemma in verb_candidates:
                if lemma != 'być':
                    main_verb = (idx, lemma); break
            if main_verb is None:
                main_verb = verb_candidates[0]
        subj = None; obj = None
        sent_mentions = [m for m in mentions if m['sentence']==sid and m.get('entity')]
        if main_verb:
            v_idx = main_verb[0]
            left = [m for m in sent_mentions if m['token_idx'] < v_idx]
            right = [m for m in sent_mentions if m['token_idx'] > v_idx]
            if left: subj = left[-1]['entity']
            if right: obj = right[0]['entity']
        # include attachments if any for this sentence
        added = [ {'antecedent': a['antecedent_entity'], 'verb': a['clause_verb_lemma']} for a in attachments if a['sentence']==sid ]
        # use corefs to override subj if pronoun near verb
        for c in corefs:
            if c['sentence']==sid:
                if main_verb and abs(c['token_idx'] - main_verb[0]) <= 2:
                    subj = c['resolved_entity']
        events.append({'sentence': sid, 'main_verb': main_verb, 'subject': subj, 'object': obj, 'attachments': added})
    return events

def run_pipeline(morfeusz_data):
    entities, mentions = extract_entities(morfeusz_data)
    attachments = resolve_relative_clauses(morfeusz_data, mentions)
    corefs = coreference_resolution(morfeusz_data, entities, mentions)
    events = enhanced_event_extraction(morfeusz_data, entities, mentions, attachments, corefs)
    out = {'entities': entities, 'mentions': mentions, 'attachments': attachments, 'corefs': corefs, 'events': events}
    return out

if __name__ == "__main__":
    # Sample usage: load morfeusz JSON file passed as arg, otherwise run built-in tiny example
    import sys
    if len(sys.argv) >= 2:
        fn = sys.argv[1]
        with open(fn, 'r', encoding='utf8') as f:
            data = json.load(f)
    else:
        # tiny sample - replace with your morfeusz output file in real tests
        data = [
            {"sentence_id":0,"token":"Ala","analyses":[{"base":"Ala","pos":"subst","features":"sg:nom:f"}]},
            {"sentence_id":0,"token":"ma","analyses":[{"base":"mieć","pos":"fin","features":"sg:ter:imperf"}]},
            {"sentence_id":0,"token":"kota","analyses":[{"base":"kot","pos":"subst","features":"sg:acc:m1"}]},
            {"sentence_id":0,"token":".","analyses":[{"base":".","pos":"interp","features":""}]},
            {"sentence_id":1,"token":"Ze","analyses":[{"base":"ze","pos":"prep","features":""}]},
            {"sentence_id":1,"token":"wszystkich","analyses":[{"base":"wszystek","pos":"adj","features":"pl:gen"}]},
            {"sentence_id":1,"token":"wspomnień","analyses":[{"base":"wspomnienie","pos":"subst","features":"pl:gen"}]},
            {"sentence_id":1,"token":"najgorsze","analyses":[{"base":"najgorszy","pos":"adj","features":"sg:nom:n"}]},
            {"sentence_id":1,"token":"było","analyses":[{"base":"być","pos":"fin","features":"sg:ter:past"}]},
            {"sentence_id":1,"token":"wspomnienie","analyses":[{"base":"wspomnienie","pos":"subst","features":"sg:nom:n"}]},
            {"sentence_id":1,"token":"o","analyses":[{"base":"o","pos":"prep","features":""}]},
            {"sentence_id":1,"token":"człowieku,","analyses":[{"base":"człowiek","pos":"subst","features":"sg:loc:m1"}]},
            {"sentence_id":1,"token":"którego","analyses":[{"base":"który","pos":"pron","features":"sg:gen:m"}]},
            {"sentence_id":1,"token":"zabił,","analyses":[{"base":"zabić","pos":"praet","features":"sg:past:m1"}]},
            {"sentence_id":1,"token":"strzelając","analyses":[{"base":"strzelać","pos":"ger","features":""}]},
            {"sentence_id":1,"token":"z","analyses":[{"base":"z","pos":"prep","features":""}]},
            {"sentence_id":1,"token":"bliska,","analyses":[{"base":"blisko","pos":"adv","features":""}]},
            {"sentence_id":1,"token":"po","analyses":[{"base":"po","pos":"prep","features":""}]},
            {"sentence_id":1,"token":"to,","analyses":[{"base":"to","pos":"pron","features":""}]},
            {"sentence_id":1,"token":"aby","analyses":[{"base":"aby","pos":"conj","features":""}]},
            {"sentence_id":1,"token":"tamten","analyses":[{"base":"tamten","pos":"pron","features":"sg:nom:m"}]},
            {"sentence_id":1,"token":"nie","analyses":[{"base":"nie","pos":"adv","features":""}]},
            {"sentence_id":1,"token":"zabił","analyses":[{"base":"zabić","pos":"praet","features":"sg:past:m1"}]},
            {"sentence_id":1,"token":"innych","analyses":[{"base":"inny","pos":"adj","features":"pl:gen"}]},
            {"sentence_id":1,"token":".","analyses":[{"base":".","pos":"interp","features":""}]}
        ]
    result = run_pipeline(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
