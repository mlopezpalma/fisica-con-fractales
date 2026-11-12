"""Biología y geofísica: red vascular de West, Brown y Enquist (1997) y ley de Kleiber; costas autoafines y regla
de Richardson."""
from __future__ import annotations

import math

import numpy as np

from .dimension import ajuste_loglog


def red_wbe(niveles: int, ramas: int = 2, beta: float | None = None, gamma: float | None = None) -> dict:
    """Red jerárquica: en cada nivel cada vaso se divide en `ramas` hijos con radio β·r y longitud γ·l.

    Por defecto, β = n^(−1/2) (conserva el área de la sección, vasos grandes) y γ = n^(−1/3) (la red llena el
    volumen). El capilar (último nivel) es igual en todos los tamaños de red. Devuelve el número de capilares
    (proporcional al metabolismo B en el modelo) y el volumen de sangre (proporcional a la masa M)."""
    n = ramas
    beta = n ** -0.5 if beta is None else beta
    gamma = n ** (-1 / 3) if gamma is None else gamma
    k = np.arange(niveles + 1)
    r = beta ** (k - niveles)          # radio relativo al capilar
    l = gamma ** (k - niveles)
    volumen = float(np.sum(n ** k * math.pi * r ** 2 * l))
    return {"capilares": float(n ** niveles), "volumen": volumen}


def exponente_wbe(niveles_lista, ramas: int = 2, beta=None, gamma=None) -> dict:
    """Exponente de escala d ln B / d ln M entre redes de distinto número de niveles."""
    d = [red_wbe(N, ramas, beta, gamma) for N in niveles_lista]
    aj = ajuste_loglog([x["volumen"] for x in d], [x["capilares"] for x in d])
    return {"exponente": aj["pendiente"], "r2": aj["r2"]}


def exponente_local_wbe(N: int, ramas: int = 2, beta=None, gamma=None) -> float:
    a, b = red_wbe(N, ramas, beta, gamma), red_wbe(N + 1, ramas, beta, gamma)
    return math.log(b["capilares"] / a["capilares"]) / math.log(b["volumen"] / a["volumen"])


def cociente_metabolico(masa_a: float, masa_b: float, exponente: float) -> float:
    """B_b / B_a para una ley B ∝ M^b."""
    return (masa_b / masa_a) ** exponente


def costa_autoafin(n: int, hurst: float, semilla: int = 51) -> np.ndarray:
    """Perfil de costa sintético: gráfica de un movimiento browniano fraccionario (dimensión de la gráfica 2 − H),
    reescalada a la caja unidad."""
    from .aleatorio import fbm
    y = fbm(n, hurst, semilla)
    x = np.linspace(0, 1, len(y))
    y = (y - y.min()) / (y.max() - y.min())
    return np.column_stack([x, y])
