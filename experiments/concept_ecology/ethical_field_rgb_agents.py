"""
ethical_field_rgb_agents.py
----------------------------
Etap A: trzy pola (R,G,B) + agenci podążający za gradientami.
Bez replikacji i zanikania, tylko ruch i lokalne sprzężenie z polami.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

# --- konfiguracja ---
N = 80
agents_n = 40
steps = 400
alpha_R, alpha_G, alpha_B = 0.22, 0.25, 0.28  # dyfuzja dla R,G,B
beta = 0.05   # coupling między polem a lokalną aktywnością
gamma = 0.01  # szum
agent_speed = 1.0
trail_decay = 0.95

# --- pola ---
R = np.random.rand(N, N) * 0.5
G = np.random.rand(N, N) * 0.5
B = np.random.rand(N, N) * 0.5
Trail = np.zeros((N, N))  # ślady agentów

# --- agenci ---
agents = []
for _ in range(agents_n):
    agents.append({
        "x": np.random.randint(0, N),
        "y": np.random.randint(0, N),
        # preferencje dla pól (R,G,B)
        "w": np.random.dirichlet(np.ones(3)),
    })


def laplacian(M):
    return (
        np.roll(M, 1, 0) + np.roll(M, -1, 0) +
        np.roll(M, 1, 1) + np.roll(M, -1, 1) - 4 * M
    )


def step(R, G, B, agents, Trail):
    # dyfuzja i sprzężenie
    for M, a in zip([R, G, B], [alpha_R, alpha_G, alpha_B]):
        lap = laplacian(M)
        M += a * lap + beta * (np.random.rand(*M.shape) - 0.5) + gamma * np.random.randn(*M.shape)
        np.clip(M, 0, 1, out=M)

    # ruch agentów
    for ag in agents:
        x, y = ag["x"], ag["y"]
        # lokalny gradient dla każdego pola
        grad_Rx = R[(x+1)%N, y] - R[(x-1)%N, y]
        grad_Ry = R[x, (y+1)%N] - R[x, (y-1)%N]
        grad_Gx = G[(x+1)%N, y] - G[(x-1)%N, y]
        grad_Gy = G[x, (y+1)%N] - G[x, (y-1)%N]
        grad_Bx = B[(x+1)%N, y] - B[(x-1)%N, y]
        grad_By = B[x, (y+1)%N] - B[x, (y-1)%N]

        # wektor kierunku = kombinacja wag * gradientów
        dx = ag["w"][0]*grad_Rx + ag["w"][1]*grad_Gx + ag["w"][2]*grad_Bx
        dy = ag["w"][0]*grad_Ry + ag["w"][1]*grad_Gy + ag["w"][2]*grad_By
        norm = np.hypot(dx, dy) + 1e-6
        dx, dy = (dx/norm, dy/norm)

        # aktualizacja pozycji
        ag["x"] = int((x + agent_speed*dx) % N)
        ag["y"] = int((y + agent_speed*dy) % N)
        Trail[ag["x"], ag["y"]] = 1.0

    # zanikanie śladów
    Trail *= trail_decay
    return R, G, B, agents, Trail


# --- wizualizacja RGB ---
fig, ax = plt.subplots()
img = np.zeros((N, N, 3))
im = ax.imshow(img, vmin=0, vmax=1)
ax.set_title("ethical_field_rgb_agents")

def update(frame):
    global R, G, B, agents, Trail
    R, G, B, agents, Trail = step(R, G, B, agents, Trail)
    img[..., 0] = R
    img[..., 1] = G
    img[..., 2] = B
    # nałożyć ślady (jaśniejsze tam, gdzie agenci byli często)
    overlay = np.clip(img + Trail[..., None]*0.5, 0, 1)
    im.set_array(overlay)
    return [im]

ani = animation.FuncAnimation(fig, update, frames=steps, interval=40, blit=True)
plt.axis("off")
plt.show()
