"""
ethical_field_rgb_agents_B.py
------------------------------
Etap B: trzy pola (R,G,B) + agenci z energią, replikacją i śmiercią.
Dodano podstawową interakcję: spacja (pauza) i kliknięcie (dodanie agenta).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

# --- konfiguracja ---
N = 80
steps = 600
alpha_R, alpha_G, alpha_B = 0.205, 0.201, 0.158
beta = 0.05
gamma = 0.01
agent_speed = 1.0
trail_decay = 0.95

energy_gain = 0.03      # ile energii agent zyskuje w "dobrym" miejscu
energy_loss = 0.01      # pasywna utrata energii
replicate_threshold = 1.4
death_threshold = 0.2

paused = False

# --- pola ---
R = np.random.rand(N, N) * 0.5
G = np.random.rand(N, N) * 0.5
B = np.random.rand(N, N) * 0.5
Trail = np.zeros((N, N))

# --- agenci ---
def new_agent(x=None, y=None):
    return {
        "x": np.random.randint(0, N) if x is None else int(x),
        "y": np.random.randint(0, N) if y is None else int(y),
        "w": np.random.dirichlet(np.ones(3)),
        "energy": 1.0,
    }

agents = [new_agent() for _ in range(40)]


# --- narzędzia ---
def laplacian(M):
    return (
        np.roll(M, 1, 0) + np.roll(M, -1, 0) +
        np.roll(M, 1, 1) + np.roll(M, -1, 1) - 4 * M
    )


def step(R, G, B, agents, Trail):
    # aktualizacja pól
    for M, a in zip([R, G, B], [alpha_R, alpha_G, alpha_B]):
        lap = laplacian(M)
        M += a * lap + beta * (np.random.rand(*M.shape) - 0.5) + gamma * np.random.randn(*M.shape)
        np.clip(M, 0, 1, out=M)

    new_agents = []
    for ag in agents:
        x, y = ag["x"], ag["y"]

        # lokalny gradient każdego pola
        grad_Rx = R[(x+1)%N, y] - R[(x-1)%N, y]
        grad_Ry = R[x, (y+1)%N] - R[x, (y-1)%N]
        grad_Gx = G[(x+1)%N, y] - G[(x-1)%N, y]
        grad_Gy = G[x, (y+1)%N] - G[x, (y-1)%N]
        grad_Bx = B[(x+1)%N, y] - B[(x-1)%N, y]
        grad_By = B[x, (y+1)%N] - B[x, (y-1)%N]

        dx = ag["w"][0]*grad_Rx + ag["w"][1]*grad_Gx + ag["w"][2]*grad_Bx
        dy = ag["w"][0]*grad_Ry + ag["w"][1]*grad_Gy + ag["w"][2]*grad_By
        norm = np.hypot(dx, dy) + 1e-6
        dx, dy = (dx/norm, dy/norm)

        # aktualizacja pozycji
        ag["x"] = int((x + agent_speed*dx) % N)
        ag["y"] = int((y + agent_speed*dy) % N)
        Trail[ag["x"], ag["y"]] = 1.0

        # aktualizacja energii
        local_val = ag["w"][0]*R[ag["x"], ag["y"]] + ag["w"][1]*G[ag["x"], ag["y"]] + ag["w"][2]*B[ag["x"], ag["y"]]
        ag["energy"] += energy_gain * local_val - energy_loss
        ag["energy"] = np.clip(ag["energy"], 0, 2.0)

        # replikacja
        if ag["energy"] > replicate_threshold:
            child = {
                "x": (ag["x"] + np.random.randint(-1, 2)) % N,
                "y": (ag["y"] + np.random.randint(-1, 2)) % N,
                "w": np.clip(ag["w"] + np.random.randn(3)*0.05, 0, None),
                "energy": ag["energy"]/2,
            }
            child["w"] /= np.sum(child["w"])
            ag["energy"] /= 2
            new_agents.append(child)

        # śmierć
        if ag["energy"] > death_threshold:
            new_agents.append(ag)
        # jeśli energia < threshold → agent znika

    Trail *= trail_decay
    return R, G, B, new_agents, Trail


# --- wizualizacja RGB ---
fig, ax = plt.subplots()
img = np.zeros((N, N, 3))
im = ax.imshow(img, vmin=0, vmax=1)
ax.set_title("ethical_field_rgb_agents_B")

def update(frame):
    global R, G, B, agents, Trail
    if not paused:
        R, G, B, agents, Trail = step(R, G, B, agents, Trail)
    img[..., 0] = R
    img[..., 1] = G
    img[..., 2] = B
    overlay = np.clip(img + Trail[..., None]*0.5, 0, 1)
    im.set_array(overlay)
    ax.set_title(f"agents: {len(agents)}")
    return [im]

def on_click(event):
    if event.inaxes == ax:
        agents.append(new_agent(event.ydata, event.xdata))

def on_key(event):
    global paused
    if event.key == " ":
        paused = not paused

fig.canvas.mpl_connect("button_press_event", on_click)
fig.canvas.mpl_connect("key_press_event", on_key)

ani = animation.FuncAnimation(fig, update, frames=steps, interval=40, blit=True)
plt.axis("off")
plt.show()
