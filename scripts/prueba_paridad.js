#!/usr/bin/env node
/*
 * Prueba de paridad: la predicción en JavaScript debe coincidir con scikit-learn.
 *
 * Uso:  node scripts/prueba_paridad.js [web/modelo.js] [casos_extra.json]
 *
 * 1. Carga modelo.js y motor.js igual que el navegador. motor.js es el código que
 *    usa la página para predecir; se busca en la misma carpeta que modelo.js.
 * 2. Recalcula cada caso de prueba con ese motor.
 * 3. Compara con la predicción de scikit-learn guardada al exportar.
 * 4. Revisa que los aportes de la gráfica sumen la estimación.
 *
 * Termina con código 1 si alguna diferencia supera la tolerancia (1e-6).
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var TOLERANCIA = 1e-6;
var rutaModelo = process.argv[2] || path.join(__dirname, '..', 'web', 'modelo.js');
var rutaExtra = process.argv[3];

function rutaMotor() {
  var junto = path.join(path.dirname(rutaModelo), 'motor.js');
  if (fs.existsSync(junto)) return junto;
  return path.join(__dirname, '..', 'web', 'motor.js');
}

// Un contexto como el del navegador: los dos archivos escriben en window.
var contexto = { window: {} };
vm.createContext(contexto);
[rutaMotor(), rutaModelo].forEach(function (ruta) {
  vm.runInContext(fs.readFileSync(ruta, 'utf8'), contexto, { filename: ruta });
});
var motor = contexto.window.MotorModelo;
var modelo = contexto.window.MODELO;
if (!motor) throw new Error('motor.js no definió window.MotorModelo');
if (!modelo) throw new Error(rutaModelo + ' no definió window.MODELO');

function desconocidas(caso) {
  // Respuestas de texto que no están entre las categorías del modelo.
  return modelo.variables.filter(function (v) {
    return v.tipo !== 'numero' && !motor.categoria(v, caso.entradas[v.nombre]);
  }).length;
}

function comparar(casos) {
  var resumen = { n: casos.length, maxDif: 0, fallos: 0, desconocidas: 0 };
  casos.forEach(function (caso) {
    resumen.desconocidas += desconocidas(caso);
    var dif = Math.abs(motor.predecir(modelo, caso.entradas) - caso.prediccion_sklearn);
    if (dif > resumen.maxDif) resumen.maxDif = dif;
    if (!(dif <= TOLERANCIA)) resumen.fallos += 1;
  });
  return resumen;
}

function formato(numero) {
  return numero.toFixed(6).padStart(12);
}

var ok = true;
var tipo = modelo.tipo === 'arboles' ? modelo.arboles.lista.length + ' árboles' : 'lineal';
console.log('Modelo ' + modelo.version + (modelo.periodo ? ' · periodo ' + modelo.periodo : '') +
            ' · ' + tipo + ' · ' + modelo.variables.length + ' variables');
console.log('Caso       sklearn   JavaScript    diferencia');
modelo.casos_prueba.forEach(function (caso) {
  var js = motor.predecir(modelo, caso.entradas);
  var dif = Math.abs(js - caso.prediccion_sklearn);
  console.log(String(caso.id).padStart(4) + ' ' + formato(caso.prediccion_sklearn) + ' ' +
              formato(js) + '  ' + dif.toExponential(2));
});

var casos = comparar(modelo.casos_prueba);
console.log('Casos de modelo.js: ' + casos.n + ', diferencia máxima ' +
            casos.maxDif.toExponential(2) + ', fuera de tolerancia: ' + casos.fallos);
if (casos.fallos > 0 || casos.desconocidas > 0) ok = false;

if (rutaExtra) {
  var extra = comparar(JSON.parse(fs.readFileSync(rutaExtra, 'utf8')));
  console.log('Casos extra del set de prueba: ' + extra.n + ', diferencia máxima ' +
              extra.maxDif.toExponential(2) + ', fuera de tolerancia: ' + extra.fallos);
  if (extra.fallos > 0) ok = false;
}

// La gráfica de aportes muestra: punto de partida + aportes = estimación.
// Si esto falla, las barras no cuadrarían con el número del medidor.
var maxSuma = 0;
modelo.casos_prueba.forEach(function (caso) {
  var e = motor.explicar(modelo, caso.entradas);
  var suma = e.partida;
  Object.keys(e.aportes).forEach(function (k) { suma += e.aportes[k]; });
  maxSuma = Math.max(maxSuma, Math.abs(suma - e.estimacion));
});
console.log('Punto de partida + aportes = estimación: diferencia máxima ' + maxSuma.toExponential(2));
if (!(maxSuma <= TOLERANCIA)) ok = false;

console.log(ok ? 'OK: JavaScript y scikit-learn coinciden (tolerancia 1e-6).'
               : 'ERROR: la paridad falló.');
process.exit(ok ? 0 : 1);
