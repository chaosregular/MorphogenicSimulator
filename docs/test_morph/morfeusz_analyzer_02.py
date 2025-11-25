import sys
import json
import time
from morfeusz2 import Morfeusz

def analyze_text(text):
    """
    Zwraca listę:
    [
      {
        "sentence_id": int,
        "token": str,
        "analyses": [
            {
               "base": str,
               "pos": str,
               "features": str
            },
            ...
        ]
      },
      ...
    ]
    """
    morf = Morfeusz()
    results = []
    sentence_id = 0

    # Bardzo prosty tokenizer zdań
    sentences = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in ".!?":
            sentences.append(buf.strip())
            buf = ""
    if buf.strip():
        sentences.append(buf.strip())

    for sid, sentence in enumerate(sentences):
        tokens = sentence.split()

        # Morfeusz działa na sekwencji znaków, ale analizuje jedno słowo
        for token in tokens:
            analyses_raw = morf.analyse(token)
            analyses = []

            for pos_info in analyses_raw:
                print(f"DEBUG: pos_info dla tokena '{token}': {pos_info}, Typ: {type(pos_info)}")
                # Poprawne rozpakowanie dla struktury:
                # (0, 1, ('Ala', 'Ala', 'subst:sg:nom:f', ['imię'], []))
                 
                # Interesuje nas tylko trzeci element pos_info
                analysis_tuple = pos_info[2]
                 
                # Teraz rozpakowujemy zagnieżdżoną tuplę:
                # ('Ala', 'Ala', 'subst:sg:nom:f', ['imię'], [])
                _, base, tag, _, _ = analysis_tuple

                # 'base' to teraz 'Ala' (string)
                # 'tag' to teraz 'subst:sg:nom:f' (string)

                # tag formatu "subst:sg:nom:m1"
                parts = tag.split(":")
                if len(parts) > 0:
                    pos = parts[0]
                    features = ":".join(parts[1:])
                else:
                    pos = tag
                    features = ""

                analyses.append({
                    "base": base,
                    "pos": pos,
                    "features": features
                })

            results.append({
                "sentence_id": sid,
                "token": token,
                "analyses": analyses
            })



    return results


def main():
    if len(sys.argv) < 2:
        print("Użycie: python3 morfeusz_analyzer.py plik.txt [--save]")
        sys.exit(1)

    filename = sys.argv[1]
    save = ("--save" in sys.argv)

    with open(filename, "r", encoding="utf8") as f:
        text = f.read()

    data = analyze_text(text)

    # Wypisz na ekran
    for entry in data:
        print(f"[Zdanie {entry['sentence_id']}] {entry['token']}")
        for a in entry["analyses"]:
            print(f"  - base={a['base']} pos={a['pos']} feat={a['features']}")
        print()

    if save:
        ts = time.strftime("%Y%m%d_%H%M%S")
        outname = f"morfeusz_output_{ts}.json"
        with open(outname, "w", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nZapisano wynik do: {outname}")


if __name__ == "__main__":
    main()