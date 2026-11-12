"""Turbulencia: espectro de Kolmogorov (1941) y cascada multifractal (modelo p de Meneveau y Sreenivasan, 1987).

- `senal_k41`: señal de velocidad sintética con espectro E(k) ∝ k^(−5/3) (fases al azar); no es un flujo resuelto,
  es un banco de pruebas para comprobar que el estimador de pendiente funciona.
- `cascada_p`: medida de disipación construida repartiendo la energía en mitades con pesos p y 1 − p.
- `zeta_p_modelo`: exponentes de las funciones de estructura ζ_p = 1 − log2(p^(p/3) + (1 − p)^(p/3)) frente a p/3 (K41).
"""
from __future__ import annotations

import numpy as np

from .dimension import ajuste_loglog


def senal_k41(n: int = 2 ** 16, pendiente: float = -5 / 3, semilla: int = 31) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    k = np.fft.rfftfreq(n, d=1.0)
    amp = np.zeros_like(k)
    amp[1:] = k[1:] ** (pendiente / 2)
    fase = np.exp(2j * np.pi * rng.random(len(k)))
    u = np.fft.irfft(amp * fase, n)
    return u / u.std()


def espectro(u) -> tuple[np.ndarray, np.ndarray]:
    """Espectro de energía 1D: |û(k)|² promediado en bandas logarítmicas."""
    n = len(u)
    E = np.abs(np.fft.rfft(u)) ** 2 / n
    k = np.fft.rfftfreq(n)
    bordes = np.geomspace(k[1], k[-1], 40)
    kc, Ec = [], []
    for a, b in zip(bordes[:-1], bordes[1:]):
        m = (k >= a) & (k < b)
        if m.any():
            kc.append(k[m].mean()); Ec.append(E[m].mean())
    return np.array(kc), np.array(Ec)


def pendiente_espectro(u, k_min=1e-3, k_max=1e-1) -> dict:
    k, E = espectro(u)
    m = (k >= k_min) & (k <= k_max)
    aj = ajuste_loglog(k[m], E[m])
    return {"pendiente": aj["pendiente"], "r2": aj["r2"]}


def cascada_p(niveles: int = 16, p: float = 0.7, semilla: int = 32) -> np.ndarray:
    """Medida de la cascada: en cada nivel cada intervalo reparte su masa en dos mitades con p y 1 − p
    (el lado que recibe p se elige al azar). Devuelve 2^niveles masas que suman 1."""
    rng = np.random.default_rng(semilla)
    m = np.array([1.0])
    for _ in range(niveles):
        izq = rng.random(len(m)) < 0.5
        a = np.where(izq, p, 1 - p)
        m = np.column_stack([m * a, m * (1 - a)]).ravel()
    return m


def tau_q(medida, qs, niveles_ajuste=range(3, 13)) -> dict:
    """Exponentes de masa τ(q): Σ μ_i(ε)^q ∝ ε^τ(q) con cajas ε = 2^−j. Dimensiones generalizadas D_q = τ(q)/(q − 1)."""
    mu = np.asarray(medida, float)
    n_tot = int(np.log2(len(mu)))
    out = {}
    for q in qs:
        eps, Z = [], []
        for j in niveles_ajuste:
            caja = mu.reshape(2 ** j, 2 ** (n_tot - j)).sum(1)
            caja = caja[caja > 0]
            eps.append(2.0 ** -j); Z.append(float((caja ** q).sum()))
        out[q] = ajuste_loglog(eps, Z)["pendiente"]
    return out


def dq_teorico(q: float, p: float) -> float:
    """D_q del modelo p: log2(p^q + (1 − p)^q) / (1 − q); para q = 1, la entropía en bits."""
    if abs(q - 1) < 1e-12:
        return float(-(p * np.log2(p) + (1 - p) * np.log2(1 - p)))
    return float(np.log2(p ** q + (1 - p) ** q) / (1 - q))


def zeta_p_modelo(orden: float, p: float = 0.7) -> float:
    return float(1 - np.log2(p ** (orden / 3) + (1 - p) ** (orden / 3)))


def funcion_estructura(u, ordenes, separaciones) -> dict:
    """S_p(r) = ⟨|u(x + r) − u(x)|^p⟩ y su pendiente ζ_p en log-log."""
    out = {}
    for p in ordenes:
        S = [float(np.mean(np.abs(u[r:] - u[:-r]) ** p)) for r in separaciones]
        out[p] = ajuste_loglog(separaciones, S)["pendiente"]
    return out
