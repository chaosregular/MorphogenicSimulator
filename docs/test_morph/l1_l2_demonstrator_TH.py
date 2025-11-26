# We'll run a small demonstrator of L1 (syntactic heuristics) and L2 (coreference resolution)
# using sample Morfeusz-style input derived from earlier conversation.
# This code is visible to the user and will print outputs for inspection.
import json
from collections import defaultdict, Counter
import re

# Sample morfeusz-style data (simplified) for two sentences:
sample_data = [
    # Sentence 0: "Ala ma kota."
    {"sentence_id": 0, "token": "Ala", "analyses": [{"base": "Ala", "pos": "subst", "features": "sg:nom:f"}]},
    {"sentence_id": 0, "token": "ma", "analyses": [{"base": "mieć", "pos": "fin", "features": "sg:ter:imperf"}]},
    {"sentence_id": 0, "token": "kota", "analyses": [{"base": "kot", "pos": "subst", "features": "sg:acc:m1"}]},
    {"sentence_id": 0, "token": ".", "analyses": [{"base": ".", "pos": "interp", "features": ""}]},
    # Sentence 1: "Ze wszystkich wspomnień najgorsze było wspomnienie o człowieku, którego zabił, strzelając z bliska, po to, aby tamten nie zabił innych."
    {"sentence_id": 1, "token": "Ze", "analyses": [{"base": "ze", "pos": "prep", "features": ""}]},
    {"sentence_id": 1, "token": "wszystkich", "analyses": [{"base": "wszystek", "pos": "adj", "features": "pl:gen"}]},
    {"sentence_id": 1, "token": "wspomnień", "analyses": [{"base": "wspomnienie", "pos": "subst", "features": "pl:gen"}]},
    {"sentence_id": 1, "token": "najgorsze", "analyses": [{"base": "najgorszy", "pos": "adj", "features": "sg:nom:n"}]},
    {"sentence_id": 1, "token": "było", "analyses": [{"base": "być", "pos": "fin", "features": "sg:ter:past"}]},
    {"sentence_id": 1, "token": "wspomnienie", "analyses": [{"base": "wspomnienie", "pos": "subst", "features": "sg:nom:n"}]},
    {"sentence_id": 1, "token": "o", "analyses": [{"base": "o", "pos": "prep", "features": ""}]},
    {"sentence_id": 1, "token": "człowieku,", "analyses": [{"base": "człowiek", "pos": "subst", "features": "sg:loc:m1"}]},
    {"sentence_id": 1, "token": "którego", "analyses": [{"base": "który", "pos": "pron", "features": "sg:gen:m"}]},
    {"sentence_id": 1, "token": "zabił,", "analyses": [{"base": "zabić", "pos": "praet", "features": "sg:past:m1"}]},
    {"sentence_id": 1, "token": "strzelając", "analyses": [{"base": "strzelać", "pos": "ger", "features": ""}]},
    {"sentence_id": 1, "token": "z", "analyses": [{"base": "z", "pos": "prep", "features": ""}]},
    {"sentence_id": 1, "token": "bliska,", "analyses": [{"base": "blisko", "pos": "adv", "features": ""}]},
    {"sentence_id": 1, "token": "po", "analyses": [{"base": "po", "pos": "prep", "features": ""}]},
    {"sentence_id": 1, "token": "to,", "analyses": [{"base": "to", "pos": "pron", "features": ""}]},
    {"sentence_id": 1, "token": "aby", "analyses": [{"base": "aby", "pos": "conj", "features": ""}]},
    {"sentence_id": 1, "token": "tamten", "analyses": [{"base": "tamten", "pos": "pron", "features": "sg:nom:m"}]},
    {"sentence_id": 1, "token": "nie", "analyses": [{"base": "nie", "pos": "adv", "features": ""}]},
    {"sentence_id": 1, "token": "zabił", "analyses": [{"base": "zabić", "pos": "praet", "features": "sg:past:m1"}]},
    {"sentence_id": 1, "token": "innych", "analyses": [{"base": "inny", "pos": "adj", "features": "pl:gen"}]},
    {"sentence_id": 1, "token": ".", "analyses": [{"base": ".", "pos": "interp", "features": ""}]},
]

