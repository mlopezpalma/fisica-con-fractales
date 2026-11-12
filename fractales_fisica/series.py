"""Exponente de Hurst de una serie temporal: rango reescalado (R/S, Hurst 1951) y análisis de fluctuaciones sin
tendencia (DFA, Peng y otros 1994). Los dos estimadores tienen sesgo en series cortas: compárelos siempre con series
sintéticas de H conocido antes de interpretar una serie real."""
from __future__ import annotations

import numpy as np

from .dimension import ajuste_loglog


def _ventanas(n: int, n_min: int = 16, n_ventanas: int = 12) -> np.ndarray:
    return np.unique(np.geomspace(n_min, n // 4, n_ventanas).astype(int))


def hurst_rs(serie, tamanos=None) -> dict:
    """Pendiente de log(R/S) frente a log n, con R/S promediado en ventanas disjuntas de tamaño n."""
    x = np.asarray(serie, float)
    tamanos = _ventanas(len(x)) if tamanos is None else np.asarray(tamanos)
    rs = []
    for n in tamanos:
        m = len(x) // n
        b = x[: m * n].reshape(m, n)
        y = np.cumsum(b - b.mean(1, keepdims=True), axis=1)
        R = y.max(1) - y.min(1)
        S = b.std(1)
        ok = S > 0
        rs.append(float((R[ok] / S[ok]).mean()))
    aj = ajuste_loglog(tamanos, rs)
    return {"H": aj["pendiente"], "r2": aj["r2"], "tamanos": tamanos.tolist(), "rs": rs}


def dfa(serie, tamanos=None) -> dict:
    """DFA de orden 1: perfil acumulado, recta de tendencia en cada ventana y fluctuación F(n) ∝ n^α.
    Para ruido gaussiano fraccionario, α = H."""
    x = np.asarray(serie, float)
    perfil = np.cumsum(x - x.mean())
    tamanos = _ventanas(len(x)) if tamanos is None else np.asarray(tamanos)
    F = []
    for n in tamanos:
        m = len(perfil) // n
        b = perfil[: m * n].reshape(m, n)
        t = np.arange(n)
        a1, a0 = np.polyfit(t, b.T, 1)
        tendencia = a1[None, :] * t[:, None] + a0[None, :]
        F.append(float(np.sqrt(((b.T - tendencia) ** 2).mean())))
    aj = ajuste_loglog(tamanos, F)
    return {"alfa": aj["pendiente"], "r2": aj["r2"], "tamanos": tamanos.tolist(), "F": F}


def rendimientos_garch(n: int, semilla: int = 8, omega=1e-6, a=0.08, b=0.9) -> np.ndarray:
    """Serie sintética de rendimientos GARCH(1,1): sin memoria en el signo, pero con agrupamiento de volatilidad.
    Sirve para enseñar que H ≈ 0,5 en los rendimientos no excluye memoria en |rendimientos|."""
    rng = np.random.default_rng(semilla)
    r = np.empty(n)
    s2 = omega / (1 - a - b)
    for k in range(n):
        r[k] = np.sqrt(s2) * rng.standard_normal()
        s2 = omega + a * r[k] ** 2 + b * s2
    return r
