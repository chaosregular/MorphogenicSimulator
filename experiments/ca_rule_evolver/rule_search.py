from ca_module import run_ca
import numpy as np

def evaluate(rule):
    grid = run_ca(rule, steps=200)
    # np.var(grid) → zróżnicowanie,
    # count domain edges, entropy → fitness
    return fitness

rules = [np.random.randint(0, 2, size=(24,), dtype=np.uint8) for _ in range(100)]
for generation in range(100):
    fitnesses = [evaluate(r) for r in rules]
    # select, mutate, crossover...
