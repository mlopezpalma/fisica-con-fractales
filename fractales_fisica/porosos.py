"""Medios porosos y rugosidad: porosidad de la alfombra de Sierpinski y la esponja de Menger, ley de Darcy,
flujo en una red porosa aleatoria (resuelto con gradiente conjugado, solo NumPy) y superficies rugosas
autoafines (movimiento browniano fraccionario 2D) con su dimensión D = 3 − H."""
from __future__ import annotations

import numpy as np

from .dimension import ajuste_loglog



def porosidad_alfombra(nivel: int) -> float:
    return 1 - (8 / 9) ** nivel


def porosidad_menger(nivel: int) -> float:
    return 1 - (20 / 27) ** nivel


def caudal_darcy(k_m2: float, area_m2: float, dp_pa: float, longitud_m: float, mu_pa_s: float) -> float:
    """Ley de Darcy: Q = k A ΔP / (μ L), en m³/s."""
    return k_m2 * area_m2 * dp_pa / (mu_pa_s * longitud_m)


def _laplaciano(p, abierto):
    """−Σ_vecinos (p_j − p_i) sobre poros abiertos, con conductancia 1 entre poros vecinos."""
    out = np.zeros_like(p)
    for eje, s in ((0, 1), (0, -1), (1, 1), (1, -1)):
        q = np.roll(p, s, axis=eje)
        m = np.roll(abierto, s, axis=eje)
        if eje == 0:
            if s == 1: m[0, :] = False
            else: m[-1, :] = False
        else:
            if s == 1: m[:, 0] = False
            else: m[:, -1] = False
        out += np.where(m & abierto, p - q, 0.0)
    return out


def permeabilidad_red(abierto, tol: float = 1e-10, max_iter: int = 20000) -> float:
    """Conductancia relativa de una red de poros (True = poro) con presión 1 a la izquierda y 0 a la derecha.

    Se resuelve la conservación del caudal (ley de Kirchhoff, equivalente discreto de ∇·(k∇p) = 0) por gradiente
    conjugado. Devuelve el caudal dividido entre el de la red sin sólido del mismo tamaño (1 = todo abierto)."""
    a = np.asarray(abierto, bool).copy()
    L = a.shape[1]
    fijo = np.zeros_like(a)
    fijo[:, 0] = fijo[:, -1] = True
    pb = np.zeros(a.shape)
    pb[:, 0] = 1.0
    pb = np.where(a, pb, 0.0)
    libre = a & ~fijo
    b = -np.where(libre, _laplaciano(pb, a), 0.0)
    x = np.zeros(a.shape)
    r = b.copy()
    d = r.copy()
    rr = float((r * r).sum())
    for _ in range(max_iter):
        if rr < tol ** 2:
            break
        Ad = np.where(libre, _laplaciano(np.where(libre, d, 0.0), a), 0.0)
        alfa = rr / float((d * Ad).sum())
        x += alfa * d
        r -= alfa * Ad
        rr_n = float((r * r).sum())
        d = r + (rr_n / rr) * d
        rr = rr_n
    p = np.where(libre, x, pb)
    caudal = float(np.where(a[:, 0] & a[:, 1], p[:, 0] - p[:, 1], 0.0).sum())
    return caudal / (a.shape[0] / (L - 1))


def permeabilidad_frente_porosidad(L: int, porosidades, n_muestras: int = 10, semilla: int = 41) -> np.ndarray:
    rng = np.random.default_rng(semilla)
    return np.array([np.mean([permeabilidad_red(rng.random((L, L)) < f) for _ in range(n_muestras)]) for f in porosidades])


def superficie_fbm(n: int, hurst: float, semilla: int = 42) -> np.ndarray:
    """Superficie autoafín por síntesis espectral: |ẑ(k)|² ∝ k^−(2H + 2), fases al azar. Altura con desviación 1."""
    rng = np.random.default_rng(semilla)
    kx = np.fft.fftfreq(n)[:, None]
    ky = np.fft.rfftfreq(n)[None, :]
    k = np.hypot(kx, ky)
    k[0, 0] = 1.0
    amp = k ** (-(hurst + 1))
    amp[0, 0] = 0.0
    z = np.fft.irfft2(amp * np.exp(2j * np.pi * rng.random(amp.shape)), s=(n, n))
    return z / z.std()


def hurst_variograma(z, separaciones=(1, 2, 4, 8, 16, 32)) -> dict:
    """⟨(z(x + r) − z(x))²⟩ ∝ r^(2H) a lo largo de las filas. Dimensión de la superficie: D = 3 − H."""
    z = np.asarray(z, float)
    v = [float(((z[:, r:] - z[:, :-r]) ** 2).mean()) for r in separaciones]
    aj = ajuste_loglog(separaciones, v)
    H = aj["pendiente"] / 2
    return {"H": H, "D": 3 - H, "r2": aj["r2"]}
