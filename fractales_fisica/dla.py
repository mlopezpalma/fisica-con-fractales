"""Agregación limitada por difusión (DLA, Witten y Sander 1981) en red cuadrada.

Cada partícula nace en un círculo alrededor del agregado, camina al azar y se queda pegada al tocar un vecino
ocupado. Si se aleja demasiado se elimina y nace otra. Lejos del agregado da saltos grandes (un círculo vacío
permite saltar a su borde sin cambiar la estadística), lo que acelera mucho la simulación.
"""
from __future__ import annotations

import math

import numpy as np


def dla(n_particulas: int = 3000, semilla: int = 11, lado: int = 801) -> np.ndarray:
    """Devuelve una imagen binaria lado × lado con el agregado (semilla en el centro)."""
    rng = np.random.default_rng(semilla)
    g = np.zeros((lado, lado), bool)
    c = lado // 2
    g[c, c] = True
    r_max = 1.0
    movs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    pegadas = 1
    while pegadas < n_particulas:
        r_nac = r_max + 5
        r_muerte = min(3 * r_nac + 20, c - 2)
        a = rng.random() * 2 * math.pi
        x, y = c + int(round(r_nac * math.cos(a))), c + int(round(r_nac * math.sin(a)))
        while True:
            d = math.hypot(x - c, y - c)
            if d > r_muerte:
                break
            if d > r_max + 3:      # salto largo al borde del círculo libre
                s = d - r_max - 2
                a = rng.random() * 2 * math.pi
                x, y = int(round(x + s * math.cos(a))), int(round(y + s * math.sin(a)))
                continue
            if g[x + 1, y] or g[x - 1, y] or g[x, y + 1] or g[x, y - 1]:
                g[x, y] = True
                pegadas += 1
                r_max = max(r_max, d)
                break
            mx, my = movs[int(rng.integers(4))]
            x, y = x + mx, y + my
    return g


def radio_de_giro(g) -> float:
    ys, xs = np.nonzero(g)
    return float(np.sqrt(((ys - ys.mean()) ** 2 + (xs - xs.mean()) ** 2).mean()))
