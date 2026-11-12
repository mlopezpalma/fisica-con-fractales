"""Procesos aleatorios con geometría fractal: caminata aleatoria (movimiento browniano discreto), vuelos de Lévy,
caminata de tiempo continuo con esperas de cola pesada (subdifusión) y ruido gaussiano fraccionario (fGn/fBm)."""
from __future__ import annotations

import numpy as np

from .dimension import ajuste_loglog


def caminata(n: int, semilla: int = 1, dim: int = 2) -> np.ndarray:
    """Caminata aleatoria en red cuadrada (o cúbica): n pasos de longitud 1 en una dirección de eje al azar."""
    rng = np.random.default_rng(semilla)
    eje = rng.integers(0, dim, n)
    signo = rng.choice([-1, 1], n)
    pasos = np.zeros((n, dim), int)
    pasos[np.arange(n), eje] = signo
    return np.vstack([np.zeros((1, dim), int), np.cumsum(pasos, axis=0)])


def msd_conjunto(n_caminantes: int, n_pasos: int, semilla: int = 2) -> tuple[np.ndarray, np.ndarray]:
    """Desplazamiento cuadrático medio ⟨r²(t)⟩ promediado sobre caminantes independientes en 2D."""
    rng = np.random.default_rng(semilla)
    ang = rng.integers(0, 4, (n_caminantes, n_pasos))
    dx = np.choose(ang, [1, -1, 0, 0])
    dy = np.choose(ang, [0, 0, 1, -1])
    x, y = np.cumsum(dx, 1), np.cumsum(dy, 1)
    r2 = (x ** 2 + y ** 2).mean(0)
    t = np.arange(1, n_pasos + 1)
    return t, r2


def exponente_msd(t, msd, t_min=None, t_max=None) -> dict:
    """Ajusta ⟨r²⟩ ∝ t^α entre t_min y t_max (por defecto, todo el rango)."""
    t, msd = np.asarray(t, float), np.asarray(msd, float)
    m = np.ones(len(t), bool)
    if t_min is not None:
        m &= t >= t_min
    if t_max is not None:
        m &= t <= t_max
    aj = ajuste_loglog(t[m], msd[m])
    return {"alfa": aj["pendiente"], "r2": aj["r2"]}


def vuelo_levy(n: int, mu: float, semilla: int = 4, l0: float = 1.0) -> np.ndarray:
    """Vuelo de Lévy en 2D: saltos de longitud con cola de Pareto P(l > x) = (x/l0)^−μ y dirección uniforme."""
    rng = np.random.default_rng(semilla)
    u = rng.random(n)
    l = l0 * u ** (-1.0 / mu)
    th = rng.random(n) * 2 * np.pi
    pasos = np.column_stack([l * np.cos(th), l * np.sin(th)])
    return np.vstack([[0.0, 0.0], np.cumsum(pasos, axis=0)])


def fraccion_salto_mayor(n: int, mu: float, semilla: int = 4) -> float:
    """Fracción de la distancia total recorrida que aporta el salto más largo."""
    rng = np.random.default_rng(semilla)
    l = rng.random(n) ** (-1.0 / mu)
    return float(l.max() / l.sum())


def ctrw_msd(n_caminantes: int, t_max: float, alfa: float, semilla: int = 5, n_t: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """Caminata de tiempo continuo (Montroll y Weiss) en 1D: saltos ±1 tras esperas con cola P(τ > t) = t^−α (τ ≥ 1).
    Para α < 1 la espera media es infinita y ⟨x²(t)⟩ ∝ t^α (subdifusión)."""
    rng = np.random.default_rng(semilla)
    tiempos = np.geomspace(10, t_max, n_t)
    msd = np.zeros(n_t)
    for _ in range(n_caminantes):
        t, x, k = 0.0, 0, 0
        pos = np.zeros(n_t)
        while k < n_t:
            t += rng.random() ** (-1.0 / alfa)
            while k < n_t and tiempos[k] < t:
                pos[k] = x
                k += 1
            x += 1 if rng.random() < 0.5 else -1
        msd += pos ** 2
    return tiempos, msd / n_caminantes


# ------------------------------------------------------------------ ruido gaussiano fraccionario
def fgn(n: int, hurst: float, semilla: int = 6) -> np.ndarray:
    """Ruido gaussiano fraccionario de varianza 1 (método exacto de Davies y Harte, 1987, por incrustación circulante)."""
    if not 0 < hurst < 1:
        raise ValueError("H debe estar en (0, 1)")
    k = np.arange(n + 1)
    g = 0.5 * (np.abs(k + 1) ** (2 * hurst) - 2 * np.abs(k) ** (2 * hurst) + np.abs(k - 1) ** (2 * hurst))
    fila = np.concatenate([g, g[-2:0:-1]])
    lam = np.fft.fft(fila).real
    if lam.min() < -1e-9:
        raise ArithmeticError("autovalores negativos: la incrustación circulante falla")
    lam = np.clip(lam, 0, None)
    m = len(fila)
    rng = np.random.default_rng(semilla)
    w = rng.standard_normal(m) + 1j * rng.standard_normal(m)
    x = np.fft.fft(np.sqrt(lam / m) * w)
    return x.real[:n]


def fbm(n: int, hurst: float, semilla: int = 6) -> np.ndarray:
    """Movimiento browniano fraccionario: suma acumulada del fGn, empezando en 0."""
    return np.concatenate([[0.0], np.cumsum(fgn(n, hurst, semilla))])


def escala_levy(n_caminantes: int, n_pasos: int, mu: float, semilla: int = 7) -> dict:
    """Mediana de la distancia al origen de un vuelo de Lévy tras t saltos. Para 0 < μ < 2 crece como t^(1/μ)
    (superdifusión); el desplazamiento cuadrático medio no sirve porque la varianza del salto es infinita."""
    rng = np.random.default_rng(semilla)
    l = rng.random((n_caminantes, n_pasos)) ** (-1.0 / mu)
    th = rng.random((n_caminantes, n_pasos)) * 2 * np.pi
    x, y = np.cumsum(l * np.cos(th), 1), np.cumsum(l * np.sin(th), 1)
    med = np.median(np.hypot(x, y), axis=0)
    t = np.arange(1, n_pasos + 1)
    m = t >= 10
    aj = ajuste_loglog(t[m], med[m])
    return {"exponente": aj["pendiente"], "r2": aj["r2"], "t": t, "mediana": med}
