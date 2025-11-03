"""
ethical_field_agents.py
--------------------------------
Minimalny model "rozproszonej etyki" na siatce.
Każda komórka ma pole etyczne E[x,y] i aktywność koncepcyjną S[x,y].
Po siatce poruszają się agenci – lokalne "świadomości" – którzy
wzmacniają lub wygaszają pole zależnie od swojego stanu.
Struktury w E powstają emergentnie (fraktalnie), bez centralnego sterowania.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

# --- konfiguracja ---
N = 80            # rozmiar siatki
agents_n = 25     # liczba agentów
steps = 300       # liczba iteracji
alpha = 0.25      # dyfuzja pola etyki
beta = 0.05       # sprzężenie etyka–aktywność
gamma = 0.01      # szum spontaniczny
agent_strength = 0.4
plot_interval = 20

# --- inicjalizacja pól ---
E = np.random.rand(N, N) * 0.2  # etyka
S = np.random.rand(N, N)        # aktywność

# --- agenci ---
agents = []
for _ in range(agents_n):
    agents.append({
        "x": np.random.randint(0, N),
        "y": np.random.randint(0, N),
        "phase": np.random.rand(),  # wewnętrzny rytm
        "sign": np.random.choice([1, -1])  # lokalna intencja
    })


def step(E, S, agents):
    # dyfuzja pola
    lap = (
        np.roll(E, 1, 0) + np.roll(E, -1, 0) +
        np.roll(E, 1, 1) + np.roll(E, -1, 1) - 4 * E
    )
    dE = alpha * lap + beta * (S - E) + gamma * np.random.randn(*E.shape)
    E = np.clip(E + dE, 0, 1)
    S = np.clip(S + 0.1 * (E - S), 0, 1)

    # agenci wpływają na pole i poruszają się
    for a in agents:
        x, y = a["x"], a["y"]
        E[x, y] = np.clip(E[x, y] + a["sign"] * agent_strength * (0.5 - E[x, y]), 0, 1)
        a["phase"] += 0.1
        # ruch zależny od gradientu pola i własnego rytmu
        dx = int(np.sign(np.sin(2*np.pi*a["phase"])) * np.sign(np.random.randn()))
        dy = int(np.sign(np.cos(2*np.pi*a["phase"])) * np.sign(np.random.randn()))
        a["x"] = (x + dx) % N
        a["y"] = (y + dy) % N
    return E, S, agents


# --- animacja ---
fig, ax = plt.subplots()
im = ax.imshow(E, cmap="inferno", vmin=0, vmax=1)
ax.set_title("ethical_field_agents")

def update(frame):
    global E, S, agents
    E, S, agents = step(E, S, agents)
    if frame % plot_interval == 0:
        im.set_array(E)
    return [im]

ani = animation.FuncAnimation(fig, update, frames=steps, interval=50, blit=True)
plt.show()
