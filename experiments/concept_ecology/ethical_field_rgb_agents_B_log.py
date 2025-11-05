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
N = 200
steps = 800
alpha_R, alpha_G, alpha_B = 0.178, 0.184, 0.187
beta = 0.212
gamma = 0.007
agent_speed = 0.01
trail_decay = 0.99

energy_gain = 0.035
energy_loss = 0.008
replicate_threshold = 1.1
death_threshold = 0.5

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
    # --- losowa kolejność aktualizacji pól (eliminuje bias fazy) ---
    fields = [(R, alpha_R), (G, alpha_G), (B, alpha_B)]
    np.random.shuffle(fields)
    R, G, B = [f[0] for f in fields]
    alphas = [f[1] for f in fields]

    # --- symetryczna aktualizacja pól ---
    for M, a in zip([R, G, B], alphas):
        lap = (
            np.roll(M, 1, 0) + np.roll(M, -1, 0) +
            np.roll(M, 1, 1) + np.roll(M, -1, 1) - 4 * M
        )
        # losowa fluktuacja w pełni symetryczna
        noise = gamma * (np.random.randn(*M.shape) + np.random.randn(*M.shape).T) * 0.5
        M += a * lap + beta * (np.random.rand(*M.shape) - 0.5) + noise
        np.clip(M, 0, 1, out=M)

    # --- ruch agentów ---
    new_agents = []
    for ag in agents:
        x, y = ag["x"], ag["y"]

        # lokalne gradienty (centralne, symetryczne)
        def grad(M):
            gx = (M[(x+1)%N, y] - M[(x-1)%N, y]) * 0.5
            gy = (M[x, (y+1)%N] - M[x, (y-1)%N]) * 0.5
            return gx, gy

        gR, gG, gB = grad(R), grad(G), grad(B)

        # kierunek: rotacja losowa zamiast szumu niezależnego
        theta = np.random.uniform(0, 2*np.pi)
        rot = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])

        v = np.array([
            ag["w"][0]*gR[0] + ag["w"][1]*gG[0] + ag["w"][2]*gB[0],
            ag["w"][0]*gR[1] + ag["w"][1]*gG[1] + ag["w"][2]*gB[1]
        ])
        v = rot @ v
        norm = np.hypot(v[0], v[1]) + 1e-9
        dx, dy = (v / norm)

        ag["x"] = int((x + agent_speed*dx) % N)
        ag["y"] = int((y + agent_speed*dy) % N)
        Trail[ag["x"], ag["y"]] = 1.0

        # energia jak wcześniej
        local_val = ag["w"][0]*R[ag["x"], ag["y"]] + ag["w"][1]*G[ag["x"], ag["y"]] + ag["w"][2]*B[ag["x"], ag["y"]]
        ag["energy"] += energy_gain * local_val - energy_loss
        ag["energy"] = np.clip(ag["energy"], 0, 2.0)

        # replikacja i śmierć jak dotąd
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

    # logowanie jak wcześniej ...
    if t % log_interval == 0:
        with open(log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                t, len(new_agents),
                np.mean([a["energy"] for a in new_agents]) if new_agents else 0,
                np.mean(R), np.mean(G), np.mean(B)
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

ani = animation.FuncAnimation(fig, update, frames=steps, interval=40, blit=False)
plt.axis("off")
plt.show()
