"""Caos determinista: mapa logístico (bifurcaciones, Feigenbaum, Lyapunov) y atractor de Lorenz
(integración RK4, exponente de Lyapunov máximo por el método de Benettin, dimensión de correlación)."""
from __future__ import annotations

import math

import numpy as np

from .dimension import ajuste_loglog


# ------------------------------------------------------------------ mapa logístico
def logistico(r: float, x0: float = 0.2, n: int = 1000) -> np.ndarray:
    """Órbita x_{k+1} = r x_k (1 − x_k)."""
    x = np.empty(n)
    v = x0
    for k in range(n):
        v = r * v * (1 - v)
        x[k] = v
    return x


def bifurcacion(r_min=2.8, r_max=4.0, n_r=800, transitorio=600, n_puntos=120) -> tuple[np.ndarray, np.ndarray]:
    """Datos del diagrama de bifurcación: para cada r, los últimos n_puntos valores de la órbita."""
    rs = np.linspace(r_min, r_max, n_r)
    x = np.full(n_r, 0.2)
    for _ in range(transitorio):
        x = rs * x * (1 - x)
    R, X = [], []
    for _ in range(n_puntos):
        x = rs * x * (1 - x)
        R.append(rs.copy()); X.append(x.copy())
    return np.concatenate(R), np.concatenate(X)


def lyapunov_logistico(r: float, n: int = 100_000, transitorio: int = 1000, x0: float = 0.2) -> float:
    """λ = media de ln|f'(x_k)| = media de ln|r (1 − 2 x_k)| a lo largo de la órbita."""
    x = x0
    for _ in range(transitorio):
        x = r * x * (1 - x)
    s = 0.0
    for _ in range(n):
        x = r * x * (1 - x)
        s += math.log(abs(r * (1 - 2 * x)) + 1e-300)
    return s / n


def _g(r: float, m: int) -> tuple[float, float]:
    """f_r^m(1/2) − 1/2 y su derivada respecto de r."""
    x, dx = 0.5, 0.0
    for _ in range(m):
        dx = x * (1 - x) + r * (1 - 2 * x) * dx
        x = r * x * (1 - x)
    return x - 0.5, dx


def superestables(n_max: int = 12) -> list[float]:
    """Parámetros R_n en los que la órbita de periodo 2^n pasa por x = 1/2 (órbita superestable).

    Se resuelve f^{2^n}(1/2) = 1/2 por Newton, partiendo de la extrapolación geométrica de los dos anteriores.
    """
    R = [2.0, 1 + math.sqrt(5)]
    delta = 4.7
    for n in range(2, n_max + 1):
        r = R[-1] + (R[-1] - R[-2]) / delta
        for _ in range(60):
            g, dg = _g(r, 2 ** n)
            paso = g / dg
            r -= paso
            if abs(paso) < 1e-15:
                break
        R.append(r)
        delta = (R[-2] - R[-3]) / (R[-1] - R[-2])
    return R


def feigenbaum(n_max: int = 12) -> dict:
    """Estimaciones de δ y α de Feigenbaum a partir de los parámetros superestables R_n.

    δ_n = (R_{n−1} − R_{n−2}) / (R_n − R_{n−1});  d_n = f^{2^{n−1}}(1/2; R_n) − 1/2;  α_n = −d_n / d_{n+1}.
    También extrapola r_∞ = R_n + (R_n − R_{n−1}) / (δ − 1).
    """
    R = superestables(n_max)
    deltas = [(R[n - 1] - R[n - 2]) / (R[n] - R[n - 1]) for n in range(2, len(R))]
    d = []
    for n in range(1, len(R)):
        x = 0.5
        for _ in range(2 ** (n - 1)):
            x = R[n] * x * (1 - x)
        d.append(x - 0.5)
    alfas = [-d[k] / d[k + 1] for k in range(len(d) - 1)]
    delta = deltas[-1]
    r_inf = R[-1] + (R[-1] - R[-2]) / (delta - 1)
    return {"R": R, "deltas": deltas, "alfas": alfas, "delta": delta, "alfa": alfas[-1], "r_inf": r_inf}


# ------------------------------------------------------------------ Lorenz
SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0


def _f_lorenz(x, y, z, s=SIGMA, r=RHO, b=BETA):
    return s * (y - x), x * (r - z) - y, x * y - b * z


