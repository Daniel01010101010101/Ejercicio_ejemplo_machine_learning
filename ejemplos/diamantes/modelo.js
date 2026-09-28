// Generado por el cuaderno plantilla_tu_modelo.ipynb. No lo edites a mano.
window.MODELO = {
  "version": "1.0.0",
  "proyecto": "Predictor de precio de diamantes",
  "fuente": {
    "nombre": "Diamonds (seaborn-data)",
    "url": "https://github.com/mwaskom/seaborn-data",
    "portal": "",
    "id": ""
  },
  "fecha_entrenamiento": "2026-09-28",
  "n_total": 53940,
  "n_entrenamiento": 43152,
  "n_prueba": 10788,
  "semilla": 42,
  "min_casos": 216,
  "algoritmo": "Ridge (alpha = 1) con codificación one-hot",
  "sklearn_version": "1.9.1",
  "objetivo": {
    "nombre": "price",
    "etiqueta": "Precio",
    "minimo": 0.0,
    "maximo": 20000,
    "unidad": "USD"
  },
  "metricas": {
    "modelo": {
      "nombre": "Regresión lineal (Ridge)",
      "mae": 1103.028593111198,
      "rmse": 1857.5243971693465,
      "r2": 0.7829505164501961
    },
    "linea_base": {
      "nombre": "Línea base: siempre el promedio",
      "mae": 3020.5058390529985,
      "rmse": 3987.2221763258735,
      "r2": -7.04060323410971e-05
    }
  },
  "cobertura_mae": 0.7257137560252132,
  "promedio_nacional": 3932.799721913237,
  "promedio_entrenamiento": 3939.490707267334,
  "intercepto": 3661.0255564932813,
  "variables": [
    {
      "nombre": "carat",
      "etiqueta": "Peso en quilates",
      "etiqueta_corta": "Peso en quilates",
      "grupo": "caso",
      "ayuda": "Elige el rango.",
      "mas_frecuente": "0,54 a 0,90",
      "categorias": [
        {
          "valor": "hasta 0,35",
          "etiqueta": "hasta 0,35",
          "coeficiente": -3755.3234880471628,
          "frecuencia": 0.20302651093807936,
          "n": 8761,
          "en_formulario": true
        },
        {
          "valor": "0,35 a 0,54",
          "etiqueta": "0,35 a 0,54",
          "coeficiente": -3079.697428236246,
          "frecuencia": 0.20844920281794588,
          "n": 8995,
          "en_formulario": true
        },
        {
          "valor": "0,54 a 0,90",
          "etiqueta": "0,54 a 0,90",
          "coeficiente": -1340.9383796241932,
          "frecuencia": 0.2111142009640341,
          "n": 9110,
          "en_formulario": true
        },
        {
          "valor": "0,90 a 1,13",
          "etiqueta": "0,90 a 1,13",
          "coeficiente": 1621.861725844068,
          "frecuencia": 0.17901835372636263,
          "n": 7725,
          "en_formulario": true
        },
        {
          "valor": "más de 1,13",
          "etiqueta": "más de 1,13",
          "coeficiente": 6554.0975700465,
          "frecuencia": 0.19839173155357806,
          "n": 8561,
          "en_formulario": true
        }
      ]
    },
    {
      "nombre": "cut",
      "etiqueta": "Calidad del corte",
      "etiqueta_corta": "Calidad del corte",
      "grupo": "caso",
      "ayuda": "",
      "mas_frecuente": "Ideal",
      "categorias": [
        {
          "valor": "Fair",
          "etiqueta": "Regular",
          "coeficiente": -322.93625686936747,
          "frecuencia": 0.029546718576195775,
          "n": 1275,
          "en_formulario": true
        },
        {
          "valor": "Good",
          "etiqueta": "Bueno",
          "coeficiente": 3.8849143478837647,
          "frecuencia": 0.09042454579162032,
          "n": 3902,
          "en_formulario": true
        },
        {
          "valor": "Very Good",
          "etiqueta": "Muy bueno",
          "coeficiente": 95.4443553340117,
          "frecuencia": 0.22478680014831295,
          "n": 9700,
          "en_formulario": true
        },
        {
          "valor": "Premium",
          "etiqueta": "Premium",
          "coeficiente": 84.6391974265198,
          "frecuencia": 0.25528364849833146,
          "n": 11016,
          "en_formulario": true
        },
        {
          "valor": "Ideal",
          "etiqueta": "Ideal",
          "coeficiente": 138.9677897674552,
          "frecuencia": 0.3999582869855395,
          "n": 17259,
          "en_formulario": true
        }
      ]
    },
    {
      "nombre": "color",
      "etiqueta": "Color (D es el mejor, J el peor)",
      "etiqueta_corta": "Color (D es el mejor, J el peor)",
      "grupo": "caso",
      "ayuda": "",
      "mas_frecuente": "G",
      "categorias": [
        {
          "valor": "D",
          "etiqueta": "D",
          "coeficiente": 608.3736992493193,
          "frecuencia": 0.12544030404152762,
          "n": 5413,
          "en_formulario": true
        },
        {
          "valor": "E",
          "etiqueta": "E",
          "coeficiente": 415.33140386230406,
          "frecuencia": 0.1822163515016685,
          "n": 7863,
          "en_formulario": true
        },
        {
          "valor": "F",
          "etiqueta": "F",
          "coeficiente": 370.67484337566265,
          "frecuencia": 0.1771412680756396,
          "n": 7644,
          "en_formulario": true
        },
        {
          "valor": "G",
          "etiqueta": "G",
          "coeficiente": 200.49303729876053,
          "frecuencia": 0.208912680756396,
          "n": 9015,
          "en_formulario": true
        },
        {
          "valor": "H",
          "etiqueta": "H",
          "coeficiente": -168.1603200825179,
          "frecuencia": 0.15542732665925102,
          "n": 6707,
          "en_formulario": true
        },
        {
          "valor": "I",
          "etiqueta": "I",
          "coeficiente": -345.018027504268,
          "frecuencia": 0.09904523544679274,
          "n": 4274,
          "en_formulario": true
        },
        {
          "valor": "J",
          "etiqueta": "J",
          "coeficiente": -1081.6946362022363,
          "frecuencia": 0.05181683351872451,
          "n": 2236,
          "en_formulario": true
        }
      ]
    },
    {
      "nombre": "clarity",
      "etiqueta": "Pureza",
      "etiqueta_corta": "Pureza",
      "grupo": "caso",
      "ayuda": "",
      "mas_frecuente": "SI1",
      "categorias": [
        {
          "valor": "I1",
          "etiqueta": "I1",
          "coeficiente": -2925.320629130437,
          "frecuencia": 0.013556729699666295,
          "n": 585,
          "en_formulario": true
        },
        {
          "valor": "SI2",
          "etiqueta": "SI2",
          "coeficiente": -636.3913731298106,
          "frecuencia": 0.16930849091583242,
          "n": 7306,
          "en_formulario": true
        },
        {
          "valor": "SI1",
          "etiqueta": "SI1",
          "coeficiente": -136.26666711049302,
          "frecuencia": 0.24378939562476826,
          "n": 10520,
          "en_formulario": true
        },
        {
          "valor": "VS2",
          "etiqueta": "VS2",
          "coeficiente": 320.73143654247843,
          "frecuencia": 0.22694197256210605,
          "n": 9793,
          "en_formulario": true
        },
        {
          "valor": "VS1",
          "etiqueta": "VS1",
          "coeficiente": 514.3356742780162,
          "frecuencia": 0.15132554690396738,
          "n": 6530,
          "en_formulario": true
        },
        {
          "valor": "VVS2",
          "etiqueta": "VVS2",
          "coeficiente": 798.0078912282817,
          "frecuencia": 0.09371523915461624,
          "n": 4044,
          "en_formulario": true
        },
        {
          "valor": "VVS1",
          "etiqueta": "VVS1",
          "coeficiente": 840.2681905408314,
          "frecuencia": 0.0682239525398591,
          "n": 2944,
          "en_formulario": true
        },
        {
          "valor": "IF",
          "etiqueta": "IF",
          "coeficiente": 1224.635476782511,
          "frecuencia": 0.03313867259918428,
          "n": 1430,
          "en_formulario": true
        }
      ]
    }
  ],
  "excluidas": [],
  "casos_prueba": [
    {
      "id": 1,
      "entradas": {
        "carat": "hasta 0,35",
        "cut": "Ideal",
        "color": "I",
        "clarity": "VS1"
      },
      "puntaje_real": 434.0,
      "prediccion_sklearn": 213.9875049873217
    },
    {
      "id": 2,
      "entradas": {
        "carat": "0,54 a 0,90",
        "cut": "Ideal",
        "color": "J",
        "clarity": "SI1"
      },
      "puntaje_real": 1889.0,
      "prediccion_sklearn": 1241.0936633238139
    },
    {
      "id": 3,
      "entradas": {
        "carat": "0,54 a 0,90",
        "cut": "Ideal",
        "color": "H",
        "clarity": "VS2"
      },
      "puntaje_real": 4007.0,
      "prediccion_sklearn": 2611.626083096504
    },
    {
      "id": 4,
      "entradas": {
        "carat": "0,90 a 1,13",
        "cut": "Good",
        "color": "E",
        "clarity": "SI1"
      },
      "puntaje_real": 5411.0,
      "prediccion_sklearn": 5565.836933437044
    },
    {
      "id": 5,
      "entradas": {
        "carat": "más de 1,13",
        "cut": "Very Good",
        "color": "E",
        "clarity": "SI1"
      },
      "puntaje_real": 6373.0,
      "prediccion_sklearn": 10589.632218625604
    }
  ],
  "textos": {
    "titulo": "Predictor de precio de diamantes",
    "subtitulo": "Machine Learning 1 · Universidad EAN",
    "pregunta": "¿Cuánto vale un diamante?",
    "aviso_etico": "Es una estimación con error: úsala para aprender y discutir, no para tomar decisiones importantes.",
    "etiqueta_promedio": "Promedio de los datos",
    "subetiqueta_medidor": "USD",
    "autor": "Tu nombre",
    "autor_url": "",
    "grupos": {
      "caso": "Datos del caso"
    }
  }
};
