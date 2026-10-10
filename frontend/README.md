# frontend-food-ia

Interfaz web para consultar recomendaciones de platos por texto o voz.

## Ejecución local

```bash
python3 -m http.server 8080
```

Abrir `http://localhost:8080` con el backend disponible en `http://localhost:8000`.

La entrada por voz utiliza Web Speech API. Para probarla, abre el sistema en
Chrome, Edge o Brave, permite el acceso al micrófono cuando el navegador lo
solicite y pulsa “Hablar”. El dispositivo necesita conexión a Internet para
el servicio de reconocimiento. Si el navegador no es compatible, utiliza el
campo de texto.
