"""
ethical_field_agents_interactive.py
-----------------------------------
Interaktywna wersja symulacji rozproszonego pola etycznego.
Kliknięcie myszą dodaje agenta; klawisze zmieniają parametry.
  h  - zwiększ α (dyfuzja)
  j  - zmniejsz α
  k  - zwiększ β (sprzężenie)
  l  - zmniejsz β
  n  - zmiana liczby agentów
  space - zatrzymaj/wznów symulację
W prawym pasku pokazuje aktualne wartości parametrów.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

# --- konfiguracja początkowa ---
N = 80
steps = 300
alpha, beta, gamma = 0.25, 0.05, 0.01
agent_strength = 0.4
agents_n = 25
paused = False

# --- pola i agenci ---
E = np.random.rand(N, N) * 0.2
S = np.random.rand(N, N)
agents = [
    {"x": np.random.randint(0, N),
     "y": np.random.randint(0, N),
     "phase": np.random.rand(),
     "sign": np.random.choice([1, -1])}
    for _ in range(agents_n)
]

# --- aktualizacja ---
def step(E, S, agents):
    lap = (
        np.roll(E, 1, 0) + np.roll(E, -1, 0) +
        np.roll(E, 1, 1) + np.roll(E, -1, 1) - 4 * E
    )
    dE = alpha * lap + beta * (S - E) + gamma * np.random.randn(*E.shape)
    E = np.clip(E + dE, 0, 1)
    S = np.clip(S + 0.1 * (E - S), 0, 1)

    for a in agents:
        x, y = a["x"], a["y"]
        E[x, y] = np.clip(E[x, y] + a["sign"] * agent_strength * (0.5 - E[x, y]), 0, 1)
        a["phase"] += 0.1
        dx = int(np.sign(np.sin(2*np.pi*a["phase"])) * np.sign(np.random.randn()))
        dy = int(np.sign(np.cos(2*np.pi*a["phase"])) * np.sign(np.random.randn()))
        a["x"] = (x + dx) % N
        a["y"] = (y + dy) % N
    return E, S, agents

# --- rysowanie ---
fig, (ax_field, ax_info) = plt.subplots(1, 2, figsize=(9, 5))
im = ax_field.imshow(E, cmap="inferno", vmin=0, vmax=1)
ax_field.set_title("ethical_field_agents_interactive")
ax_field.axis("off")
info_text = ax_info.text(0.05, 0.95, "", va="top", family="monospace")
ax_info.axis("off")

def update_info():
    info_text.set_text(
        f"α (diffusion): {alpha:.3f}\n"
        f"β (coupling): {beta:.3f}\n"
        f"agents: {len(agents)}\n"
        "Hotkeys:\n"
        " h/j : α up/down\n"
        " k/l : β up/down\n"
        " n   : add agent\n"
        " space : pause"
    )

update_info()

# --- obsługa interakcji ---
def on_click(event):
    if event.inaxes == ax_field:
        agents.append({
            "x": int(event.ydata),
            "y": int(event.xdata),
            "phase": np.random.rand(),
            "sign": np.random.choice([1, -1])
        })
        update_info()

def on_key(event):
    global alpha, beta, paused
    if event.key == "h":
        alpha += 0.05
    elif event.key == "j":
        alpha = max(0, alpha - 0.05)
    elif event.key == "k":
        beta += 0.02
    elif event.key == "l":
        beta = max(0, beta - 0.02)
    elif event.key == "n":
        agents.append({
            "x": np.random.randint(0, N),
            "y": np.random.randint(0, N),
            "phase": np.random.rand(),
            "sign": np.random.choice([1, -1])
        })
    elif event.key == " ":
        paused = not paused
    update_info()

fig.canvas.mpl_connect("button_press_event", on_click)
fig.canvas.mpl_connect("key_press_event", on_key)

# --- animacja ---
def update(frame):
    global E, S, agents
    if not paused:
        E, S, agents = step(E, S, agents)
        im.set_array(E)
    return [im, info_text]

ani = animation.FuncAnimation(fig, update, frames=steps, interval=50, blit=True)
plt.tight_layout()
plt.show()