# Simple helper functions
def group_by_sentence(data):
    out = defaultdict(list)
    for tok in data:
        out[tok['sentence_id']].append(tok)
    return dict(sorted(out.items()))

def get_primary_analysis(analyses):
    # prefer non-empty base and non-interp pos
    for a in analyses:
        if a.get('pos') and a.get('pos') != 'interp':
            return a
    return analyses[0] if analyses else None

def parse_gender_number(features):
    # parse features like 'sg:nom:f' or 'pl:gen' etc.
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

# Build entities using capitals and qualifiers and noun POS
def extract_entities(data):
    sentences = group_by_sentence(data)
    entities = {}
    eid = 0
    mentions = []
    for sid, toks in sentences.items():
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok['analyses'])
            token_text = tok['token'].strip(' ,.;:')
            # treat nouns (subst) or capitalized tokens as entity candidates
            if a and (a['pos'] == 'subst' or re.match(r'^[A-ZĄĆĘŁŃÓŚŻŹ]', token_text)):
                gender, number = parse_gender_number(a.get('features',''))
                label = token_text
                # create entity id
                eid_str = f"E{eid}"
                entities[eid_str] = {'label': label, 'lemmas': [a.get('base')], 'gender': gender, 'number': number, 'mentions': [(sid, idx, token_text)]}
                mentions.append({'sentence': sid, 'token_idx': idx, 'entity': eid_str, 'text': token_text})
                eid += 1
    return entities, mentions

def resolve_relative_clauses(data, entities, mentions):
    # Find tokens 'który' etc and attach following clause verb to nearest antecedent entity to left (in same sentence)
    sentences = group_by_sentence(data)
    rel_prons = set(['który','która','które','którego','której','którym','których'])
    attachments = []  # list of dicts: {'sentence', 'rel_token_idx', 'antecedent_entity', 'clause_verb_idx', 'clause_verb_lemma'}
    for sid, toks in sentences.items():
        # map token idx -> entity if any
        token_entity_map = {m['token_idx']: m['entity'] for m in mentions if m['sentence']==sid}
        for idx, tok in enumerate(toks):
            text = tok['token'].strip(' ,.;:')
            base = get_primary_analysis(tok['analyses']).get('base','').lower()
            if base in rel_prons:
                # scan left for antecedent entity
                ant = None
                for j in range(idx-1, -1, -1):
                    if j in token_entity_map and token_entity_map[j] is not None:
                        ant = token_entity_map[j]; break
                # find first verb after pron within same sentence
                clause_verb_idx = None; clause_verb_lemma = None
                for k in range(idx+1, len(toks)):
                    a = get_primary_analysis(toks[k]['analyses'])
                    if a and a['pos'] in ('fin','verb','praet','impt','imps','ger'):
                        clause_verb_idx = k
                        clause_verb_lemma = a.get('base')
                        break
                if ant and clause_verb_idx is not None:
                    attachments.append({'sentence': sid, 'rel_token_idx': idx, 'antecedent_entity': ant, 'clause_verb_idx': clause_verb_idx, 'clause_verb_lemma': clause_verb_lemma})
    return attachments

