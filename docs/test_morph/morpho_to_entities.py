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

def main():
    if len(sys.argv) < 2:
        print("Użycie: python3 morpho_to_entities.py morfeusz_output.json")
        sys.exit(1)
    fn = sys.argv[1]
    data = load_json(fn)
    entities, mentions = gather_entities(data)
    events = build_events(data, entities, mentions)
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