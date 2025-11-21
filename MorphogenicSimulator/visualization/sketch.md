Wizualizacja - Prosty Interfejs
```
# Przykład danych wyjściowych do wizualizacji
visualization_data = {
    'nodes': [
        {'id': 'kid_metaphor', 'type': 'light', 'size': 0.95, 'x': 0.1, 'y': 0.9},
        {'id': 'koryto_system', 'type': 'dark', 'size': 0.3, 'x': 0.8, 'y': 0.2},
        {'id': 'truth', 'type': 'light', 'size': 0.98, 'x': 0.5, 'y': 0.5}
    ],
    'links': [
        {'source': 'kid_metaphor', 'target': 'truth', 'strength': 0.9},
        {'source': 'koryto_system', 'target': 'truth', 'strength': 0.1}
    ]
}
```
KOMENTARZ:
Te dane można wyświetlić w:

    D3.js dla interaktywnej wizualizacji w przeglądarce
    Matplotlib dla statycznych wykresów
    NetworkX dla analizy sieciowej
