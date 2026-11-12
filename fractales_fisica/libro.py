"""Todas las cifras y los datos de las figuras del libro «Física con fractales», calculadas con este paquete.

`calcular()` devuelve (cifras, datos):
- cifras: {clave: {"v": valor, "tipo": "calculado" | "exacto" | "supuesto", "desc": texto}}. El libro imprime estas
  cifras sustituyendo marcas {=clave|formato} y la QA las vuelve a calcular y las busca en el PDF.
- datos: arrays que usa `figuras.py` para dibujar.

Las semillas aleatorias son fijas: el mismo código da las mismas cifras en cualquier ordenador con NumPy ≥ 1.22.
"""
from __future__ import annotations

import math

import numpy as np

from . import aleatorio, antenas, biologia, caos, conjuntos, dimension, dla, fraccionario, ia, percolacion, porosos, series, turbulencia

KB = 1.380649e-23   # J/K, exacta desde 2019 (SI)


def calcular(rapido: bool = False) -> tuple[dict, dict]:
    C: dict = {}
    D: dict = {}

    def c(clave, v, tipo="calculado", desc=""):
        C[clave] = {"v": float(v), "tipo": tipo, "desc": desc}

    # ---------------------------------------------------------- 1. dimensión fractal
    c("D_cantor", dimension.dimension_semejanza(2, 1 / 3), "exacto", "log 2 / log 3")
    c("D_koch", dimension.dimension_semejanza(4, 1 / 3), "exacto", "log 4 / log 3")
    c("D_sierp", dimension.dimension_semejanza(3, 1 / 2), "exacto", "log 3 / log 2")
    c("D_alfombra", dimension.dimension_semejanza(8, 1 / 3), "exacto", "log 8 / log 3")
    c("D_menger", dimension.dimension_semejanza(20, 1 / 3), "exacto", "log 20 / log 3")
    c("D_vicsek", dimension.dimension_semejanza(5, 1 / 3), "exacto", "log 5 / log 3")
    c("D_cantor_mitad", dimension.dimension_semejanza(2, 1 / 4), "exacto", "Cantor quitando la mitad central")
    c("D_koch_cuadrada", dimension.dimension_semejanza(8, 1 / 4), "exacto", "curva de Koch cuadrada de tipo 2")
    sier = conjuntos.sierpinski(9)
    bc = dimension.box_counting(sier)
    c("bc_sierp", bc["D"], desc="conteo de cajas del triángulo de Sierpinski de nivel 9 (512 px)")
    c("bc_sierp_r2", bc["r2"])
    D["bc_sierp"] = bc
    alf = conjuntos.alfombra(6)
    b2 = dimension.box_counting(alf)
    b3 = dimension.box_counting(alf, [3 ** k for k in range(0, 5)])
    c("bc_alf_pot2", b2["D"], desc="alfombra nivel 6 con cajas de 2^k píxeles")
    c("bc_alf_pot3", b3["D"], desc="alfombra nivel 6 con cajas de 3^k píxeles")
    c("err_alf_pot2", abs(b2["D"] - C["D_alfombra"]["v"]))
    koch_img = dimension.rasterizar(conjuntos.koch(7), 2048)
    bk = dimension.box_counting(koch_img, [2 ** k for k in range(1, 8)])
    bk_fino = dimension.box_counting(koch_img, [2 ** k for k in range(0, 4)])
    bk_grueso = dimension.box_counting(koch_img, [2 ** k for k in range(5, 10)])
    c("bc_koch", bk["D"], desc="Koch nivel 7 en 2048 px, cajas de 2 a 128 px")
    c("bc_koch_fino", bk_fino["D"], desc="cajas de 1 a 8 px")
    c("bc_koch_grueso", bk_grueso["D"], desc="cajas de 32 a 512 px")
    D["bc_koch"] = bk
    c("koch_long5", antenas.longitud_koch(5), "exacto", "(4/3)^5")
    c("koch_long10", antenas.longitud_koch(10), "exacto")
    c("koch_segmentos5", 4 ** 5, "exacto")

    # ---------------------------------------------------------- 2. leyes de escala
    rng = np.random.default_rng(101)
    L = np.geomspace(0.1, 2.0, 12)
    T = 2 * math.pi * np.sqrt(L / 9.81) * (1 + 0.02 * rng.standard_normal(len(L)))
    aj = dimension.ajuste_loglog(L, T)
    c("pendulo_exp", aj["pendiente"], desc="exponente ajustado de T ∝ L^b con 2 % de ruido")
    c("pendulo_pref", math.exp(aj["ordenada"]), desc="prefactor ajustado (s·m^−1/2)")
    c("pendulo_exp_err", aj["error_pendiente"], desc="error típico del exponente")
    c("pendulo_pref_teor", 2 * math.pi / math.sqrt(9.81), "supuesto", "2π/√g con g = 9,81 m/s²")
    x = np.linspace(1, 3, 15)
    aj_e = dimension.ajuste_loglog(x, np.exp(x))
    c("falsa_r2", aj_e["r2"], desc="R² de un ajuste log-log a y = e^x en [1, 3]")
    c("falsa_pend", aj_e["pendiente"])
    D["pendulo"] = (L, T, aj)
    D["falsa"] = (x, np.exp(x), aj_e)
    c("decadas_pendulo", math.log10(L.max() / L.min()), desc="décadas cubiertas")

    # ---------------------------------------------------------- 3. conjuntos clásicos
    c("cantor_n5", len(conjuntos.cantor(5)), "exacto")
    c("cantor_long5", (2 / 3) ** 5, "exacto", "longitud que queda en el nivel 5")
    c("cantor_long20", (2 / 3) ** 20, "exacto")
    c("copo_area_limite", 8 / 5, "exacto", "área del copo / área del triángulo inicial")
    caos_pts = conjuntos.juego_del_caos(200_000, 1)
    bcc = dimension.box_counting(dimension.rasterizar(caos_pts, 1024), [2 ** k for k in range(1, 7)])
    c("bc_juego_caos", bcc["D"], desc="juego del caos, 200 000 puntos")
    D["caos_pts"] = caos_pts
    mand = conjuntos.mandelbrot(900, 600, max_iter=300 if not rapido else 120)
    dentro = mand >= mand.max()
    c("mand_area", dentro.sum() * (3.0 / 899) * (2.0 / 599), desc="área estimada por recuento de píxeles (900 × 600)")
    D["mand"] = mand
    mand_hr = conjuntos.mandelbrot(1024, 1024, (-2.0, 0.6), (-1.3, 1.3), max_iter=400 if not rapido else 150)
    borde = conjuntos.borde(mand_hr >= mand_hr.max())
    bm = dimension.box_counting(borde, [2 ** k for k in range(1, 7)])
    c("bc_mand_borde", bm["D"], desc="conteo de cajas del borde del Mandelbrot a 1024 px")
    D["julia"] = conjuntos.julia(complex(-0.8, 0.156), 700, 500, 1.5, 300 if not rapido else 120)

    # ---------------------------------------------------------- 4. browniano
    t, m = aleatorio.msd_conjunto(2000, 1000, 2)
    e = aleatorio.exponente_msd(t, m, 10)
    c("msd_alfa", e["alfa"], desc="exponente de ⟨r²⟩ ∝ t^α, 2000 caminantes, 1000 pasos")
    c("msd_coef", float(np.polyfit(t, m, 1)[0]), desc="pendiente de ⟨r²⟩ frente a t (pasos de longitud 1)")
    D["msd"] = (t, m)
    cam = aleatorio.caminata(10 ** 6, 1)
    bcw = dimension.box_counting(dimension.rasterizar(cam, 1024), [2 ** k for k in range(1, 7)])
    c("bc_caminata", bcw["D"], desc="caminata de 10^6 pasos en 1024 px")
    D["caminata"] = cam[:20000]
    a_pol = 0.5e-6
    eta = 1.0e-3
    Tk = 293.15
    Dse = KB * Tk / (6 * math.pi * eta * a_pol)
    c("einstein_D", Dse, desc="Stokes-Einstein: esfera de 0,5 µm en agua a 20 °C (η = 1,0 mPa·s supuesta)")
    c("einstein_t10", (10e-6) ** 2 / (4 * Dse), desc="tiempo para ⟨r²⟩ = (10 µm)² en 2D")
    c("einstein_t1mm", (1e-3) ** 2 / (4 * Dse) / 86400, desc="días para (1 mm)²")

    # ---------------------------------------------------------- 5. difusión anómala
    tc, mc = aleatorio.ctrw_msd(600 if rapido else 1500, 1e5, 0.6, 5)
    ec = aleatorio.exponente_msd(tc, mc)
    c("ctrw_alfa", ec["alfa"], desc="CTRW con α = 0,6")
    D["ctrw"] = (tc, mc)
    lv = aleatorio.escala_levy(2000, 1000, 1.5, 7)
    c("levy_exp", lv["exponente"], desc="exponente de la mediana, μ = 1,5")
    c("levy_exp_teor", 1 / 1.5, "exacto")
    D["levy_escala"] = (lv["t"], lv["mediana"])
    c("levy_frac_mu1", aleatorio.fraccion_salto_mayor(10 ** 5, 1.0, 4), desc="fracción del salto mayor, μ = 1")
    c("levy_frac_mu15", aleatorio.fraccion_salto_mayor(10 ** 5, 1.5, 4))
    D["levy"] = aleatorio.vuelo_levy(3000, 1.5, 4)
    D["browniano_corto"] = aleatorio.caminata(3000, 3)

    # ---------------------------------------------------------- 6. DLA
    g = dla.dla(1500 if rapido else 5000, 11)
    cc = g.shape[0] // 2
    rg = dla.radio_de_giro(g)
    mr = dimension.masa_radio(g, (cc, cc), np.geomspace(4, rg, 8))
    c("dla_D", mr["D"], desc="masa-radio, 5000 partículas")
    c("dla_r2", mr["r2"])
    c("dla_rg", rg, desc="radio de giro en píxeles")
    c("dla_n", int(g.sum()), "exacto")
    D["dla"] = (g, mr)
    Ds = []
    for s in (21, 22, 23):
        gs = dla.dla(800 if rapido else 3000, s)
        cs_ = gs.shape[0] // 2
        Ds.append(dimension.masa_radio(gs, (cs_, cs_), np.geomspace(4, dla.radio_de_giro(gs), 8))["D"])
    c("dla_D_media", float(np.mean(Ds)), desc="media de tres agregados de 3000 partículas")
    c("dla_D_min", float(np.min(Ds)))
    c("dla_D_max", float(np.max(Ds)))

    # ---------------------------------------------------------- 7. percolación
    ps = np.linspace(0.55, 0.65, 11)
    u64 = percolacion.umbral_por_cruce(64, ps, 60 if rapido else 200, 21)
    u128 = percolacion.umbral_por_cruce(128, ps, 30 if rapido else 100, 24)
    c("pc_64", u64["pc"], desc="cruce 1/2, L = 64, 200 redes por punto")
    c("pc_128", u128["pc"], desc="cruce 1/2, L = 128, 100 redes por punto")
    D["cruce"] = (ps, u64["P"], u128["P"])
    dc = percolacion.dimension_cumulo([32, 64, 128, 256], 0.5927, 10 if rapido else 40, 22)
    c("perc_D", dc["D"], desc="M(L) ∝ L^D del cúmulo mayor en p = 0,5927")
    D["perc_D"] = dc
    rngp = np.random.default_rng(25)
    red = percolacion.red(128, 0.5927, rngp)
    et, n = percolacion.cumulos(red)
    mayor = np.bincount(et.ravel())[1:].argmax() + 1
    D["perc_red"] = (red, et == mayor)
    ps2 = np.linspace(0.5, 0.8, 13)
    D["pinf"] = (ps2, percolacion.fuerza_cumulo_infinito(128, ps2, 5 if rapido else 20, 23))

    # ---------------------------------------------------------- 8. mapa logístico
    f = caos.feigenbaum(11)
    for n_, R in enumerate(f["R"]):
        c(f"R{n_}", R, desc=f"parámetro superestable de periodo 2^{n_}")
    for k, dlt in enumerate(f["deltas"], start=2):
        c(f"delta{k}", dlt)
    c("feig_delta", f["delta"], desc="δ estimada con R_9, R_10, R_11")
    c("feig_alfa", f["alfa"], desc="α estimada")
    c("r_inf", f["r_inf"], desc="r_∞ extrapolado")
    c("lyap_r4", caos.lyapunov_logistico(4.0))
    c("lyap_r35", caos.lyapunov_logistico(3.5))
    c("lyap_r39", caos.lyapunov_logistico(3.9))
    c("lyap_r383", caos.lyapunov_logistico(3.83))
    c("ln2", math.log(2), "exacto")
    D["bif"] = caos.bifurcacion(2.8, 4.0, 900 if not rapido else 400, 500, 150 if not rapido else 60)
    rs = np.linspace(2.8, 4.0, 600 if not rapido else 200)
    D["lyap_curva"] = (rs, np.array([caos.lyapunov_logistico(r, 4000, 300) for r in rs]))

    # ---------------------------------------------------------- 9. Lorenz
    lam = caos.lyapunov_lorenz(200.0 if rapido else 1000.0)
    c("lorenz_lyap", lam, desc="Benettin, 1000 unidades de tiempo, dt = 0,01")
    c("lorenz_lyap_dt", caos.lyapunov_lorenz(200.0 if rapido else 1000.0, 0.005), desc="mismo cálculo con dt = 0,005")
    Lz = caos.lorenz(30000, 0.01)
    radios = np.geomspace(0.5, 4, 10)
    d2 = caos.dimension_correlacion(Lz[::5], radios)
    c("lorenz_D2", d2["D2"], desc="Grassberger-Procaccia, 6000 puntos, r de 0,5 a 4")
    c("lorenz_D2_r2", d2["r2"])
    D["lorenz"] = Lz
    D["lorenz_C"] = d2
    ts, sep = caos.separacion_lorenz(1e-8, 40.0)
    k1 = int(np.argmax(sep > 1.0))
    c("lorenz_t_sep", ts[k1], desc="tiempo hasta que la separación pasa de 10^−8 a 1")
    c("lorenz_t_pred", math.log(1e8) / lam, desc="ln(10^8)/λ")
    D["sep"] = (ts, sep)

    # ---------------------------------------------------------- 10. turbulencia
    u = turbulencia.senal_k41(2 ** 16, -5 / 3, 31)
    pe = turbulencia.pendiente_espectro(u)
    c("k41_pend", pe["pendiente"], desc="pendiente del espectro de la señal sintética")
    c("k41_teor", -5 / 3, "exacto")
    D["espectro"] = turbulencia.espectro(u)
    med = turbulencia.cascada_p(16, 0.7, 32)
    tq = turbulencia.tau_q(med, [0, 2, 3, 4, -1])
    for q in (2, 3, 4):
        c(f"Dq{q}_sim", tq[q] / (q - 1), desc=f"D_{q} de la cascada simulada")
        c(f"Dq{q}_teor", turbulencia.dq_teorico(q, 0.7), "exacto")
    c("D1_teor", turbulencia.dq_teorico(1, 0.7), "exacto")
    for p in (1, 2, 3, 4, 6, 8):
        c(f"zeta{p}", turbulencia.zeta_p_modelo(p, 0.7), "exacto", f"ζ_{p} del modelo p (p = 0,7)")
        c(f"zeta{p}_k41", p / 3, "exacto")
    c("intermit6", 2 - turbulencia.zeta_p_modelo(6, 0.7), "exacto", "corrección de intermitencia μ = 2 − ζ_6")
    D["cascada"] = med
    D["zetas"] = ([1, 2, 3, 4, 5, 6, 7, 8], [turbulencia.zeta_p_modelo(p, 0.7) for p in range(1, 9)])
    nu, eps, Lint = 1.0e-6, 1.0e-3, 0.1
    eta_k = (nu ** 3 / eps) ** 0.25
    c("kolm_eta", eta_k * 1e3, "calculado", "η en mm, con ν = 10^−6 m²/s y ε = 10^−3 W/kg (supuestos)")
    c("kolm_ratio", Lint / eta_k, desc="L/η con L = 0,1 m")
    c("kolm_grados", (Lint / eta_k) ** 3, desc="(L/η)^3")

    # ---------------------------------------------------------- 11. cálculo fraccionario
    h = 0.01
    tt = np.arange(0, 1 + h / 2, h)
    c("caputo_l1", fraccionario.derivada_caputo_l1(tt ** 2, h, 0.5)[-1], desc="D^½ t² en t = 1 por L1, h = 0,01")
    c("caputo_exacta", fraccionario.caputo_potencia(1.0, 2, 0.5), "exacto", "Γ(3)/Γ(2,5)")
    c("gl_valor", fraccionario.derivada_gl(tt ** 2, h, 0.5)[-1], desc="Grünwald-Letnikov, h = 0,01")
    c("caputo_err_rel", abs(C["caputo_l1"]["v"] / C["caputo_exacta"]["v"] - 1) * 100, desc="error relativo en %")
    tr, yr = fraccionario.relajacion(0.6, 1.0, 2.0, 400)
    ml = float(fraccionario.mittag_leffler(0.6, -(2.0 ** 0.6)))
    c("relaj_num", yr[-1], desc="L1 implícito, α = 0,6, λ = 1, t = 2")
    c("relaj_ml", ml, desc="E_0,6(−2^0,6) por su serie")
    c("relaj_exp", math.exp(-2.0), "exacto", "e^−2 (relajación ordinaria)")
    D["relaj"] = {a: fraccionario.relajacion(a, 1.0, 5.0, 300) for a in (0.4, 0.7, 1.0)}
    for a in (0.5, 0.8, 1.0):
        r = fraccionario.difusion_fraccionaria(a)
        clave = str(a).replace(".", "")
        c(f"fdif_alfa{clave}", r["alfa_ajustado"], desc=f"α ajustado, ecuación con α = {a}")
        c(f"fdif_coef{clave}", r["coef_ajustado"])
        c(f"fdif_coefteor{clave}", r["coef_teorico"], "exacto", "2K/Γ(1 + α)")
        D[f"fdif{clave}"] = r

    # ---------------------------------------------------------- 12. porosos y rugosidad
    for n_ in (1, 3, 5):
        c(f"por_alf{n_}", porosos.porosidad_alfombra(n_), "exacto")
        c(f"por_men{n_}", porosos.porosidad_menger(n_), "exacto")
    q = porosos.caudal_darcy(1.0e-13, 0.01, 2.0e5, 0.5, 1.0e-3)
    c("darcy_q", q * 1e6 * 60, desc="caudal en mL/min: k = 10^−13 m², A = 0,01 m², ΔP = 2 bar, L = 0,5 m, μ = 1 mPa·s")
    fis = np.array([0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0])
    kr = porosos.permeabilidad_frente_porosidad(48, fis, 3 if rapido else 10, 41)
    D["perm"] = (fis, kr)
    c("krel_07", float(kr[3]), desc="permeabilidad relativa con porosidad 0,7")
    c("krel_06", float(kr[1]))
    c("krel_09", float(kr[7]))
    z = porosos.superficie_fbm(512, 0.7, 42)
    hv = porosos.hurst_variograma(z)
    c("sup_H", hv["H"], desc="H estimado por variograma, H de síntesis 0,7")
    c("sup_D", hv["D"])
    D["superficie"] = z

    # ---------------------------------------------------------- 13. antenas
    c("monopolo_24", antenas.monopolo_cuarto_onda(2.4e9) * 1000, "calculado", "λ/4 a 2,4 GHz en mm")
    c("monopolo_09", antenas.monopolo_cuarto_onda(0.9e9) * 1000, "calculado", "λ/4 a 900 MHz en mm")
    c("koch_long3", antenas.longitud_koch(3), "exacto")
    c("koch_long4", antenas.longitud_koch(4), "exacto")
    c("sierp_area4", antenas.area_sierpinski(4), "exacto")
    c("sierp_perim4", antenas.perimetro_sierpinski(4), "exacto")
    c("bandas_razon", 2.0, "exacto")

    # ---------------------------------------------------------- 14. Kleiber, costas
    ew = biologia.exponente_wbe(range(10, 31, 2))
    c("wbe_exp", ew["exponente"], desc="exponente de N_c frente a V_b, redes de 10 a 30 niveles")
    for N in (5, 10, 20, 40):
        c(f"wbe_local{N}", biologia.exponente_local_wbe(N))
    D["wbe"] = (np.arange(3, 41), [biologia.exponente_local_wbe(N) for N in range(3, 41)])
    ratio = 4000 / 0.02
    c("masa_ratio", ratio, "exacto", "elefante 4000 kg / ratón 20 g")
    c("met_ratio_075", biologia.cociente_metabolico(0.02, 4000, 0.75))
    c("met_ratio_067", biologia.cociente_metabolico(0.02, 4000, 2 / 3))
    c("met_ratio_dif", C["met_ratio_075"]["v"] / C["met_ratio_067"]["v"])
    costa = biologia.costa_autoafin(2 ** 14, 0.6, 51)
    rd = dimension.regla_divisores(costa, np.geomspace(0.002, 0.05, 8))
    c("costa_D", rd["D"], desc="regla de divisores sobre costa sintética de H = 0,6")
    c("costa_D_teor", 2 - 0.6, "exacto", "dimensión de caja de la gráfica, 2 − H")
    D["costa"] = (costa, rd)
    rdk = dimension.regla_divisores(conjuntos.koch(7), [3 ** -k for k in range(2, 6)])
    c("koch_divisores", rdk["D"], desc="regla de divisores sobre Koch nivel 7")

    # ---------------------------------------------------------- 15. Hurst
    for H in (0.3, 0.5, 0.7):
        xx = aleatorio.fgn(2 ** 14, H, 6)
        clave = str(H).replace(".", "")
        c(f"hrs_{clave}", series.hurst_rs(xx)["H"], desc=f"R/S sobre fGn de H = {H}, 16 384 datos")
        c(f"dfa_{clave}", series.dfa(xx)["alfa"], desc=f"DFA sobre fGn de H = {H}")
        D[f"dfa_{clave}"] = series.dfa(xx)
    gr = series.rendimientos_garch(2 ** 14, 8)
    c("garch_dfa", series.dfa(gr)["alfa"], desc="DFA de rendimientos GARCH(1,1)")
    c("garch_abs_dfa", series.dfa(np.abs(gr))["alfa"], desc="DFA de |rendimientos|")
    corto = aleatorio.fgn(512, 0.5, 9)
    c("hrs_corto", series.hurst_rs(corto)["H"], desc="R/S con 512 datos, H = 0,5")
    c("dfa_corto", series.dfa(corto)["alfa"])

    # ---------------------------------------------------------- 16. IA: verificación de afirmaciones
    v1 = ia.verificar_afirmacion("dimension_koch", 1.5)
    v2 = ia.verificar_afirmacion("feigenbaum_delta", 4.67)
    c("ia_koch_falso", 1.5, "supuesto", "cifra errónea de ejemplo")
    c("ia_delta_afirmado", 4.67, "supuesto")
    c("ia_koch_ok", 1.0 if v1["estado"] == "coincide" else 0.0)
    c("ia_delta_ok", 1.0 if v2["estado"] == "coincide" else 0.0)

    # ---------------------------------------------------------- soluciones de los ejercicios
    c("pot_10_15", 10 ** 1.5, "exacto", "10^1,5")
    Lc = np.geomspace(0.1, 0.3, 12)
    Tc = 2 * math.pi * np.sqrt(Lc / 9.81) * (1 + 0.02 * np.random.default_rng(101).standard_normal(12))
    ajc = dimension.ajuste_loglog(Lc, Tc)
    c("pendulo_corto_exp", ajc["pendiente"], desc="exponente con L de 0,1 a 0,3 m")
    c("pendulo_corto_err", ajc["error_pendiente"], desc="error típico del exponente con L de 0,1 a 0,3 m")
    c("pendulo_err_ratio", ajc["error_pendiente"] / aj["error_pendiente"])
    c("cantor_n20", 2 ** 20, "exacto")
    c("cantor_n7", 2 ** 7, "exacto"); c("cantor_long7", (2 / 3) ** 7, "exacto")
    c("sierp_area6", antenas.area_sierpinski(6), "exacto")
    c("met_caballo_075", biologia.cociente_metabolico(4, 500, 0.75), desc="caballo 500 kg / gato 4 kg")
    c("met_caballo_067", biologia.cociente_metabolico(4, 500, 2 / 3))
    c("pies_m", 22 * 0.3048, "exacto", "22 pies en metros")
    c("masa_caballo_gato", 500 / 4, "exacto")
    Ds2 = []
    for s_ in (31, 32, 33):
        gs = dla.dla(600 if rapido else 2000, s_)
        cs_ = gs.shape[0] // 2
        Ds2.append(dimension.masa_radio(gs, (cs_, cs_), np.geomspace(4, dla.radio_de_giro(gs), 8))["D"])
    c("dla2_D_media", float(np.mean(Ds2)), desc="semillas 31-33, 2000 partículas")
    c("dla2_D_min", float(np.min(Ds2))); c("dla2_D_max", float(np.max(Ds2)))
    hr, hd = [], []
    for s_ in range(100, 100 + (10 if rapido else 50)):
        xx = aleatorio.fgn(512, 0.5, s_)
        hr.append(series.hurst_rs(xx)["H"]); hd.append(series.dfa(xx)["alfa"])
    c("hrs_512_media", float(np.mean(hr)), desc="R/S, 512 datos, H = 0,5, 50 semillas")
    c("hrs_512_sd", float(np.std(hr, ddof=1)))
    c("dfa_512_media", float(np.mean(hd))); c("dfa_512_sd", float(np.std(hd, ddof=1)))
    c("D_caos_04", dimension.dimension_semejanza(3, 0.4), "exacto", "log 3 / log 2,5")
    p04 = conjuntos.juego_del_caos(200_000, 1, razon=0.6)     # salto del 60 % = contracción 0,4
    c("bc_caos_04", dimension.box_counting(dimension.rasterizar(p04, 1024), [2 ** k for k in range(1, 7)])["D"])
    c("K_3d", 1 / 6, "exacto", "⟨r²⟩ = 6Kt = t")
    t2, m2 = aleatorio.msd_conjunto(200, 1000, 2)
    c("msd_alfa_200", aleatorio.exponente_msd(t2, m2, 10)["alfa"], desc="200 caminantes")
    c("ej_ctrw_100", 100 ** 0.5, "exacto")
    c("ej_levy_12", 1 / 1.2, "exacto")
    c("ej_fbm_03", 2 * 0.3, "exacto", "α = 2H")
    c("ej_fbm_08", 2 * 0.8, "exacto")
    c("ej_dla_200", 2500 * 2 ** 1.71, "calculado", "2500 · 2^1,71")
    c("D_perc_frac", 91 / 48, "exacto")
    c("xi_factor", 10 ** (4 / 3), "exacto")
    u32 = percolacion.umbral_por_cruce(32, ps, 60 if rapido else 200, 26)
    c("pc_32", u32["pc"], desc="cruce 1/2, L = 32")
    c("pred_r4", math.log(1e8) / math.log(2), "exacto", "ln(10^8)/ln 2")
    c("ej_lorenz_hor", math.log(1000) / 0.9056, "calculado", "ln(1000)/λ con λ = 0,9056 publicado")
    c("lorenz_D2_2000", caos.dimension_correlacion(Lz[::15], radios, max_puntos=2000)["D2"], desc="2000 puntos")
    c("eta_factor", 16 ** -0.25, "exacto")
    c("ej_frac_t", math.gamma(2) / math.gamma(1.5), "exacto", "Γ(2)/Γ(1,5)")
    c("ej_frac_msd4", 2 * 4 ** 0.5 / math.gamma(1.5), "exacto", "2·4^0,5/Γ(1,5)")
    r100 = fraccionario.difusion_fraccionaria(0.5, nt=100)
    c("fdif_alfa05_100", r100["alfa_ajustado"], desc="α = 0,5 con 100 pasos")
    c("darcy_q2", C["darcy_q"]["v"] / 2)
    c("ej_sup_D04", 3 - 0.4, "exacto"); c("ej_sup_D08", 3 - 0.8, "exacto")
    c("ej_koch_3cm", 3 * antenas.longitud_koch(4), "exacto", "cm")
    c("ej_banda2", 0.9 * 2, "exacto"); c("ej_banda3", 0.9 * 4, "exacto")
    c("ej_costa", 2000 * 10 ** 0.25, "calculado", "2000 km · 10^(D − 1)")
    c("ej_fbm_sd08", 100 ** 0.8, "exacto"); c("ej_fbm_sd05", 100 ** 0.5, "exacto")
    c("ej_fbm_dim01", 2 - 0.1, "exacto")
    for H in (0.3, 0.5, 0.7):
        xx = aleatorio.fgn(2048, H, 6)
        clave = str(H).replace(".", "")
        c(f"hrs_{clave}_2048", series.hurst_rs(xx)["H"]); c(f"dfa_{clave}_2048", series.dfa(xx)["alfa"])
    e16 = [abs(C[f"hrs_{k}"]["v"] - h) for k, h in (("03", .3), ("05", .5), ("07", .7))]
    e16d = [abs(C[f"dfa_{k}"]["v"] - h) for k, h in (("03", .3), ("05", .5), ("07", .7))]
    e2 = [abs(C[f"hrs_{k}_2048"]["v"] - h) for k, h in (("03", .3), ("05", .5), ("07", .7))]
    e2d = [abs(C[f"dfa_{k}_2048"]["v"] - h) for k, h in (("03", .3), ("05", .5), ("07", .7))]
    c("err_rs_16k", float(np.mean(e16)), desc="error absoluto medio de R/S con 16 384 datos")
    c("err_dfa_16k", float(np.mean(e16d))); c("err_rs_2k", float(np.mean(e2))); c("err_dfa_2k", float(np.mean(e2d)))
    v3 = ia.verificar_afirmacion("umbral_percolacion_cuadrada", 0.5)
    c("ia_pc_ok", 1.0 if v3["estado"] == "coincide" else 0.0)
    c("ia_pc_sim", v3["simulador"])
    from .figuras import NOMBRES
    c("n_figuras", len(NOMBRES), "exacto")
    c("n_cifras", len(C) + 1, "exacto", "número de cifras que calcula esta función")
    return C, D
