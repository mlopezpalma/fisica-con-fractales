"""Dimensión fractal: semejanza, conteo de cajas (box-counting), masa-radio y regla de divisores (Richardson).

Todas las funciones devuelven números de Python o arrays de NumPy; ninguna dibuja.
"""
from __future__ import annotations

import math

import numpy as np


def dimension_semejanza(n_copias: int, razon: float) -> float:
    """Dimensión de semejanza D = log N / log(1/r) de un conjunto formado por N copias reducidas a escala r."""
    if not 0 < razon < 1 or n_copias < 1:
        raise ValueError("hace falta N ≥ 1 y 0 < r < 1")
    return math.log(n_copias) / math.log(1 / razon)


def ajuste_loglog(x, y) -> dict:
    """Recta de mínimos cuadrados de log y frente a log x. Devuelve pendiente, ordenada, R² y error típico de la pendiente."""
    lx, ly = np.log(np.asarray(x, float)), np.log(np.asarray(y, float))
    a, b = np.polyfit(lx, ly, 1)
    pred = a * lx + b
    ss_res = float(np.sum((ly - pred) ** 2))
    ss_tot = float(np.sum((ly - ly.mean()) ** 2)) or 1e-300
    n = len(lx)
    sxx = float(np.sum((lx - lx.mean()) ** 2)) or 1e-300
    err = float(np.sqrt(ss_res / (n - 2) / sxx)) if n > 2 else float("nan")
    return {"pendiente": float(a), "ordenada": float(b), "r2": 1 - ss_res / ss_tot, "error_pendiente": err}


def box_counting(img, tamanos=None) -> dict:
    """Dimensión de conteo de cajas de una imagen binaria (True = ocupado).

    Cubre la imagen con cajas de lado s píxeles, cuenta las que tocan algún píxel ocupado y ajusta
    log N(s) = −D log s + c. Devuelve D, R², los tamaños y los conteos.
    """
    a = np.asarray(img, bool)
    if a.ndim != 2 or not a.any():
        raise ValueError("hace falta una imagen 2D con algún píxel ocupado")
    lado = min(a.shape)
    if tamanos is None:
        tamanos = [2 ** k for k in range(1, int(math.log2(lado)) - 1)]
    conteos = []
    for s in tamanos:
        h, w = (a.shape[0] // s) * s, (a.shape[1] // s) * s
        b = a[:h, :w].reshape(h // s, s, w // s, s).any(axis=(1, 3))
        conteos.append(int(b.sum()))
    aj = ajuste_loglog(tamanos, conteos)
    return {"D": -aj["pendiente"], "r2": aj["r2"], "ordenada": aj["ordenada"], "tamanos": list(tamanos), "conteos": conteos}


def box_counting_puntos(xy, epsilons) -> dict:
    """Conteo de cajas sobre una nube de puntos (x, y): cajas de lado ε ocupadas por al menos un punto."""
    p = np.asarray(xy, float)
    p = p - p.min(axis=0)
    conteos = []
    for e in epsilons:
        celdas = np.floor(p / e).astype(np.int64)
        conteos.append(int(len(np.unique(celdas, axis=0))))
    aj = ajuste_loglog(epsilons, conteos)
    return {"D": -aj["pendiente"], "r2": aj["r2"], "epsilons": list(epsilons), "conteos": conteos}


def masa_radio(img, centro=None, radios=None) -> dict:
    """Dimensión de masa: M(R) = número de píxeles ocupados a distancia ≤ R del centro; M ∝ R^D."""
    a = np.asarray(img, bool)
    ys, xs = np.nonzero(a)
    if centro is None:
        centro = (a.shape[0] // 2, a.shape[1] // 2)
    d = np.hypot(ys - centro[0], xs - centro[1])
    rmax = d.max()
    if radios is None:
        radios = np.geomspace(3, rmax / 2, 10)
    masas = [int((d <= r).sum()) for r in radios]
    aj = ajuste_loglog(radios, masas)
    return {"D": aj["pendiente"], "r2": aj["r2"], "ordenada": aj["ordenada"], "radios": [float(r) for r in radios], "masas": masas}


def regla_divisores(curva, pasos) -> dict:
    """Método de Richardson: se recorre la curva con un compás de abertura δ y se mide L(δ) = n·δ.

    L(δ) ∝ δ^(1−D), así que D = 1 − pendiente del ajuste log L frente a log δ.
    """
    p = np.asarray(curva, float)
    longitudes = []
    for delta in pasos:
        n, i, actual = 0, 0, p[0]
        while True:
            d = np.hypot(*(p[i + 1:] - actual).T)
            fuera = np.nonzero(d >= delta)[0]
            if len(fuera) == 0:
                break
            i = i + 1 + int(fuera[0])
            actual = p[i]
            n += 1
        longitudes.append(n * delta)
    aj = ajuste_loglog(pasos, longitudes)
    return {"D": 1 - aj["pendiente"], "r2": aj["r2"], "ordenada": aj["ordenada"], "pasos": [float(x) for x in pasos], "longitudes": [float(x) for x in longitudes]}


def rasterizar(xy, n: int) -> np.ndarray:
    """Convierte una nube de puntos en una imagen binaria cuadrada de n × n píxeles (misma escala en x e y)."""
    p = np.asarray(xy, float)
    p = p - p.min(axis=0)
    esc = (n - 1) / max(p.max(), 1e-300)
    ij = np.round(p * esc).astype(int)
    img = np.zeros((n, n), bool)
    img[ij[:, 1], ij[:, 0]] = True
    return img
