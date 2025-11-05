"""
analyze_field_log.py
--------------------
Odczytuje i wizualizuje dane z ethical_field_log.csv.
Wykresy: liczba agentów, średnia energia, średnie wartości pól R,G,B.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

LOG_PATH = "ethical_field_log.csv"

if not os.path.exists(LOG_PATH):
    print("Brak pliku logu:", LOG_PATH)
    exit()

df = pd.read_csv(LOG_PATH)

# podstawowe informacje
print(df.head(), "\n")
print(f"Zarejestrowano {len(df)} wpisów (od kroku {df.step.min()} do {df.step.max()})")

# --- wykres 1: liczba agentów i średnia energia ---
fig1, ax1 = plt.subplots()
ax1.plot(df.step, df.n_agents, label="Liczba agentów", linewidth=1.8)
ax1.set_xlabel("Krok symulacji")
ax1.set_ylabel("Liczba agentów", color="C0")
ax1.tick_params(axis="y", labelcolor="C0")

ax2 = ax1.twinx()
ax2.plot(df.step, df.mean_energy, color="C3", label="Śr. energia", linewidth=1.3, alpha=0.7)
ax2.set_ylabel("Średnia energia", color="C3")
ax2.tick_params(axis="y", labelcolor="C3")
plt.title("Dynamika populacji i energii w czasie")
plt.tight_layout()
plt.show()

# --- wykres 2: średnie wartości pól ---
fig2, ax = plt.subplots()
ax.plot(df.step, df.mean_R, color="r", label="R (zasoby)")
ax.plot(df.step, df.mean_G, color="g", label="G (przeżywalność)")
ax.plot(df.step, df.mean_B, color="b", label="B (wolność)")
ax.set_xlabel("Krok symulacji")
ax.set_ylabel("Średnie wartości pól")
ax.legend()
plt.title("Ewolucja pól R,G,B w czasie")
plt.tight_layout()
plt.show()

# --- wykres 3: korelacje między polami ---
fig3, ax = plt.subplots()
df[["mean_R","mean_G","mean_B"]].plot(kind="scatter",
                                      x="mean_R", y="mean_G",
                                      c=df["mean_B"], cmap="coolwarm", ax=ax)
ax.set_xlabel("R (zasoby)")
ax.set_ylabel("G (przeżywalność)")
plt.title("Korelacja R–G, kolor = B (wolność)")
plt.tight_layout()
plt.show()
