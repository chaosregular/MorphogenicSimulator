# l2_extractor_v1.py
import json
import sys
import re

MODAL_MARKERS = {
    "certainty_high": ["na pewno", "z pewnością"],
    "uncertainty": ["chyba", "zdaje się", "zdawało się", "jakby"],
    "necessity": ["musiał", "musiała", "musieli"],
    "possibility": ["mógł", "mogła", "mogli", "możliwe"],
}

def detect_modality(tokens):
    modal = []
    joined = " ".join(tokens).lower()
    for cat, markers in MODAL_MARKERS.items():
        for m in markers:
            if m in joined:
                modal.append({"category": cat, "marker": m})
    return modal

def extract_l2(data):
    results = []

    for entry in data:
        token = entry["token"]
        sid = entry["sentence_id"]

        # detekcja czasowników jako rdzeni predykatów
        verbs = [
            a for a in entry["analyses"]
            if a["pos"] in ["fin", "praet", "impt", "inf"]
        ]

        # rzeczowniki → potencjalne encje
        nouns = [
            a for a in entry["analyses"]
            if a["pos"] in ["subst", "depr"]
        ]

        # przymiotniki → opisy cech
        adjs = [
            a for a in entry["analyses"]
            if a["pos"] == "adj"
        ]

        # proste założenie L2:
        # zdanie = (eventy, uczestnicy, cechy, modalność)
        results.append({
            "sentence_id": sid,
            "token": token,
            "verbs": verbs,
            "nouns": nouns,
            "adjectives": adjs
        })

    # po tokenach: grupowanie per zdanie
    grouped = {}
    for r in results:
        grouped.setdefault(r["sentence_id"], []).append(r)

    final = []

    for sid, entries in grouped.items():
        tokens = [e["token"] for e in entries]
        modality = detect_modality(tokens)

        events = []
        entities = []

        for e in entries:
            for v in e["verbs"]:
                events.append({
                    "token": e["token"],
                    "lemma": v["base"],
                    "features": v["features"]
                })

            for n in e["nouns"]:
                entities.append({
                    "token": e["token"],
                    "lemma": n["base"],
                    "features": n["features"]
                })

        final.append({
            "sentence_id": sid,
            "tokens": tokens,
            "events": events,
            "entities": entities,
            "modality": modality
        })

    return final


def main():
    if len(sys.argv) < 2:
        print("Użycie: python3 l2_extractor_v1.py morfeusz_output.json")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r", encoding="utf8") as f:
        data = json.load(f)

    l2 = extract_l2(data)
    outname = "l2_output.json"
    with open(outname, "w", encoding="utf8") as f:
        json.dump(l2, f, ensure_ascii=False, indent=2)

    print("Zapisano:", outname)


if __name__ == "__main__":
    main()