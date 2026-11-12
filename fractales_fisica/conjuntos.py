"""Conjuntos fractales clásicos: Cantor, Koch, Sierpinski (triángulo y alfombra), juego del caos, Mandelbrot y Julia."""
from __future__ import annotations

import numpy as np


def cantor(nivel: int) -> list[tuple[float, float]]:
    """Intervalos del conjunto de Cantor ternario en el nivel dado (2^nivel intervalos de longitud 3^−nivel)."""
    tramos = [(0.0, 1.0)]
    for _ in range(nivel):
        nuevos = []
        for a, b in tramos:
            t = (b - a) / 3
            nuevos += [(a, a + t), (b - t, b)]
        tramos = nuevos
    return tramos


def koch(nivel: int) -> np.ndarray:
    """Vértices de la curva de Koch entre (0, 0) y (1, 0): 4^nivel segmentos de longitud 3^−nivel."""
    pts = np.array([[0.0, 0.0], [1.0, 0.0]])
    rot = np.array([[0.5, -np.sqrt(3) / 2], [np.sqrt(3) / 2, 0.5]])
    for _ in range(nivel):
        nuevos = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            d = (b - a) / 3
            p1, p3 = a + d, a + 2 * d
            p2 = p1 + rot @ d
            nuevos += [p1, p2, p3, b]
        pts = np.array(nuevos)
    return pts


def copo_koch(nivel: int) -> np.ndarray:
    """Copo de nieve de Koch: tres curvas de Koch sobre un triángulo equilátero (polígono cerrado)."""
    c = koch(nivel)
    lados = []
    vert = np.array([[0.0, 0.0], [0.5, np.sqrt(3) / 2], [1.0, 0.0], [0.0, 0.0]])
    for a, b in zip(vert[:-1], vert[1:]):
        d = b - a
        ang = np.arctan2(d[1], d[0])
        r = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
        # la curva se refleja para que los picos apunten hacia fuera
        cc = c * np.array([1.0, -1.0])
        lados.append(a + (r @ (cc * np.hypot(*d)).T).T)
    return np.vstack([l[:-1] for l in lados] + [lados[0][:1]])


def sierpinski(nivel: int) -> np.ndarray:
    """Triángulo de Sierpinski como imagen binaria de 2^nivel × 2^nivel (triángulo de Pascal módulo 2)."""
    n = 2 ** nivel
    i, j = np.indices((n, n))
    return ((i & j) == j) & (j <= i)


def alfombra(nivel: int) -> np.ndarray:
    """Alfombra de Sierpinski como imagen binaria de 3^nivel × 3^nivel (True = material)."""
    a = np.ones((1, 1), bool)
    for _ in range(nivel):
        z = np.zeros_like(a)
        a = np.block([[a, a, a], [a, z, a], [a, a, a]])
    return a


def juego_del_caos(n: int, semilla: int = 1, vertices=None, razon: float = 0.5) -> np.ndarray:
    """Juego del caos (Barnsley): saltar una fracción `razon` de la distancia hacia un vértice elegido al azar.
    Cada salto es una contracción de factor 1 − razon hacia ese vértice. Con tres vértices y razon = 1/2 (contracción
    1/2) los puntos se acumulan sobre el triángulo de Sierpinski; con razon = 0,6 la contracción es 0,4."""
    rng = np.random.default_rng(semilla)
    v = np.array(vertices if vertices is not None else [[0, 0], [1, 0], [0.5, np.sqrt(3) / 2]], float)
    elec = rng.integers(0, len(v), n)
    p = np.empty((n, 2))
    x = np.array([0.3, 0.3])
    for k in range(n):
        x = x + razon * (v[elec[k]] - x)
        p[k] = x
    return p[20:]


def mandelbrot(nx: int = 600, ny: int = 400, xlim=(-2.2, 0.8), ylim=(-1.0, 1.0), max_iter: int = 200) -> np.ndarray:
    """Tiempo de escape de z → z² + c desde z = 0; los puntos que no escapan en max_iter valen max_iter."""
    x = np.linspace(*xlim, nx)
    y = np.linspace(*ylim, ny)
    c = x[None, :] + 1j * y[:, None]
    z = np.zeros_like(c)
    n = np.full(c.shape, max_iter, int)
    vivo = np.ones(c.shape, bool)
    for k in range(max_iter):
        z[vivo] = z[vivo] ** 2 + c[vivo]
        esc = vivo & (np.abs(z) > 2)
        n[esc] = k
        vivo &= ~esc
    return n


def julia(c: complex, nx: int = 500, ny: int = 500, lim: float = 1.6, max_iter: int = 200) -> np.ndarray:
    """Tiempo de escape de z → z² + c desde cada punto z del plano (conjunto de Julia lleno)."""
    x = np.linspace(-lim, lim, nx)
    y = np.linspace(-lim, lim, ny)
    z = x[None, :] + 1j * y[:, None]
    n = np.full(z.shape, max_iter, int)
    vivo = np.ones(z.shape, bool)
    for k in range(max_iter):
        z[vivo] = z[vivo] ** 2 + c
        esc = vivo & (np.abs(z) > 2)
        n[esc] = k
        vivo &= ~esc
    return n


def borde(img) -> np.ndarray:
    """Píxeles del interior que tocan al menos un píxel del exterior (vecindad de 4)."""
    a = np.asarray(img, bool)
    p = np.pad(a, 1, constant_values=False)
    vecino_fuera = ~p[:-2, 1:-1] | ~p[2:, 1:-1] | ~p[1:-1, :-2] | ~p[1:-1, 2:]
    return a & vecino_fuera
