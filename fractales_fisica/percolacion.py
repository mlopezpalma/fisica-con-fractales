"""Percolación por sitios en red cuadrada: probabilidad de cruce, umbral estimado y dimensión fractal del cúmulo
más grande en el umbral (M ∝ L^D)."""
from __future__ import annotations

import numpy as np

from .dimension import ajuste_loglog


def red(L: int, p: float, rng) -> np.ndarray:
    return rng.random((L, L)) < p


def cumulos(ocupada) -> tuple[np.ndarray, int]:
    """Etiqueta los cúmulos con vecindad de 4 (arriba, abajo, izquierda, derecha). Devuelve etiquetas 1..n (0 = vacío)
    y el número de cúmulos. Componentes conexas por propagación del mínimo con saltos de puntero (solo NumPy)."""
    a = np.asarray(ocupada, bool)
    h, w = a.shape
    idx = np.arange(h * w).reshape(h, w)
    pares = [(idx[:, :-1][a[:, :-1] & a[:, 1:]], idx[:, 1:][a[:, :-1] & a[:, 1:]]),
             (idx[:-1, :][a[:-1, :] & a[1:, :]], idx[1:, :][a[:-1, :] & a[1:, :]])]
    ea = np.concatenate([p[0] for p in pares])
    eb = np.concatenate([p[1] for p in pares])
    lab = np.arange(h * w)
    while True:
        la, lb = lab[ea], lab[eb]
        if np.array_equal(la, lb):
            break
        m = np.minimum(la, lb)
        np.minimum.at(lab, la, m)
        np.minimum.at(lab, lb, m)
        while True:
            nuevo = lab[lab]
            if np.array_equal(nuevo, lab):
                break
            lab = nuevo
    lab = lab.reshape(h, w)
    raices = np.unique(lab[a])
    out = np.zeros((h, w), int)
    out[a] = np.searchsorted(raices, lab[a]) + 1
    return out, len(raices)


def cruza(ocupada) -> bool:
    """¿Hay un cúmulo que une la fila de arriba con la de abajo?"""
    etiquetas, _ = cumulos(ocupada)
    arriba = set(np.unique(etiquetas[0])) - {0}
    abajo = set(np.unique(etiquetas[-1])) - {0}
    return bool(arriba & abajo)


def prob_cruce(L: int, ps, n_muestras: int = 200, semilla: int = 21) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    return np.array([np.mean([cruza(red(L, p, rng)) for _ in range(n_muestras)]) for p in ps])


def umbral_por_cruce(L: int, ps, n_muestras: int = 200, semilla: int = 21) -> dict:
    """p en el que la probabilidad de cruce vale 1/2 (interpolación lineal entre los dos puntos que la rodean)."""
    P = prob_cruce(L, ps, n_muestras, semilla)
    k = int(np.nonzero(P >= 0.5)[0][0])
    p0, p1, P0, P1 = ps[k - 1], ps[k], P[k - 1], P[k]
    return {"pc": float(p0 + (0.5 - P0) * (p1 - p0) / (P1 - P0)), "P": P.tolist()}


def masa_cumulo_mayor(L: int, p: float, n_muestras: int = 40, semilla: int = 22) -> float:
    """Tamaño medio del cúmulo más grande (número de sitios)."""
    rng = np.random.default_rng(semilla)
    m = []
    for _ in range(n_muestras):
        et, n = cumulos(red(L, p, rng))
        m.append(np.bincount(et.ravel())[1:].max() if n else 0)
    return float(np.mean(m))


def dimension_cumulo(Ls, p: float, n_muestras: int = 40, semilla: int = 22) -> dict:
    """D del ajuste M(L) ∝ L^D en el umbral."""
    M = [masa_cumulo_mayor(L, p, n_muestras, semilla + i) for i, L in enumerate(Ls)]
    aj = ajuste_loglog(Ls, M)
    return {"D": aj["pendiente"], "r2": aj["r2"], "L": list(Ls), "M": M}


def fuerza_cumulo_infinito(L: int, ps, n_muestras: int = 20, semilla: int = 23) -> np.ndarray:
    """Fracción de sitios de la red que pertenecen al cúmulo más grande (aproxima P∞ por encima del umbral)."""
    return np.array([masa_cumulo_mayor(L, p, n_muestras, semilla) / L ** 2 for p in ps])
