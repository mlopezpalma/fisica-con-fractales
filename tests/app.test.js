// Pruebas de docs/fractales.js con Node (sin dependencias): node tests/app.test.js
"use strict";
const F = require("../docs/fractales.js");
let fallos = 0;
function cerca(nombre, v, esperado, tol) {
  const ok = Math.abs(v - esperado) <= tol;
  if (!ok) fallos++;
  console.log((ok ? "OK " : "NO ") + nombre + ": " + v.toFixed(5) + " (esperado " + esperado.toFixed(5) + " ± " + tol + ")");
}
const s = F.sierpinskiMascara(8);
cerca("conteo de cajas de Sierpinski", F.boxCounting(s.mascara, s.ancho, s.alto).D, Math.log(3) / Math.log(2), 1e-6);
cerca("semejanza de Koch", F.semejanza(4, 1 / 3), Math.log(4) / Math.log(3), 1e-12);
const k = F.koch(4);
let L = 0; for (let i = 1; i < k.length; i++) L += Math.hypot(k[i][0] - k[i - 1][0], k[i][1] - k[i - 1][1]);
cerca("longitud de Koch nivel 4", L, Math.pow(4 / 3, 4), 1e-9);
cerca("Lyapunov logístico r = 4", F.lyapunovLogistico(4, 200000), Math.log(2), 0.01);
cerca("Lyapunov de Lorenz", F.lyapunovLorenz(200, 0.01), 0.9056, 0.05);
const m = F.msdBrowniano(500, 500, 2);
cerca("exponente browniano", F.exponente(m.t, m.msd, 10).pendiente, 1, 0.05);
const c = F.ctrwMsd(300, 1e4, 0.5, 5);
cerca("exponente CTRW α = 0,5", F.exponente(c.t, c.msd).pendiente, 0.5, 0.12);
const lv = F.medianaLevy(500, 300, 1.5, 7);
cerca("Lévy μ = 1,5", F.exponente(lv.t, lv.mediana, 10).pendiente, 1 / 1.5, 0.07);
const d = new F.DLA(401, 11); d.anadir(1500);
cerca("DLA dimensión de masa", d.dimension().D, 1.71, 0.15);
const ps = []; for (let i = 0; i <= 10; i++) ps.push(0.55 + 0.01 * i);
cerca("umbral de percolación L = 32", F.umbralCruce(ps, F.probCruce(32, ps, 60, 21)), 0.5927, 0.03);
cerca("Γ(2,5)", F.gamma(2.5), 1.329340388, 1e-8);
const df = F.difusionFraccionaria(0.6, { nt: 150 });
cerca("difusión fraccionaria α", df.alfaAjustado, 0.6, 0.03);
cerca("difusión fraccionaria coeficiente", df.coefAjustado / df.coefTeorico, 1, 0.03);
const txt = F.explicacionLocal("prueba", { D: 1.26 });
if (!txt.includes("Modo sin clave")) { fallos++; console.log("NO explicación local"); } else console.log("OK explicación local");
console.log(fallos ? fallos + " fallos" : "todas las pruebas de JavaScript pasan");
process.exit(fallos ? 1 : 0);
