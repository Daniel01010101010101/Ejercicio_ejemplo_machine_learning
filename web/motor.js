// Motor de predicción del modelo exportado en modelo.js.
//
// Lo usan la página (index.html) y la prueba de paridad (scripts/prueba_paridad.js),
// así la prueba revisa exactamente el mismo código que corre en el navegador.
//
// Dos tipos de modelo:
//  - "arboles": punto de partida + la hoja a la que llega cada árbol
//    (Gradient Boosting, bosque aleatorio o un solo árbol de decisión).
//  - "lineal" (o sin tipo, como los modelo.js de la versión 1): intercepto + la suma
//    de los coeficientes de las respuestas elegidas.
(function (global) {
  'use strict';

  function categoria(variable, valor) {
    var lista = variable.categorias || [];
    for (var i = 0; i < lista.length; i++) {
      if (lista[i].valor === valor) return lista[i];
    }
    return null;
  }

  // Datos que se calculan una sola vez por modelo.
  var memoria = typeof WeakMap === 'function' ? new WeakMap() : null;
  function preparar(modelo) {
    var listo = memoria && memoria.get(modelo);
    if (listo) return listo;
    listo = { variables: {} };
    modelo.variables.forEach(function (v) { listo.variables[v.nombre] = v; });
    if (modelo.tipo === 'arboles') {
      // Cada columna de los árboles es [variable, categoría] (un uno o un cero)
      // o [variable] (un número).
      listo.columnas = modelo.arboles.columnas.map(function (c) {
        return { variable: c[0], categoria: c.length > 1 ? c[1] : null, numerica: c.length === 1 };
      });
    } else {
      // Efecto promedio de cada pregunta en entrenamiento. Se cumple:
      // intercepto + suma(efectos promedio) = promedio de entrenamiento.
      listo.efectoMedio = {};
      modelo.variables.forEach(function (v) {
        listo.efectoMedio[v.nombre] = v.categorias.reduce(function (s, c) {
          return s + c.frecuencia * c.coeficiente;
        }, 0);
      });
    }
    if (memoria) memoria.set(modelo, listo);
    return listo;
  }

  // ---------------------------------------------------------------- Lineal
  function predecirLineal(modelo, respuestas) {
    var total = modelo.intercepto;
    modelo.variables.forEach(function (v) {
      var c = categoria(v, respuestas[v.nombre]);
      if (c) total += c.coeficiente; // categoría desconocida: aporta 0
    });
    return total;
  }

  function explicarLineal(modelo, respuestas) {
    var listo = preparar(modelo);
    var aportes = {};
    modelo.variables.forEach(function (v) {
      var c = categoria(v, respuestas[v.nombre]);
      aportes[v.nombre] = (c ? c.coeficiente : 0) - listo.efectoMedio[v.nombre];
    });
    return { estimacion: predecirLineal(modelo, respuestas), partida: modelo.promedio_entrenamiento, aportes: aportes };
  }

  // ---------------------------------------------------------------- Árboles
  // Las respuestas en el orden de columnas que vio el modelo al entrenar.
  function vector(modelo, respuestas) {
    var listo = preparar(modelo);
    var float32 = modelo.arboles.float32;
    var x = new Array(listo.columnas.length);
    for (var j = 0; j < listo.columnas.length; j++) {
      var col = listo.columnas[j];
      var valor = respuestas[col.variable];
      if (!col.numerica) {
        // One-hot: 1 si es la categoría de esta columna. Una categoría desconocida
        // queda en ceros, como OneHotEncoder(handle_unknown="ignore").
        x[j] = valor === col.categoria ? 1 : 0;
        continue;
      }
      var numero = typeof valor === 'number' ? valor : parseFloat(valor);
      // Un vacío se reemplaza por la mediana de entrenamiento, como SimpleImputer.
      if (!isFinite(numero)) numero = listo.variables[col.variable].mediana;
      // Los árboles de scikit-learn comparan en float32; el Gradient Boosting, en float64.
      x[j] = float32 ? Math.fround(numero) : numero;
    }
    return x;
  }

  // Recorre cada árbol desde la raíz hasta una hoja: en cada nodo pregunta
  // «¿columna <= umbral?» y baja a la izquierda (sí) o a la derecha (no).
  // El aporte de cada respuesta es cuánto cambió el valor del nodo en los pasos
  // que preguntaron por ella; punto de partida + aportes = estimación.
  function explicarArboles(modelo, respuestas, conAportes) {
    var A = modelo.arboles;
    var listo = preparar(modelo);
    var x = vector(modelo, respuestas);
    var total = A.base, partida = A.base, aportes = {};
    if (conAportes) modelo.variables.forEach(function (v) { aportes[v.nombre] = 0; });
    for (var t = 0; t < A.lista.length; t++) {
      var arbol = A.lista[t];
      var n = 0;
      if (conAportes) partida += A.escala * arbol.v[0];
      while (arbol.c[n] >= 0) {
        var j = arbol.c[n];
        var hijo = x[j] <= arbol.u[n] ? arbol.i[n] : arbol.d[n];
        if (conAportes) aportes[listo.columnas[j].variable] += A.escala * (arbol.v[hijo] - arbol.v[n]);
        n = hijo;
      }
      total += A.escala * arbol.v[n];
    }
    return { estimacion: total, partida: partida, aportes: aportes };
  }

  // Las preguntas que hace un árbol con estas respuestas, para mostrarlas en la página.
  function recorrido(modelo, respuestas, indice) {
    var A = modelo.arboles;
    var listo = preparar(modelo);
    var arbol = A.lista[indice || 0];
    var x = vector(modelo, respuestas);
    var pasos = [];
    var n = 0;
    while (arbol.c[n] >= 0) {
      var j = arbol.c[n];
      var cumple = x[j] <= arbol.u[n];
      pasos.push({ columna: listo.columnas[j], umbral: arbol.u[n], cumple: cumple });
      n = cumple ? arbol.i[n] : arbol.d[n];
    }
    return { pasos: pasos, hoja: arbol.v[n] };
  }

  // ---------------------------------------------------------------- Uso público
  function predecir(modelo, respuestas) {
    return modelo.tipo === 'arboles'
      ? explicarArboles(modelo, respuestas, false).estimacion
      : predecirLineal(modelo, respuestas);
  }

  function explicar(modelo, respuestas) {
    return modelo.tipo === 'arboles'
      ? explicarArboles(modelo, respuestas, true)
      : explicarLineal(modelo, respuestas);
  }

  global.MotorModelo = { predecir: predecir, explicar: explicar, recorrido: recorrido, categoria: categoria };
})(typeof window !== 'undefined' ? window : this);
