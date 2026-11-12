"""Pruebas con verdad conocida: cada función del paquete se compara con un resultado exacto o publicado."""
import math

import numpy as np
import pytest

from fractales_fisica import (aleatorio, antenas, biologia, caos, conjuntos, dimension, dla, fraccionario, ia, percolacion,
                              porosos, series, turbulencia)


# ------------------------------------------------------------- dimensión y conjuntos
@pytest.mark.parametrize("n,r,esperado", [(2, 1 / 3, math.log(2) / math.log(3)), (4, 1 / 3, math.log(4) / math.log(3)),
                                          (3, 1 / 2, math.log(3) / math.log(2)), (8, 1 / 3, math.log(8) / math.log(3))])
def test_dimension_semejanza(n, r, esperado):
    assert dimension.dimension_semejanza(n, r) == pytest.approx(esperado)


def test_dimension_semejanza_rechaza_razon_invalida():
    with pytest.raises(ValueError):
        dimension.dimension_semejanza(2, 1.5)


def test_box_counting_sierpinski_exacto():
    r = dimension.box_counting(conjuntos.sierpinski(8))
    assert r["D"] == pytest.approx(math.log(3) / math.log(2), abs=1e-6)


def test_box_counting_alfombra_con_cajas_de_tres():
    r = dimension.box_counting(conjuntos.alfombra(5), [3 ** k for k in range(4)])
    assert r["D"] == pytest.approx(math.log(8) / math.log(3), abs=1e-6)


def test_box_counting_cuadrado_lleno_da_2():
    assert dimension.box_counting(np.ones((256, 256), bool))["D"] == pytest.approx(2.0, abs=1e-9)


def test_box_counting_recta_da_1():
    img = np.zeros((256, 256), bool)
    img[128, :] = True
    assert dimension.box_counting(img)["D"] == pytest.approx(1.0, abs=1e-9)


def test_cantor_longitud():
    tramos = conjuntos.cantor(5)
    assert len(tramos) == 32
    assert sum(b - a for a, b in tramos) == pytest.approx((2 / 3) ** 5)


def test_koch_numero_de_segmentos_y_longitud():
    p = conjuntos.koch(4)
    assert len(p) == 4 ** 4 + 1
    assert np.hypot(*np.diff(p, axis=0).T).sum() == pytest.approx((4 / 3) ** 4)


def test_regla_divisores_koch_cerca_de_teorica():
    r = dimension.regla_divisores(conjuntos.koch(7), [3.0 ** -k for k in range(2, 6)])
    assert r["D"] == pytest.approx(math.log(4) / math.log(3), abs=0.06)


def test_mandelbrot_puntos_conocidos():
    m = conjuntos.mandelbrot(3, 3, (-1, 1), (-1, 1), max_iter=50)
    assert m[1, 1] == 50          # c = 0 no escapa
    assert m[0, 2] < 50           # c = 1 − i escapa


# ------------------------------------------------------------- caos
def test_feigenbaum_delta_y_alfa():
    f = caos.feigenbaum(11)
    assert f["delta"] == pytest.approx(4.669201609, abs=2e-6)
    assert f["alfa"] == pytest.approx(2.502907875, abs=2e-6)
    assert f["r_inf"] == pytest.approx(3.569945672, abs=1e-8)


def test_lyapunov_logistico_r4_es_ln2():
    assert caos.lyapunov_logistico(4.0) == pytest.approx(math.log(2), abs=0.01)


def test_lyapunov_logistico_negativo_en_periodo_2():
    assert caos.lyapunov_logistico(3.2) < 0


def test_lyapunov_lorenz_cerca_de_publicado():
    assert caos.lyapunov_lorenz(300.0) == pytest.approx(0.9056, abs=0.03)


def test_dimension_correlacion_lorenz():
    L = caos.lorenz(20000, 0.01)
    r = caos.dimension_correlacion(L[::5], np.geomspace(0.5, 4, 8), max_puntos=2000)
    assert r["D2"] == pytest.approx(2.05, abs=0.08)


# ------------------------------------------------------------- difusión
def test_msd_difusion_normal():
    t, m = aleatorio.msd_conjunto(1000, 500, 2)
    assert aleatorio.exponente_msd(t, m, 10)["alfa"] == pytest.approx(1.0, abs=0.03)
    assert m[-1] / t[-1] == pytest.approx(1.0, abs=0.1)


def test_ctrw_subdifusiva():
    t, m = aleatorio.ctrw_msd(400, 1e4, 0.5, 5)
    assert aleatorio.exponente_msd(t, m)["alfa"] == pytest.approx(0.5, abs=0.1)


def test_levy_escala_1_entre_mu():
    r = aleatorio.escala_levy(1000, 500, 1.5, 7)
    assert r["exponente"] == pytest.approx(1 / 1.5, abs=0.05)


def test_fgn_varianza_y_hurst():
    x = aleatorio.fgn(2 ** 14, 0.7, 6)
    assert x.std() == pytest.approx(1.0, abs=0.1)
    assert series.dfa(x)["alfa"] == pytest.approx(0.7, abs=0.05)


def test_fgn_rechaza_h_fuera_de_rango():
    with pytest.raises(ValueError):
        aleatorio.fgn(100, 1.2)


# ------------------------------------------------------------- DLA y percolación
def test_dla_dimension_masa_radio():
    g = dla.dla(1500, 11)
    c = g.shape[0] // 2
    r = dimension.masa_radio(g, (c, c), np.geomspace(4, dla.radio_de_giro(g), 8))
    assert g.sum() == 1500
    assert 1.55 < r["D"] < 1.85


