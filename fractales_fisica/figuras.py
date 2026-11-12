"""Figuras del libro en escala de grises, a su tamaño de impresión (4,7 in de ancho), con letra de 8 pt y trazos de
0,9 pt o más. Necesita matplotlib.

Uso: python -m fractales_fisica figuras --carpeta figuras     (o generar_todas(carpeta, datos))
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

NOMBRES = ["fig01-cantor-koch", "fig02-conteo-cajas", "fig03-leyes-potencia", "fig04-mandelbrot-julia", "fig05-juego-caos",
           "fig06-caminata-msd", "fig07-levy", "fig08-anomala", "fig09-dla", "fig10-percolacion", "fig11-bifurcacion",
           "fig12-lorenz", "fig13-turbulencia", "fig14-cascada", "fig15-difusion-fraccionaria", "fig16-relajacion",
           "fig17-porosos", "fig18-antenas-koch", "fig19-sierpinski-niveles", "fig20-kleiber", "fig21-costa", "fig22-hurst"]
ANCHO_IN = 4.7
DPI = 300
LETRA_PT = 8.0
TRAZO_MIN_PT = 0.9


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.size": LETRA_PT, "axes.titlesize": LETRA_PT + 0.5, "axes.labelsize": LETRA_PT, "xtick.labelsize": LETRA_PT - 0.5,
        "ytick.labelsize": LETRA_PT - 0.5, "legend.fontsize": LETRA_PT - 0.5, "lines.linewidth": 1.2, "axes.linewidth": TRAZO_MIN_PT,
        "xtick.major.width": TRAZO_MIN_PT, "ytick.major.width": TRAZO_MIN_PT, "xtick.minor.width": TRAZO_MIN_PT * 0.9,
        "ytick.minor.width": TRAZO_MIN_PT * 0.9, "font.family": "DejaVu Sans", "axes.prop_cycle": __import__("cycler").cycler(color=["black"]),
        "savefig.facecolor": "white", "figure.facecolor": "white", "axes.grid": False, "axes.formatter.use_locale": False,
        "axes.unicode_minus": True,
    })
    return plt


def _coma(ax):
    """Decimales con coma en los ejes lineales."""
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: (f"{v:g}").replace(".", ",").replace("-", "−"))
    for eje in (ax.xaxis, ax.yaxis):
        if eje.get_scale() == "linear":
            eje.set_major_formatter(f)


def _fmt_log(v, _):
    import math
    if v <= 0:
        return ""
    k = round(math.log10(v))
    if abs(math.log10(v) - k) > 1e-6:
        return ""
    if -2 <= k <= 4:
        return f"{v:g}".replace(".", ",")
    return f"$10^{{{k}}}$"


def _ejes_log(fig):
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
    for ax in fig.axes:
        for eje in (ax.xaxis, ax.yaxis):
            if eje.get_scale() == "log":
                eje.set_major_locator(LogLocator(base=10, numticks=12))
                eje.set_major_formatter(FuncFormatter(_fmt_log))
                eje.set_minor_formatter(NullFormatter())


def _guardar(fig, carpeta, nombre):
    _ejes_log(fig)
    ruta = Path(carpeta) / f"{nombre}.png"
    fig.savefig(ruta, dpi=DPI)
    import matplotlib.pyplot as plt
    plt.close(fig)
    # escala de grises de 8 bits
    from PIL import Image
    Image.open(ruta).convert("L").save(ruta, optimize=True)
    return ruta


def _fig(alto_in, ncols=1, **kw):
    plt = _mpl()
    fig, ax = plt.subplots(1, ncols, figsize=(ANCHO_IN, alto_in), constrained_layout=True, **kw)
    return plt, fig, ax


def _loglog_ajuste(ax, x, y, pend, ord_, etiqueta_puntos, etiqueta_recta, marcador="o"):
    ax.loglog(x, y, marcador, ms=4, mfc="white", mec="black", mew=TRAZO_MIN_PT, label=etiqueta_puntos)
    xx = np.geomspace(min(x), max(x), 50)
    ax.loglog(xx, np.exp(ord_) * xx ** pend, "-", color="black", lw=1.1, label=etiqueta_recta)


def _f(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


def generar_todas(carpeta, datos=None, cifras=None) -> list[Path]:
    from . import conjuntos, dimension
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    if datos is None or cifras is None:
        from .libro import calcular
        cifras, datos = calcular()
    C = {k: v["v"] for k, v in cifras.items()}
    out = []

    # 1. Cantor y Koch
    plt, fig, ax = _fig(2.6, 2)
    for n in range(5):
        for a, b in conjuntos.cantor(n):
            ax[0].plot([a, b], [-n, -n], "-", color="black", lw=4, solid_capstyle="butt")
        ax[0].text(-0.06, -n, f"n = {n}", ha="right", va="center")
    ax[0].set_xlim(-0.3, 1.02); ax[0].set_ylim(-4.6, 0.6); ax[0].axis("off"); ax[0].set_title("Conjunto de Cantor")
    for n, dy in zip(range(4), (0, -0.45, -0.9, -1.35)):
        p = conjuntos.koch(n)
        ax[1].plot(p[:, 0], p[:, 1] + dy, "-", color="black", lw=1.0)
        ax[1].text(-0.04, dy, f"n = {n}", ha="right", va="bottom")
    ax[1].set_xlim(-0.25, 1.02); ax[1].set_aspect("equal"); ax[1].axis("off"); ax[1].set_title("Curva de Koch")
    out.append(_guardar(fig, carpeta, "fig01-cantor-koch"))

    # 2. Conteo de cajas de Sierpinski
    plt, fig, ax = _fig(2.4, 2)
    s = conjuntos.sierpinski(7)
    ax[0].imshow(~s, cmap="gray", interpolation="nearest"); ax[0].axis("off"); ax[0].set_title("Sierpinski, nivel 7")
    bc = datos["bc_sierp"]
    _loglog_ajuste(ax[1], bc["tamanos"], bc["conteos"], -bc["D"], bc["ordenada"],
                   "cajas ocupadas", f"pendiente −{_f(bc['D'], 3)}")
    ax[1].set_xlabel("lado de la caja s (píxeles)"); ax[1].set_ylabel("N(s)"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig02-conteo-cajas"))

    # 3. Ley de potencias y falsa ley
    plt, fig, ax = _fig(2.4, 2)
    L, T, aj = datos["pendulo"]
    _loglog_ajuste(ax[0], L, T, aj["pendiente"], aj["ordenada"], "medidas simuladas", "T ∝ L$^{" + _f(aj["pendiente"], 3) + "}$")
    ax[0].set_xlabel("longitud L (m)"); ax[0].set_ylabel("periodo T (s)"); ax[0].legend(frameon=False)
    x, y, ae = datos["falsa"]
    _loglog_ajuste(ax[1], x, y, ae["pendiente"], ae["ordenada"], "y = eˣ", f"recta, R² = {_f(ae['r2'], 3)}", "s")
    ax[1].set_xlabel("x"); ax[1].set_ylabel("y"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig03-leyes-potencia"))

    # 4. Mandelbrot y Julia
    plt, fig, ax = _fig(2.3, 2)
    m = datos["mand"]
    ax[0].imshow(np.log1p(m), cmap="gray_r", extent=(-2.2, 0.8, -1, 1), origin="lower")
    ax[0].set_title("Mandelbrot (z² + c)"); ax[0].set_xlabel("Re c"); ax[0].set_ylabel("Im c"); _coma(ax[0])
    j = datos["julia"]
    ax[1].imshow(np.log1p(j), cmap="gray_r", extent=(-1.5, 1.5, -1.5, 1.5), origin="lower", aspect="auto")
    ax[1].set_title("Julia, c = −0,8 + 0,156i"); ax[1].set_xlabel("Re z"); ax[1].set_ylabel("Im z"); _coma(ax[1])
    out.append(_guardar(fig, carpeta, "fig04-mandelbrot-julia"))

    # 5. Juego del caos
    plt, fig, ax = _fig(2.4, 2)
    p = datos["caos_pts"]
    ax[0].plot(p[:300, 0], p[:300, 1], ".", ms=2.5, color="black"); ax[0].set_title("300 puntos"); ax[0].set_aspect("equal"); ax[0].axis("off")
    ax[1].plot(p[:, 0], p[:, 1], ",", color="black"); ax[1].set_title(f"{len(p):,} puntos".replace(",", " ")); ax[1].set_aspect("equal"); ax[1].axis("off")
    out.append(_guardar(fig, carpeta, "fig05-juego-caos"))

    # 6. Caminata y MSD
    plt, fig, ax = _fig(2.4, 2)
    w = datos["caminata"]
    ax[0].plot(w[:, 0], w[:, 1], "-", color="black", lw=0.9); ax[0].set_aspect("equal"); ax[0].set_title("20 000 pasos"); _coma(ax[0])
    t, msd = datos["msd"]
    sel = np.unique(np.geomspace(1, len(t), 20).astype(int)) - 1
    ax[1].loglog(t[sel], msd[sel], "o", ms=4, mfc="white", mec="black", mew=TRAZO_MIN_PT, label="⟨r²⟩ simulado")
    ax[1].loglog(t, t, "-", color="black", lw=1.0, label="⟨r²⟩ = t")
    ax[1].set_xlabel("pasos t"); ax[1].set_ylabel("⟨r²⟩"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig06-caminata-msd"))

    # 7. Lévy frente a browniano
    plt, fig, ax = _fig(2.4, 2)
    b = datos["browniano_corto"]; l = datos["levy"]
    ax[0].plot(b[:, 0], b[:, 1], "-", color="black", lw=0.9); ax[0].set_aspect("equal"); ax[0].set_title("Browniano, 3000 pasos"); _coma(ax[0])
    ax[1].plot(l[:, 0], l[:, 1], "-", color="black", lw=0.9); ax[1].plot(l[:, 0], l[:, 1], ".", ms=1.6, color="black")
    ax[1].set_aspect("equal"); ax[1].set_title("Lévy μ = 1,5, 3000 saltos"); _coma(ax[1])
    out.append(_guardar(fig, carpeta, "fig07-levy"))

    # 8. CTRW y Lévy: exponentes
    plt, fig, ax = _fig(2.4, 2)
    tc, mc = datos["ctrw"]
    ax[0].loglog(tc, mc, "o", ms=4, mfc="white", mec="black", mew=TRAZO_MIN_PT, label="simulación")
    ax[0].loglog(tc, mc[-1] * (tc / tc[-1]) ** 0.6, "-", color="black", lw=1.0, label="pendiente 0,6")
    ax[0].loglog(tc, mc[-1] * (tc / tc[-1]) ** 1.0, "--", color="black", lw=1.0, label="pendiente 1")
    ax[0].set_xlabel("tiempo"); ax[0].set_ylabel("⟨x²⟩"); ax[0].set_title("Esperas largas (α = 0,6)"); ax[0].legend(frameon=False)
    tl, med = datos["levy_escala"]
    sel = np.unique(np.geomspace(1, len(tl), 20).astype(int)) - 1
    ax[1].loglog(tl[sel], med[sel], "o", ms=4, mfc="white", mec="black", mew=TRAZO_MIN_PT, label="mediana de |r|")
    ax[1].loglog(tl, med[-1] * (tl / tl[-1]) ** (1 / 1.5), "-", color="black", lw=1.0, label="pendiente 1/μ")
    ax[1].loglog(tl, med[-1] * (tl / tl[-1]) ** 0.5, "--", color="black", lw=1.0, label="pendiente 1/2")
    ax[1].set_xlabel("saltos t"); ax[1].set_title("Vuelo de Lévy (μ = 1,5)"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig08-anomala"))

    # 9. DLA
    plt, fig, ax = _fig(2.5, 2)
    g, mr = datos["dla"]
    ys, xs = np.nonzero(g)
    c0 = g.shape[0] // 2
    r = int(max(np.abs(ys - c0).max(), np.abs(xs - c0).max())) + 4
    ax[0].imshow(~g[c0 - r:c0 + r, c0 - r:c0 + r], cmap="gray", interpolation="nearest"); ax[0].axis("off")
    ax[0].set_title(f"DLA, {int(g.sum())} partículas")
    _loglog_ajuste(ax[1], mr["radios"], mr["masas"], mr["D"], mr["ordenada"],
                   "M(R)", f"pendiente {_f(mr['D'], 2)}")
    ax[1].set_xlabel("radio R (píxeles)"); ax[1].set_ylabel("partículas dentro de R"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig09-dla"))

    # 10. Percolación
    plt, fig, ax = _fig(2.5, 2)
    red, mayor = datos["perc_red"]
    img = np.where(mayor, 0.0, np.where(red, 0.62, 1.0))
    ax[0].imshow(img, cmap="gray", vmin=0, vmax=1, interpolation="nearest"); ax[0].axis("off"); ax[0].set_title("Cúmulo mayor (negro)")
    ps, P64, P128 = datos["cruce"]
    ax[1].plot(ps, P64, "o-", ms=3.5, mfc="white", mec="black", color="black", lw=1.0, label="L = 64")
    ax[1].plot(ps, P128, "s--", ms=3.5, mfc="black", mec="black", color="black", lw=1.0, label="L = 128")
    ax[1].axhline(0.5, color="black", lw=TRAZO_MIN_PT, ls=":")
    ax[1].set_xlabel("probabilidad de ocupación p"); ax[1].set_ylabel("probabilidad de cruce"); ax[1].legend(frameon=False); _coma(ax[1])
    out.append(_guardar(fig, carpeta, "fig10-percolacion"))

    # 11. Bifurcación y Lyapunov
    plt = _mpl()
    fig, ax = plt.subplots(2, 1, figsize=(ANCHO_IN, 3.8), sharex=True, constrained_layout=True)
    R, X = datos["bif"]
    ax[0].plot(R, X, ",", color="black", alpha=1.0); ax[0].set_ylabel("x (estado final)")
    rs, ly = datos["lyap_curva"]
    ax[1].plot(rs, ly, "-", color="black", lw=0.9); ax[1].axhline(0, color="black", lw=TRAZO_MIN_PT, ls="--")
    ax[1].set_ylim(-2, 1); ax[1].set_xlabel("r"); ax[1].set_ylabel("exponente de Lyapunov λ")
    _coma(ax[0]); _coma(ax[1])
    out.append(_guardar(fig, carpeta, "fig11-bifurcacion"))

    # 12. Lorenz
    plt, fig, ax = _fig(2.5, 2)
    Lz = datos["lorenz"]
    ax[0].plot(Lz[:8000, 0], Lz[:8000, 2], "-", color="black", lw=0.5 + 0.4)
    ax[0].set_xlabel("x"); ax[0].set_ylabel("z"); ax[0].set_title("Atractor de Lorenz"); _coma(ax[0])
    ts, sep = datos["sep"]
    ax[1].semilogy(ts, sep, "-", color="black", lw=0.9, label="separación")
    k0 = int(np.argmax(sep > 1e-4))
    ax[1].semilogy(ts, sep[k0] * np.exp(C["lorenz_lyap"] * (ts - ts[k0])), "--", color="black", lw=1.0, label=r"pendiente media $\lambda$")
    ax[1].set_ylim(1e-9, 1e2); ax[1].set_xlabel("tiempo"); ax[1].set_ylabel("distancia"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig12-lorenz"))

    # 13. Turbulencia
    plt, fig, ax = _fig(2.5, 2)
    k, E = datos["espectro"]
    ax[0].loglog(k, E, "o", ms=3.5, mfc="white", mec="black", mew=TRAZO_MIN_PT, label="espectro")
    kk = np.geomspace(k[2], k[-3], 20)
    ax[0].loglog(kk, E[10] * (kk / k[10]) ** (-5 / 3), "-", color="black", lw=1.0, label="k^(−5/3)")
    ax[0].set_xlabel("número de onda k"); ax[0].set_ylabel("E(k)"); ax[0].legend(frameon=False)
    ps_, zs = datos["zetas"]
    ax[1].plot(ps_, np.array(ps_) / 3, "--", color="black", lw=1.0, label="K41: p/3")
    ax[1].plot(ps_, zs, "o-", ms=3.5, mfc="black", color="black", lw=1.0, label="cascada p = 0,7")
    ax[1].set_xlabel("orden p"); ax[1].set_ylabel(r"$\zeta_p$"); ax[1].legend(frameon=False); _coma(ax[1])
    out.append(_guardar(fig, carpeta, "fig13-turbulencia"))

    # 14. Cascada multifractal
    plt, fig, ax = _fig(1.9)
    med = datos["cascada"]
    caja = med.reshape(2 ** 8, -1).sum(1)
    ax.fill_between(np.arange(len(caja)) / len(caja), caja * len(caja), step="post", color="black", lw=0)
    ax.set_xlabel("posición x"); ax.set_ylabel("disipación local / media"); _coma(ax)
    out.append(_guardar(fig, carpeta, "fig14-cascada"))

    # 15. Difusión fraccionaria
    plt, fig, ax = _fig(2.5, 2)
    r = datos["fdif05"]
    estilos = ["-", "--", "-.", ":"]
    for (tt, perfil), est in zip(sorted(r["perfiles"].items()), estilos):
        ax[0].plot(r["x"], perfil, est, color="black", lw=1.1, label=f"t = {_f(tt, 3).rstrip('0').rstrip(',')}")
    ax[0].set_xlim(-6, 6); ax[0].set_xlabel("x"); ax[0].set_ylabel("u(x, t)"); ax[0].set_title("α = 0,5"); ax[0].legend(frameon=False); _coma(ax[0])
    for clave, mk, et in (("fdif05", "o", "α = 0,5"), ("fdif08", "s", "α = 0,8"), ("fdif10", "^", "α = 1")):
        rr = datos[clave]
        sel = np.unique(np.geomspace(1, len(rr["t"]) - 1, 14).astype(int))
        ax[1].loglog(rr["t"][sel], rr["msd"][sel], mk, ms=3.5, mfc="white", mec="black", mew=TRAZO_MIN_PT, label=et)
    ax[1].set_xlabel("t"); ax[1].set_ylabel("⟨x²⟩"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig15-difusion-fraccionaria"))

    # 16. Relajación
    plt, fig, ax = _fig(2.2)
    for (a, (tt, yy)), est in zip(sorted(datos["relaj"].items()), ["-", "--", ":"]):
        ax.plot(tt, yy, est, color="black", lw=1.2, label=f"α = {_f(a, 1)}")
    ax.set_xlabel("t"); ax.set_ylabel("y(t)"); ax.legend(frameon=False); _coma(ax)
    out.append(_guardar(fig, carpeta, "fig16-relajacion"))

    # 17. Porosos y rugosidad
    plt, fig, ax = _fig(2.4, 2)
    fis, kr = datos["perm"]
    ax[0].plot(fis, kr, "o-", ms=3.5, mfc="white", mec="black", color="black", lw=1.0)
    ax[0].axvline(0.5927, color="black", lw=TRAZO_MIN_PT, ls=":")
    ax[0].set_xlabel("porosidad φ"); ax[0].set_ylabel("permeabilidad relativa"); _coma(ax[0])
    z = datos["superficie"]
    ax[1].imshow(z[:256, :256], cmap="gray", interpolation="bilinear"); ax[1].axis("off"); ax[1].set_title("Superficie con H = 0,7")
    out.append(_guardar(fig, carpeta, "fig17-porosos"))

    # 18. Antenas
    plt, fig, ax = _fig(2.3, 3)
    for i, n in enumerate((0, 2, 4)):
        p = conjuntos.koch(n)
        ax[i].plot(p[:, 1], p[:, 0], "-", color="black", lw=1.0)
        ax[i].plot([0, 0], [-0.08, 0], "-", color="black", lw=2.5)
        ax[i].set_aspect("equal"); ax[i].axis("off"); ax[i].set_title(f"Koch n = {n}")
    out.append(_guardar(fig, carpeta, "fig18-antenas-koch"))
    plt, fig, ax = _fig(2.0, 3)
    for i, n in enumerate((2, 4, 6)):
        ax[i].imshow(~conjuntos.sierpinski(n), cmap="gray", interpolation="nearest"); ax[i].axis("off")
        ax[i].set_title(f"nivel {n}")
    out.append(_guardar(fig, carpeta, "fig19-sierpinski-niveles"))

    # 19. Kleiber / WBE
    plt, fig, ax = _fig(2.3)
    Ns, ex = datos["wbe"]
    ax.plot(Ns, ex, "o-", ms=3, mfc="white", mec="black", color="black", lw=1.0, label="exponente local de la red")
    ax.axhline(0.75, color="black", lw=TRAZO_MIN_PT, ls="--", label="3/4")
    ax.axhline(2 / 3, color="black", lw=TRAZO_MIN_PT, ls=":", label="2/3")
    ax.set_xlabel("niveles de ramificación N"); ax.set_ylabel("d ln B / d ln M"); ax.legend(frameon=False); _coma(ax)
    out.append(_guardar(fig, carpeta, "fig20-kleiber"))

    # 20. Costa
    plt, fig, ax = _fig(2.4, 2)
    costa, rd = datos["costa"]
    ax[0].plot(costa[:, 0], costa[:, 1], "-", color="black", lw=0.9); ax[0].set_title("Costa sintética, H = 0,6"); _coma(ax[0])
    _loglog_ajuste(ax[1], rd["pasos"], rd["longitudes"], 1 - rd["D"], rd["ordenada"],
                   "L(δ)", f"D = {_f(rd['D'], 2)}")
    ax[1].set_xlabel("abertura del compás δ"); ax[1].set_ylabel("longitud medida"); ax[1].legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig21-costa"))

    # 21. Hurst
    plt, fig, ax = _fig(2.4)
    for clave, mk, et in (("dfa_03", "o", "H = 0,3"), ("dfa_05", "s", "H = 0,5"), ("dfa_07", "^", "H = 0,7")):
        d = datos[clave]
        ax.loglog(d["tamanos"], d["F"], mk + "-", ms=3.5, mfc="white", mec="black", color="black", lw=0.9,
                  label=f"{et}: α = {_f(d['alfa'], 2)}")
    ax.set_xlabel("ventana n"); ax.set_ylabel("fluctuación F(n)"); ax.legend(frameon=False)
    out.append(_guardar(fig, carpeta, "fig22-hurst"))
    assert [p.stem for p in out] == NOMBRES, "la lista NOMBRES no coincide con las figuras generadas"
    return out
