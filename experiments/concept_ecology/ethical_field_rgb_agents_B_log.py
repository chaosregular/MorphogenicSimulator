"""
ethical_field_rgb_agents_B_log.py
----------------------------------
Etap B z poprawioną symetrią gradientów i loggerem CSV.
Kliknięcie = nowy agent. Spacja = pauza/wznowienie.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import csv
import os

# --- konfiguracja ---
N = 80
steps = 800
alpha_R, alpha_G, alpha_B = 0.205, 0.201, 0.158
beta = 0.05
gamma = 0.015
agent_speed = 1.0
trail_decay = 0.95

energy_gain = 0.045
energy_loss = 0.012
replicate_threshold = 1.4
death_threshold = 0.15

paused = False

log_interval = 10
log_file = "ethical_field_log.csv"

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

# --- logger ---
if os.path.exists(log_file):
    os.remove(log_file)
with open(log_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["step", "n_agents", "mean_energy", "mean_R", "mean_G", "mean_B"])

# --- funkcje pomocnicze ---
def laplacian(M):
    return (
        np.roll(M, 1, 0) + np.roll(M, -1, 0) +
        np.roll(M, 1, 1) + np.roll(M, -1, 1) - 4 * M
    )

def local_gradient(M, x, y):
    """symetryczny gradient centralny"""
    gx = (M[(x+1)%N, y] - M[(x-1)%N, y]) * 0.5
    gy = (M[x, (y+1)%N] - M[x, (y-1)%N]) * 0.5
    return gx, gy

def step(R, G, B, agents, Trail, t):
    # aktualizacja pól
    for M, a in zip([R, G, B], [alpha_R, alpha_G, alpha_B]):
        lap = laplacian(M)
        M += a * lap + beta * (np.random.rand(*M.shape) - 0.5) + gamma * np.random.randn(*M.shape)
        np.clip(M, 0, 1, out=M)

    new_agents = []
    for ag in agents:
        x, y = ag["x"], ag["y"]

        # lokalne gradienty
        grad_Rx, grad_Ry = local_gradient(R, x, y)
        grad_Gx, grad_Gy = local_gradient(G, x, y)
        grad_Bx, grad_By = local_gradient(B, x, y)

        # wektor ruchu wg wag
        dx = ag["w"][0]*grad_Rx + ag["w"][1]*grad_Gx + ag["w"][2]*grad_Bx
        dy = ag["w"][0]*grad_Ry + ag["w"][1]*grad_Gy + ag["w"][2]*grad_By
        norm = np.hypot(dx, dy) + 1e-9
        dx, dy = dx/norm, dy/norm

        # aktualizacja pozycji (dodano losowe odchylenie)
        ag["x"] = int((x + agent_speed*dx + np.random.randn()*0.3) % N)
        ag["y"] = int((y + agent_speed*dy + np.random.randn()*0.3) % N)
        Trail[ag["x"], ag["y"]] = 1.0

        # aktualizacja energii
        local_val = ag["w"][0]*R[ag["x"], ag["y"]] + ag["w"][1]*G[ag["x"], ag["y"]] + ag["w"][2]*B[ag["x"], ag["y"]]
        ag["energy"] += energy_gain * local_val - energy_loss
        ag["energy"] = np.clip(ag["energy"], 0, 2.0)

        # replikacja
        if ag["energy"] > replicate_threshold:
            child = new_agent(ag["x"] + np.random.randint(-1, 2),
                              ag["y"] + np.random.randint(-1, 2))
            child["w"] = np.clip(ag["w"] + np.random.randn(3)*0.05, 0, None)
            child["w"] /= np.sum(child["w"])
            child["energy"] = ag["energy"]/2
            ag["energy"] /= 2
            new_agents.append(child)

        if ag["energy"] > death_threshold:
            new_agents.append(ag)

    Trail *= trail_decay

    # zapis logu
    if t % log_interval == 0:
        with open(log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                t,
                len(new_agents),
                np.mean([a["energy"] for a in new_agents]) if new_agents else 0,
                np.mean(R),
                np.mean(G),
                np.mean(B)
            ])
    return R, G, B, new_agents, Trail


# --- wizualizacja ---
fig, ax = plt.subplots()
img = np.zeros((N, N, 3))
im = ax.imshow(img, vmin=0, vmax=1)
ax.set_title("ethical_field_rgb_agents_B (log)")

def update(frame):
    global R, G, B, agents, Trail
    if not paused:
        R, G, B, agents, Trail = step(R, G, B, agents, Trail, frame)
    img[..., 0], img[..., 1], img[..., 2] = R, G, B
    overlay = np.clip(img + Trail[..., None]*0.5, 0, 1)
    im.set_array(overlay)
    ax.set_title(f"t={frame}  agents={len(agents)}")
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
