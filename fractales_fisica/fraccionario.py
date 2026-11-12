"""Cálculo fraccionario numérico: derivadas de Grünwald-Letnikov y de Caputo (esquema L1), función de Mittag-Leffler,
relajación fraccionaria y ecuación de difusión fraccionaria en el tiempo ∂^α u/∂t^α = K ∂²u/∂x² (0 < α ≤ 1).

Para 0 < α < 1 el esquema L1 tiene un error de orden h^(2−α) si la solución es suave; cerca de t = 0 las soluciones
de estas ecuaciones no lo son, y el error inicial es mayor (Stynes y otros, 2017). Por eso los ajustes del libro
excluyen los primeros instantes.
"""
from __future__ import annotations

import math

import numpy as np

from .dimension import ajuste_loglog


def thomas(inf, diag, sup, d) -> np.ndarray:
    """Resuelve un sistema tridiagonal (algoritmo de Thomas). inf[0] y sup[-1] no se usan."""
    n = len(diag)
    c, e = np.empty(n), np.empty(n)
    c[0], e[0] = sup[0] / diag[0], d[0] / diag[0]
    for i in range(1, n):
        m = diag[i] - inf[i] * c[i - 1]
        c[i] = sup[i] / m if i < n - 1 else 0.0
        e[i] = (d[i] - inf[i] * e[i - 1]) / m
    x = np.empty(n)
    x[-1] = e[-1]
    for i in range(n - 2, -1, -1):
        x[i] = e[i] - c[i] * x[i + 1]
    return x


def pesos_gl(alfa: float, n: int) -> np.ndarray:
    """Pesos w_k = (−1)^k C(α, k) por la recurrencia w_k = w_{k−1} (1 − (α + 1)/k)."""
    w = np.empty(n)
    w[0] = 1.0
    for k in range(1, n):
        w[k] = w[k - 1] * (1 - (alfa + 1) / k)
    return w


def derivada_gl(f, h: float, alfa: float) -> np.ndarray:
    """Derivada de Grünwald-Letnikov de orden α de los valores f(t_0), …, f(t_n) con paso h (desde t_0)."""
    f = np.asarray(f, float)
    w = pesos_gl(alfa, len(f))
    return np.array([np.dot(w[: i + 1], f[i::-1]) for i in range(len(f))]) / h ** alfa


def derivada_caputo_l1(f, h: float, alfa: float) -> np.ndarray:
    """Derivada de Caputo de orden 0 < α < 1 por el esquema L1."""
    f = np.asarray(f, float)
    n = len(f)
    k = np.arange(n)
    b = (k + 1) ** (1 - alfa) - k ** (1 - alfa)
    df = np.diff(f)
    out = np.zeros(n)
    for i in range(1, n):
        out[i] = np.dot(b[:i], df[i - 1::-1])
    return out / (h ** alfa * math.gamma(2 - alfa))


def caputo_potencia(t, p: float, alfa: float):
    """Resultado exacto: D^α t^p = Γ(p + 1) / Γ(p + 1 − α) · t^(p − α) (Caputo, p > 0)."""
    return math.gamma(p + 1) / math.gamma(p + 1 - alfa) * np.asarray(t, float) ** (p - alfa)


def mittag_leffler(alfa: float, z, terminos: int = 200):
    """E_α(z) = Σ z^k / Γ(α k + 1) por su serie. Fiable para |z| ≲ 5 en doble precisión."""
    z = np.asarray(z, float)
    s = np.zeros_like(z)
    for k in range(terminos):
        lg = math.lgamma(alfa * k + 1)
        term = np.sign(z) ** k * np.exp(k * np.log(np.abs(z) + 1e-300) - lg)
        s = s + np.where(np.abs(z) > 0, term, 1.0 if k == 0 else 0.0)
    return s


def relajacion(alfa: float, lam: float, T: float, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Resuelve D^α y = −λ y, y(0) = 1, con el esquema L1 implícito. La solución exacta es E_α(−λ t^α)."""
    h = T / n
    c = 1 / (h ** alfa * math.gamma(2 - alfa))
    k = np.arange(n + 1)
    b = (k + 1) ** (1 - alfa) - k ** (1 - alfa)
    y = np.zeros(n + 1)
    y[0] = 1.0
    for m in range(1, n + 1):
        hist = sum(b[j] * (y[m - j] - y[m - j - 1]) for j in range(1, m))
        y[m] = (c * y[m - 1] - c * hist) / (c + lam)
    return np.linspace(0, T, n + 1), y


def difusion_fraccionaria(alfa: float, K: float = 1.0, L: float = 12.0, nx: int = 481, T: float = 1.0, nt: int = 400,
                          sigma0: float = 0.05) -> dict:
    """∂^α u/∂t^α = K ∂²u/∂x² en [−L, L] con u = 0 en los bordes y un pulso gaussiano estrecho centrado en 0.

    Devuelve los tiempos, el desplazamiento cuadrático medio ⟨x²⟩(t) y los perfiles en cinco instantes.
    Resultado teórico para un pulso puntual en dominio infinito: ⟨x²⟩ = 2 K t^α / Γ(1 + α).
    """
    x = np.linspace(-L, L, nx)
    dx = x[1] - x[0]
    h = T / nt
    c = 1 / (h ** alfa * math.gamma(2 - alfa))
    k = np.arange(nt + 1)
    b = (k + 1) ** (1 - alfa) - k ** (1 - alfa)
    u0 = np.exp(-x ** 2 / (2 * sigma0 ** 2))
    u0 /= u0.sum() * dx
    U = [u0]
    # matriz (c I − K Δ) en banda, con bordes de Dirichlet
    r = K / dx ** 2
    inf, diag, sup = np.full(nx, -r), np.full(nx, c + 2 * r), np.full(nx, -r)
    diag[0] = diag[-1] = 1.0
    sup[0] = inf[-1] = 0.0
    msd, tiempos, perfiles = [float((x ** 2 * u0).sum() * dx - sigma0 ** 2)], [0.0], {}
    marcas = {nt // 8, nt // 4, nt // 2, nt}
    dif = []                                   # u^{m} − u^{m−1}
    for m in range(1, nt + 1):
        rhs = c * U[-1].copy()
        if dif:
            D = np.array(dif[::-1])            # D[0] = u^{m−1} − u^{m−2}, …
            rhs -= c * (b[1:m, None] * D).sum(0)
        rhs[0] = rhs[-1] = 0.0
        un = thomas(inf, diag, sup, rhs)
        dif.append(un - U[-1])
        U.append(un)
        tiempos.append(m * h)
        msd.append(float((x ** 2 * un).sum() * dx / (un.sum() * dx) - sigma0 ** 2))
        if m in marcas:
            perfiles[round(m * h, 6)] = un.copy()
        if len(U) > 2:
            U.pop(0)
    t = np.array(tiempos)
    msd = np.array(msd)
    sel = t >= T / 10
    aj = ajuste_loglog(t[sel], msd[sel])
    return {"x": x, "t": t, "msd": msd, "perfiles": perfiles, "alfa_ajustado": aj["pendiente"],
            "coef_ajustado": math.exp(aj["ordenada"]), "coef_teorico": 2 * K / math.gamma(1 + alfa)}
