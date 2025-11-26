"""
morpho_to_entities.py
Wejście: morfeusz_output_YYYYMMDD_HHMMSS.json
Wyjście: entities_events_output.json
"""
import sys, json, os, time, re
from collections import defaultdict, Counter

# -- mały leksykon etyczny do szybkich etykiet (rozszerzalny)
ETH_LEXICON = {
    "zabić": -1.0, "zamordować": -1.0, "zniszczyć": -0.8,
    "uratować": 1.0, "pomóc": 0.8, "ochraniać": 0.7,
    "ukraść": -0.9, "dać": 0.6, "podzielić": 0.3, "wspierać": 0.7,
    "kłamać": -0.7, "oszukać": -0.8, "decydować": 0.0, "postanowić": 0.0
}

# heurystyki: tagi morfeusza rozpoznające nominalne entity
ENTITY_QUALIFIERS = set(["imię", "nazwisko", "nazwa_geograficzna", "nazwa_pospolita"])

def load_json(fn):
    with open(fn, "r", encoding="utf8") as f:
        return json.load(f)

def is_capitalized(token):
    return bool(re.match(r'^[A-ZĄĆĘŁŃÓŚŻŹ]', token))

def gather_entities(morfeusz_data):
    """
    morfeusz_data: lista dictów:
      { sentence_id, token, analyses: [ {base,pos,features}, ... ] }
    Zwraca: entities dict i mentions list (for timeline)
    """
    entities = {}  # id -> {label, type, lemmas, mentions: [...], count}
    entity_counter = 0
    mentions = []  # list of (sent_id, token_idx, entity_id or None, raw_token, analyses)

    # map from token index per sentence to entity id (for multiword)
    for sent_id, group in group_by_sentence(morfeusz_data).items():
        tokens = group
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            token_text = tok["token"]
            analyses = tok.get("analyses", [])
            # check qualifiers
            quals = set()
            lemmas = set()
            poses = set()
            for a in analyses:
                lem = a.get("base","")
                lemmas.add(lem)
                pos = a.get("pos","")
                poses.add(pos)
                # check qualifiers in a naive way: features string may contain qualifiers?
                feat = a.get("features","")
                # Morfeusz had qualifiers in separate element but here we rely on 'features' or base patterns
                if any(q in str(a.get("base","")) for q in ENTITY_QUALIFIERS):
                    quals.add("qual_base")
                # fallback: capitalization
            # simple detection: if any analysis tags semantic qualifier or capitalized
            candidate_entity = None
            if analyses:
                # try to detect semantic qualifier via features token (some outputs keep qualifiers in features)
                for a in analyses:
                    feat = a.get("features","")
                    # look for known qualifiers as words in features
                    for q in ENTITY_QUALIFIERS:
                        if q in feat:
                            candidate_entity = {"type": q}
                            break
                    if candidate_entity:
                        break
            if not candidate_entity and is_capitalized(token_text):
                # assume proper noun candidate (may be multiword)
                # collect following capitalized tokens as part of same name
                name_tokens = [token_text]
                j = i+1
                while j < len(tokens) and is_capitalized(tokens[j]["token"]):
                    name_tokens.append(tokens[j]["token"])
                    j += 1
                label = " ".join(name_tokens)
                # generate entity
                eid = f"E{entity_counter}"
                entity_counter += 1
                entities[eid] = {"label": label, "type": "proper", "lemmas": list(lemmas), "mentions": [{"sentence": sent_id, "token_idx": i, "text": label}], "count": 1}
                mentions.append({"sentence": sent_id, "token_idx": i, "entity": eid, "text": label})
                i = j
                continue
            # fallback: no entity
            mentions.append({"sentence": sent_id, "token_idx": i, "entity": None, "text": token_text, "analyses": analyses})
            i += 1
    # merge simple duplicates by label
    label_map = {}
    for eid, v in list(entities.items()):
        lab = v["label"]
        if lab in label_map:
            # merge
            existing = label_map[lab]
            entities[existing]["mentions"].extend(v["mentions"])
            entities[existing]["count"] += v["count"]
            del entities[eid]
        else:
            label_map[lab] = eid
    return entities, mentions

def group_by_sentence(morfeusz_data):
    out = defaultdict(list)
    for tok in morfeusz_data:
        sid = tok.get("sentence_id",0)
        out[sid].append(tok)
    # ensure tokens in sentence order (assumes original order preserved)
    return dict(sorted(out.items()))

