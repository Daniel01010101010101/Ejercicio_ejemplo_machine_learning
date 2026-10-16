#!/usr/bin/env node
/*
 * Resumen corto de un modelo.js, sin los árboles: para revisarlo sin leer 200 KB.
 *
 * Uso:  node scripts/resumen_modelo.js [web/modelo.js]
 *
 * Lo usan la skill /revisar-entrega y el subagente revisor-ml.
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var ruta = process.argv[2] || path.join(__dirname, '..', 'web', 'modelo.js');
var contexto = { window: {} };
vm.createContext(contexto);
vm.runInContext(fs.readFileSync(ruta, 'utf8'), contexto, { filename: ruta });
var m = contexto.window.MODELO;
if (!m) throw new Error(ruta + ' no definió window.MODELO');

var textos = m.textos || {};
var comparacion = (m.metricas && m.metricas.comparacion) || [];
var resumen = {
  archivo: ruta,
  proyecto: m.proyecto,
  autor: textos.autor || '',
  pregunta: textos.pregunta || '',
  fuente: m.fuente,
  fecha_entrenamiento: m.fecha_entrenamiento,
  objetivo: m.objetivo,
  tipo: m.tipo || 'lineal',
  algoritmo: m.algoritmo,
  arboles: m.arboles ? m.arboles.lista.length : 0,
  filas: { entrenamiento: m.n_entrenamiento, prueba: m.n_prueba },
  variables: m.variables.map(function (v) { return v.nombre + ' (' + (v.tipo || 'categoria') + ')'; }),
  excluidas: m.excluidas || [],
  aviso_etico: textos.aviso_etico || '',
  comparacion: comparacion.map(function (f) {
    var fila = { modelo: f.nombre, mae: +f.mae.toFixed(3), r2: +f.r2.toFixed(3) };
    if (f.exactitud !== undefined) fila.exactitud = +f.exactitud.toFixed(3);
    if (f.publicado) fila.publicado = true;
    return fila;
  }),
  casos_prueba: (m.casos_prueba || []).length,
};
console.log(JSON.stringify(resumen, null, 2));