def lorenz(n: int = 20000, dt: float = 0.01, x0=(1.0, 1.0, 1.0), transitorio: int = 1000) -> np.ndarray:
    """Trayectoria del sistema de Lorenz (σ = 10, ρ = 28, β = 8/3) integrada con Runge-Kutta de orden 4."""
    x, y, z = x0
    out = np.empty((n, 3))
    for k in range(n + transitorio):
        k1 = _f_lorenz(x, y, z)
        k2 = _f_lorenz(x + dt / 2 * k1[0], y + dt / 2 * k1[1], z + dt / 2 * k1[2])
        k3 = _f_lorenz(x + dt / 2 * k2[0], y + dt / 2 * k2[1], z + dt / 2 * k2[2])
        k4 = _f_lorenz(x + dt * k3[0], y + dt * k3[1], z + dt * k3[2])
        x += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        y += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        z += dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
        if k >= transitorio:
            out[k - transitorio] = (x, y, z)
    return out


def lyapunov_lorenz(t_total: float = 500.0, dt: float = 0.01, transitorio: float = 20.0) -> float:
    """Exponente de Lyapunov máximo (Benettin y otros, 1980): se integra a la vez la trayectoria y un vector
    tangente con la matriz jacobiana, se renormaliza el vector en cada paso y se promedia el logaritmo del crecimiento."""
    x, y, z = 1.0, 1.0, 1.0
    u = [1.0, 0.0, 0.0]
    s, b, r = SIGMA, BETA, RHO

    def campo(st):
        x, y, z, a, c, e = st
        fx, fy, fz = s * (y - x), x * (r - z) - y, x * y - b * z
        ga = s * (c - a)
        gc = (r - z) * a - c - x * e
        ge = y * a + x * c - b * e
        return (fx, fy, fz, ga, gc, ge)

    st = (x, y, z, *u)
    pasos_trans, pasos = int(transitorio / dt), int(t_total / dt)
    suma = 0.0
    for k in range(pasos_trans + pasos):
        k1 = campo(st)
        k2 = campo(tuple(a + dt / 2 * d for a, d in zip(st, k1)))
        k3 = campo(tuple(a + dt / 2 * d for a, d in zip(st, k2)))
        k4 = campo(tuple(a + dt * d for a, d in zip(st, k3)))
        st = tuple(a + dt / 6 * (d1 + 2 * d2 + 2 * d3 + d4) for a, d1, d2, d3, d4 in zip(st, k1, k2, k3, k4))
        norma = math.sqrt(st[3] ** 2 + st[4] ** 2 + st[5] ** 2)
        st = st[:3] + (st[3] / norma, st[4] / norma, st[5] / norma)
        if k >= pasos_trans:
            suma += math.log(norma)
    return suma / (pasos * dt)


def dimension_correlacion(puntos, radios, max_puntos: int = 3000, semilla: int = 3) -> dict:
    """Dimensión de correlación de Grassberger y Procaccia (1983): C(r) = fracción de pares a distancia < r;
    C(r) ∝ r^ν en la zona de escala."""
    p = np.asarray(puntos, float)
    if len(p) > max_puntos:
        rng = np.random.default_rng(semilla)
        p = p[rng.choice(len(p), max_puntos, replace=False)]
    d = np.sqrt(((p[:, None, :] - p[None, :, :]) ** 2).sum(-1))
    d = d[np.triu_indices(len(p), 1)]
    d.sort()
    C = np.searchsorted(d, radios) / len(d)
    aj = ajuste_loglog(radios, C)
    return {"D2": aj["pendiente"], "r2": aj["r2"], "radios": list(map(float, radios)), "C": C.tolist()}


def separacion_lorenz(epsilon: float = 1e-8, t: float = 30.0, dt: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    """Distancia entre dos trayectorias de Lorenz que empiezan separadas epsilon en x (efecto mariposa)."""
    a = lorenz(int(t / dt), dt, (1.0, 1.0, 1.0), transitorio=0)
    b = lorenz(int(t / dt), dt, (1.0 + epsilon, 1.0, 1.0), transitorio=0)
    return np.arange(1, len(a) + 1) * dt, np.linalg.norm(a - b, axis=1)