def build_events(morfeusz_data, entities, mentions):
    """
    Prosty event extraction per sentence:
     - find main finite verb (pos == 'fin' or pos == 'verb')
     - find nearest entity mentions to left/right as subject/object (heuristic)
    """
    sentences = group_by_sentence(morfeusz_data)
    events = []
    for sid, tokens in sentences.items():
        # find index of first finite verb
        verb_idx = None
        verb_lemma = None
        for idx, tok in enumerate(tokens):
            for a in tok.get("analyses", []):
                if a.get("pos","") in ("fin","verb","praet","impt","imps"):
                    verb_idx = idx
                    verb_lemma = a.get("base")
                    break
            if verb_idx is not None:
                break
        # collect candidate entities in sentence
        sent_entities = []
        for m in mentions:
            if m["sentence"] == sid and m.get("entity"):
                sent_entities.append(m)
        # heuristics: subject = nearest entity to left of verb, object = nearest to right
        subj = None; obj = None
        if verb_idx is not None:
            # find mention indices within sentence
            left = [m for m in sent_entities if m["token_idx"] < verb_idx]
            right = [m for m in sent_entities if m["token_idx"] > verb_idx]
            if left:
                subj = left[-1]["entity"]
            if right:
                obj = right[0]["entity"]
        events.append({
            "sentence": sid,
            "verb_index": verb_idx,
            "verb_lemma": verb_lemma,
            "subject_entity": subj,
            "object_entity": obj,
            "raw_tokens": [t["token"] for t in tokens]
        })
    return events

def detect_decisions(events, morfeusz_data):
    decisions = []
    # naive: verbs with lemma in decision lexicon
    decision_verbs = set(["zdecydować","postanowić","postanawiać","postanowic","decydowac"])
    for ev in events:
        v = ev.get("verb_lemma")
        if v and v in decision_verbs:
            decisions.append({
                "sentence": ev["sentence"],
                "actor": ev["subject_entity"],
                "action": v,
                "confidence": 0.6
            })
    return decisions

def ethical_annotate(events):
    out = []
    for ev in events:
        v = ev.get("verb_lemma")
        score = 0.0; conf = 0.0
        if v:
            # leksykon match
            val = ETH_LEXICON.get(v)
            if val is not None:
                score = val
                conf = 0.7
            else:
                # fuzzy match by startswith
                for k in ETH_LEXICON:
                    if v and str(v).startswith(k):
                        score = ETH_LEXICON[k]
                        conf = 0.4
                        break
        out.append({"sentence": ev["sentence"], "verb": v, "ethical_score": score, "ethical_confidence": conf})
    return out

# ---- BEGIN L1+L2 INTEGRATION (paste into morpho_to_entities.py) ----

# import re
# from collections import defaultdict

def group_by_sentence(data):
    out = defaultdict(list)
    for tok in data:
        out[tok['sentence_id']].append(tok)
    return dict(sorted(out.items()))

def get_primary_analysis(analyses):
    if not analyses:
        return None
    for a in analyses:
        if a.get('pos') and a.get('pos') != 'interp':
            return a
    return analyses[0]

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

def resolve_relative_clauses(morfeusz_data, mentions):
    """
    Attach actions from relative clauses to their antecedent entities.
    Returns list of attachments: {sentence, rel_token_idx, antecedent_entity, clause_verb_idx, clause_verb_lemma}
    """
    sentences = group_by_sentence(morfeusz_data)
    rel_prons = set(['który','która','które','którego','której','którym','których'])
    attachments = []
    for sid, toks in sentences.items():
        token_entity_map = {m['token_idx']: m['entity'] for m in mentions if m['sentence']==sid}
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok.get('analyses',[]))
            if not a:
                continue
            base = str(a.get('base','')).lower()
            if base in rel_prons:
                # antecedent: nearest entity to left in same sentence
                antecedent = None
                for j in range(idx-1, -1, -1):
                    if j in token_entity_map and token_entity_map[j] is not None:
                        antecedent = token_entity_map[j]; break
                # find first verb after pron within same sentence
                clause_verb_idx = None; clause_verb_lemma = None
                for k in range(idx+1, len(toks)):
                    a2 = get_primary_analysis(toks[k].get('analyses',[]))
                    if a2 and a2.get('pos') in ('fin','verb','praet','impt','imps','ger'):
                        clause_verb_idx = k
                        clause_verb_lemma = a2.get('base')
                        break
                if antecedent and clause_verb_idx is not None:
                    attachments.append({'sentence': sid, 'rel_token_idx': idx,
                                        'antecedent_entity': antecedent,
                                        'clause_verb_idx': clause_verb_idx,
                                        'clause_verb_lemma': clause_verb_lemma})
    return attachments

