#!/usr/bin/env node
/*
 * Prueba de paridad: la predicción en JavaScript debe coincidir con scikit-learn.
 *
 * Uso:  node scripts/prueba_paridad.js [web/modelo.js] [casos_extra.json]
 *
 * 1. Carga modelo.js igual que el navegador (el archivo define window.MODELO).
 * 2. Recalcula cada caso con la misma fórmula de web/index.html:
 *    intercepto + suma de los coeficientes de las categorías elegidas.
 * 3. Compara con la predicción de scikit-learn guardada al exportar.
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

function cargarModelo(ruta) {
  var contexto = { window: {} };
  vm.createContext(contexto);
  vm.runInContext(fs.readFileSync(ruta, 'utf8'), contexto, { filename: ruta });
  if (!contexto.window.MODELO) {
    throw new Error(ruta + ' no definió window.MODELO');
  }
  return contexto.window.MODELO;
}

// Misma función que usa web/index.html.
function predecir(modelo, respuestas) {
  var total = modelo.intercepto;
  modelo.variables.forEach(function (variable) {
    var valor = respuestas[variable.nombre];
    var categoria = variable.categorias.find(function (c) { return c.valor === valor; });
    if (categoria) total += categoria.coeficiente; // categoría desconocida: aporta 0
  });
  return total;
}

function comparar(modelo, casos) {
  var resumen = { n: casos.length, maxDif: 0, fallos: 0, desconocidas: 0 };
  casos.forEach(function (caso) {
    modelo.variables.forEach(function (variable) {
      var valor = caso.entradas[variable.nombre];
      var existe = variable.categorias.some(function (c) { return c.valor === valor; });
      if (!existe) resumen.desconocidas += 1;
    });
    var dif = Math.abs(predecir(modelo, caso.entradas) - caso.prediccion_sklearn);
    if (dif > resumen.maxDif) resumen.maxDif = dif;
    if (!(dif <= TOLERANCIA)) resumen.fallos += 1;
  });
  return resumen;
}

function formato(numero) {
  return numero.toFixed(6).padStart(12);
}

var modelo = cargarModelo(rutaModelo);
var ok = true;

console.log('Modelo ' + modelo.version + ' · periodo ' + modelo.periodo +
            ' · ' + modelo.variables.length + ' variables');
console.log('Caso      sklearn   JavaScript    diferencia');
modelo.casos_prueba.forEach(function (caso) {
  var js = predecir(modelo, caso.entradas);
  var dif = Math.abs(js - caso.prediccion_sklearn);
  console.log(String(caso.id).padStart(4) + formato(caso.prediccion_sklearn) + ' ' +
              formato(js) + '  ' + dif.toExponential(2));
});

var casos = comparar(modelo, modelo.casos_prueba);
console.log('Casos de modelo.js: ' + casos.n + ', diferencia máxima ' +
            casos.maxDif.toExponential(2) + ', fuera de tolerancia: ' + casos.fallos);
if (casos.fallos > 0 || casos.desconocidas > 0) ok = false;

if (rutaExtra) {
  var extra = comparar(modelo, JSON.parse(fs.readFileSync(rutaExtra, 'utf8')));
  console.log('Casos extra del set de prueba: ' + extra.n + ', diferencia máxima ' +
              extra.maxDif.toExponential(2) + ', fuera de tolerancia: ' + extra.fallos);
  if (extra.fallos > 0) ok = false;
}

// La gráfica de contribuciones usa: intercepto + suma(frecuencia x coeficiente)
// = promedio del entrenamiento. Si esto falla, la gráfica no cuadraría.
var base = modelo.intercepto;
modelo.variables.forEach(function (variable) {
  variable.categorias.forEach(function (c) { base += c.frecuencia * c.coeficiente; });
});
var difBase = Math.abs(base - modelo.promedio_entrenamiento);
console.log('Identidad del promedio: diferencia ' + difBase.toExponential(2));
if (!(difBase <= TOLERANCIA)) ok = false;

console.log(ok ? 'OK: JavaScript y scikit-learn coinciden (tolerancia 1e-6).'
               : 'ERROR: la paridad falló.');
process.exit(ok ? 0 : 1);
