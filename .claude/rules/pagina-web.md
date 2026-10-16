---
paths:
  - "web/**"
---
# Reglas de la página (`web/`)

- Solo HTML, CSS y JavaScript, sin librerías ni servidor. Lo único externo son las fuentes de Google Fonts, con respaldo del sistema: sin internet la página debe seguir funcionando.
- No quites la política de seguridad (`Content-Security-Policy` con `connect-src 'none'`): garantiza que la página no envía datos.
- Debe verse bien a 375 px de ancho (celular) sin scroll horizontal.
- Textos en español y en frases cortas; cifras con formato colombiano (12.345,6).
- No muestres más precisión de la que tiene el modelo: redondea la estimación y muestra el margen (± MAE).
- Accesibilidad: cada campo con su etiqueta, buen contraste y nada que dependa solo del color.
- `motor.js` lo usan la página y `scripts/prueba_paridad.js`; después de cambiarlo, la prueba de paridad debe seguir en OK.
- `modelo.js` y `modelo.json` se generan con `scripts/entrenar.py`: no se editan a mano.