def coreference_resolution(morfeusz_data, entities, mentions):
    """
    Very small rule-based coref: pronouns -> nearest compatible entity in previous context.
    Returns list of resolved pronouns: {pronoun, sentence, token_idx, resolved_entity}
    """
    sentences = group_by_sentence(morfeusz_data)
    pronouns = {'on':('m','sg'), 'ona':('f','sg'), 'oni':('m','pl'), 'one':('n','pl'),
                'jego':('m','sg'), 'jej':('f','sg'),'ich':('pl','pl'),'nim':('m','sg'),
                'nią':('f','sg'),'tamten':('m','sg'),'ten':(None,None),'to':(None,None),'ono':('n','sg')}
    resolved = []

    # build ordered entity list by position
    entity_list = []
    for eid, v in entities.items():
        for m in v.get('mentions',[]):
            entity_list.append((m['sentence'] if isinstance(m, dict) else m[0],
                                m['token_idx'] if isinstance(m, dict) else m[1],
                                eid, v))
    entity_list.sort()
    for sid, toks in sentences.items():
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok.get('analyses',[]))
            if not a:
                continue
            base = str(a.get('base','')).lower()
            if base in pronouns:
                desired_gender, desired_number = pronouns[base]
                cand = None
                for s, t, eid, ent in reversed(entity_list):
                    if s > sid or (s==sid and t >= idx):
                        continue
                    g = ent.get('gender'); n = ent.get('number')
                    # loose compatibility checks
                    if desired_gender is None:
                        cand = eid; break
                    if g and desired_gender and str(g).startswith(str(desired_gender)[0]):
                        cand = eid; break
                    if n and desired_number and n==desired_number:
                        cand = eid; break
                if cand:
                    resolved.append({'pronoun': base, 'sentence': sid, 'token_idx': idx, 'resolved_entity': cand})
    return resolved

def enhanced_event_extraction(morfeusz_data, entities, mentions, attachments, corefs):
    """
    Replace simple event builder with enhanced one:
    - choose main non-copula verb when possible
    - assign subject/object by proximity and use coref to correct subject if pronoun present
    - include attachments from relative clauses as events for antecedents
    """
    sentences = group_by_sentence(morfeusz_data)
    events = []
    for sid, toks in sentences.items():
        # collect verb candidates
        verb_candidates = []
        for idx, tok in enumerate(toks):
            a = get_primary_analysis(tok.get('analyses',[]))
            if a and a.get('pos') in ('fin','verb','praet','impt','imps','ger'):
                verb_candidates.append((idx, a.get('base')))
        main_verb = None
        if verb_candidates:
            # prefer first non-'być' verb
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
        # integrate attachments and corefs
        added = [ {'antecedent': a['antecedent_entity'], 'verb': a['clause_verb_lemma']} for a in attachments if a['sentence']==sid ]
        for c in corefs:
            if c['sentence']==sid and main_verb and abs(c['token_idx'] - main_verb[0]) <= 2:
                subj = c['resolved_entity']
        events.append({'sentence': sid, 'main_verb': main_verb, 'subject': subj, 'object': obj, 'attachments': added})
    return events

# ---- END L1+L2 INTEGRATION ----


def main():
    if len(sys.argv) < 2:
        print("Użycie: python3 morpho_to_entities.py morfeusz_output.json")
        sys.exit(1)
    fn = sys.argv[1]
    data = load_json(fn)
    entities, mentions = gather_entities(data)
    attachments = resolve_relative_clauses(data, mentions)
    corefs = coreference_resolution(data, entities, mentions)
    events = enhanced_event_extraction(data, entities, mentions, attachments, corefs)
    decisions = detect_decisions(events, data)
    ethics = ethical_annotate(events)

    out = {
        "meta": {"source": fn, "generated": time.strftime("%Y%m%d_%H%M%S")},
        "entities": entities,
        "mentions": mentions,
        "events": events,
        "decisions": decisions,
        "ethical_annotations": ethics
    }

    outfn = f"entities_events_{int(time.time())}.json"
    with open(outfn, "w", encoding="utf8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Zapisano: {outfn}")

if __name__ == "__main__":
    main()