def coreference_resolution(data, entities, mentions):
    # Simple pronominal resolution: map pronouns to nearest compatible entity (gender/number) in previous context
    sentences = group_by_sentence(data)
    pronouns = {'on':('m','sg'), 'ona':('f','sg'), 'oni':('m','pl'), 'one':('n','pl'), 'jego':('m','sg'), 'jej':('f','sg'),'ich':('pl','pl'),'nim':('m','sg'),'nią':('f','sg'),'tamten':('m','sg')}
    resolved = []
    # Build list of entities in document order
    entity_list = []
    for eid, v in entities.items():
        for m in v['mentions']:
            entity_list.append((m[0], m[1], eid, v))  # sentence, idx, eid, entity
    # sort by sentence, idx
    entity_list.sort()
    for sid, toks in sentences.items():
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok['analyses'])
            base = a.get('base','').lower()
            if base in pronouns:
                desired_gender, desired_number = pronouns[base]
                # search backwards in entity_list for candidate before this sentence/idx
                cand = None
                for s, t, eid, ent in reversed(entity_list):
                    if s > sid or (s==sid and t >= idx):
                        continue
                    # check compatibility
                    g = ent.get('gender'); n = ent.get('number')
                    # normalize numbers
                    ng = None
                    if n=='sg': ng_n = 'sg'
                    elif n=='pl': ng_n='pl'
                    else: ng_n=None
                    if (g and desired_gender and desired_gender.startswith(g)) or (g and desired_gender and g.startswith(desired_gender)) or (not g):
                        # number check loose
                        cand = eid; break
                if cand:
                    resolved.append({'pronoun': base, 'sentence': sid, 'token_idx': idx, 'resolved_entity': cand})
    return resolved

def enhanced_event_extraction(data, entities, mentions, attachments, corefs):
    sentences = group_by_sentence(data)
    events = []
    for sid, toks in sentences.items():
        # identify main content verbs (not copula 'być' unless no other)
        verb_candidates = []
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok['analyses'])
            if a and a['pos'] in ('fin','verb','praet','impt','imps','ger'):
                verb_candidates.append((idx, a.get('base')))
        main_verb = None
        if verb_candidates:
            # prefer non-'być' verbs if possible, select earliest non-być
            for idx, lemma in verb_candidates:
                if lemma != 'być':
                    main_verb = (idx, lemma); break
            if main_verb is None:
                main_verb = verb_candidates[0]
        # determine subject/object by proximity and coref info
        subj = None; obj = None
        # mentions in sentence
        sent_mentions = [m for m in mentions if m['sentence']==sid and m.get('entity')]
        # map mention idx to entity id
        mention_map = {m['token_idx']: m['entity'] for m in sent_mentions}
        if main_verb:
            v_idx = main_verb[0]
            # find nearest entity left and right
            left = [m for m in sent_mentions if m['token_idx'] < v_idx]
            right = [m for m in sent_mentions if m['token_idx'] > v_idx]
            if left: subj = left[-1]['entity']
            if right: obj = right[0]['entity']
        # consider relative clause attachments that add actions to antecedents
        added = []
        for att in attachments:
            if att['sentence']==sid:
                added.append({'antecedent': att['antecedent_entity'], 'verb': att['clause_verb_lemma'], 'verb_idx': att['clause_verb_idx']})
        # consider pronoun corefs mapping to entities as subjects if present
        for c in corefs:
            if c['sentence']==sid:
                # if pronoun occurs near verb, assign as subj
                if main_verb and abs(c['token_idx'] - main_verb[0]) <= 2:
                    subj = c['resolved_entity']
        events.append({'sentence': sid, 'main_verb': main_verb, 'subject': subj, 'object': obj, 'attachments': added})
    return events

# Run pipeline on sample
entities, mentions = extract_entities(sample_data)
attachments = resolve_relative_clauses(sample_data, entities, mentions)
corefs = coreference_resolution(sample_data, entities, mentions)
events = enhanced_event_extraction(sample_data, entities, mentions, attachments, corefs)

print("=== ENTITIES ===")
print(json.dumps(entities, ensure_ascii=False, indent=2))
print("\n=== MENTIONS ===")
print(json.dumps(mentions, ensure_ascii=False, indent=2))
print("\n=== RELATIVE CLAUSE ATTACHMENTS ===")
print(json.dumps(attachments, ensure_ascii=False, indent=2))
print("\n=== COREF RESOLUTIONS ===")
print(json.dumps(corefs, ensure_ascii=False, indent=2))
print("\n=== EVENTS ===")
print(json.dumps(events, ensure_ascii=False, indent=2))