def test_percolacion_cumulos_conocidos():
    red = np.array([[1, 1, 0], [0, 0, 0], [1, 0, 1]], bool)
    et, n = percolacion.cumulos(red)
    assert n == 3
    assert percolacion.cruza(np.array([[1, 0], [1, 0]], bool))
    assert not percolacion.cruza(np.array([[1, 0], [0, 1]], bool))


def test_umbral_percolacion_cerca_de_referencia():
    r = percolacion.umbral_por_cruce(48, np.linspace(0.55, 0.65, 11), 60, 21)
    assert r["pc"] == pytest.approx(0.5927, abs=0.015)


# ------------------------------------------------------------- turbulencia
def test_cascada_dq_igual_a_teorica():
    tq = turbulencia.tau_q(turbulencia.cascada_p(14, 0.7, 1), [2, 3])
    for q in (2, 3):
        assert tq[q] / (q - 1) == pytest.approx(turbulencia.dq_teorico(q, 0.7), abs=1e-9)


def test_zeta3_es_1_para_cualquier_p():
    for p in (0.5, 0.6, 0.7, 0.9):
        assert turbulencia.zeta_p_modelo(3, p) == pytest.approx(1.0)


def test_espectro_k41():
    u = turbulencia.senal_k41(2 ** 14, -5 / 3, 3)
    assert turbulencia.pendiente_espectro(u)["pendiente"] == pytest.approx(-5 / 3, abs=0.02)


# ------------------------------------------------------------- cálculo fraccionario
def test_caputo_de_una_potencia():
    h = 0.005
    t = np.arange(0, 1 + h / 2, h)
    d = fraccionario.derivada_caputo_l1(t ** 2, h, 0.5)[-1]
    assert d == pytest.approx(fraccionario.caputo_potencia(1.0, 2, 0.5), rel=1e-3)


def test_mittag_leffler_alfa_1_es_exponencial():
    z = np.array([-2.0, -0.5, 0.0, 1.0])
    assert np.allclose(fraccionario.mittag_leffler(1.0, z), np.exp(z))


def test_relajacion_coincide_con_mittag_leffler():
    _, y = fraccionario.relajacion(0.6, 1.0, 2.0, 400)
    assert y[-1] == pytest.approx(float(fraccionario.mittag_leffler(0.6, -(2.0 ** 0.6))), abs=2e-3)


def test_difusion_fraccionaria_exponente_y_coeficiente():
    r = fraccionario.difusion_fraccionaria(0.7, nt=200)
    assert r["alfa_ajustado"] == pytest.approx(0.7, abs=0.02)
    assert r["coef_ajustado"] == pytest.approx(r["coef_teorico"], rel=0.02)


def test_thomas_resuelve_tridiagonal():
    n = 6
    inf, diag, sup = np.full(n, -1.0), np.full(n, 4.0), np.full(n, -1.0)
    A = np.diag(diag) + np.diag(sup[:-1], 1) + np.diag(inf[1:], -1)
    b = np.arange(1.0, n + 1)
    assert np.allclose(fraccionario.thomas(inf, diag, sup, b), np.linalg.solve(A, b))


# ------------------------------------------------------------- porosos, antenas, biología
def test_permeabilidad_red_abierta_y_cerrada():
    assert porosos.permeabilidad_red(np.ones((16, 16), bool)) == pytest.approx(1.0, abs=1e-6)
    cerrada = np.ones((16, 16), bool)
    cerrada[:, 8] = False
    assert porosos.permeabilidad_red(cerrada) == pytest.approx(0.0, abs=1e-9)


def test_darcy():
    assert porosos.caudal_darcy(1e-12, 1.0, 1e5, 1.0, 1e-3) == pytest.approx(1e-4)


def test_superficie_hurst():
    assert porosos.hurst_variograma(porosos.superficie_fbm(256, 0.7, 1))["H"] == pytest.approx(0.7, abs=0.06)


def test_antenas_geometria():
    assert antenas.monopolo_cuarto_onda(2.4e9) == pytest.approx(0.031228, rel=1e-4)
    assert antenas.longitud_koch(2) == pytest.approx(16 / 9)
    assert antenas.area_sierpinski(2) == pytest.approx(9 / 16)


def test_wbe_tiende_a_tres_cuartos():
    assert biologia.exponente_local_wbe(40) == pytest.approx(0.75, abs=1e-3)
    assert biologia.exponente_local_wbe(5) < 0.75


# ------------------------------------------------------------- IA (sin red)
def test_ia_modo_sin_clave(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    txt = ia.explicar("dimension", {"D": 1.26, "r2": 0.999})
    assert "Modo sin clave" in txt and "Comprobaciones" in txt


def test_ia_verificar_afirmacion():
    assert ia.verificar_afirmacion("dimension_koch", 1.5)["estado"] == "NO coincide"
    assert ia.verificar_afirmacion("dimension_koch", 1.2619)["estado"] == "coincide"
    assert ia.verificar_afirmacion("no_existe", 1.0)["estado"] == "desconocida"


def test_ia_modelo_y_clave_solo_de_entorno():
    import inspect
    fuente = inspect.getsource(ia)
    assert ia.MODELO == "claude-sonnet-5-5"
    assert "os.environ.get(\"ANTHROPIC_API_KEY\"" in fuente
    assert "open(" not in fuente     # el módulo no escribe archivos


def test_linea_de_ordenes(capsys):
    from fractales_fisica.__main__ import main
    assert main(["sierpinski", "--nivel", "7"]) == 0
    assert "D_teorica" in capsys.readouterr().out
