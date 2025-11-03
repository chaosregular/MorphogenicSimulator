import numpy as np
import matplotlib.pyplot as plt

# size and steps
N, steps = 100, 200
E = np.random.rand(N, N) * 0.2         # initial ethical field
S = np.random.rand(N, N)               # conceptual activity

alpha = 0.2   # diffusion rate
beta  = 0.05  # harmonic coupling
gamma = 0.01  # spontaneous noise

def step(E, S):
    # Laplacian diffusion of E
    lap = (
        np.roll(E, 1, 0) + np.roll(E, -1, 0) +
        np.roll(E, 1, 1) + np.roll(E, -1, 1) - 4 * E
    )
    # Update ethical field with diffusion + harmonic coupling
    dE = alpha * lap + beta * (S - E) + gamma * np.random.randn(*E.shape)
    E_new = np.clip(E + dE, 0, 1)
    # Conceptual field slowly follows local ethics gradient
    S_new = np.clip(S + 0.1 * (E_new - S), 0, 1)
    return E_new, S_new

for t in range(steps):
    E, S = step(E, S)
    if t % 50 == 0:
        plt.imshow(E, cmap="inferno")
        plt.title(f"Ethical field t={t}")
        plt.axis("off")
        plt.show()
