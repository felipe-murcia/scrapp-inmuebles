# Web Scraper con Playwright - MetroCuadrado 🎭

Proyecto educativo usando **Playwright** para hacer web scraping de propiedades inmobiliarias en Neiva.

## ¿Por qué Playwright?

Playwright es superior a requests/BeautifulSoup para sitios modernos porque:

- ✅ Ejecuta JavaScript (contenido dinámico)
- ✅ Espera a que elementos se carguen
- ✅ Permite interactuar con la página (clicks, scroll, formularios)
- ✅ Toma screenshots para debugging
- ✅ Soporta múltiples navegadores (Chromium, Firefox, WebKit)

## 🚀 Instalación

1. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Instalar los navegadores de Playwright:**
   ```bash
   playwright install
   ```
   
   Esto descarga Chromium, Firefox y WebKit (~300MB)

## 💻 Uso Básico

```bash
python scrapper2.py
```

## ⚙️ Configuración

### Modo Headless

En [scrapper2.py](scrapper2.py), línea 265:

```python
# Ver el navegador mientras trabaja (útil para aprender)
scraper = MetroCuadradoScraperPlaywright(headless=False)

# Ejecutar en segundo plano (más rápido)
scraper = MetroCuadradoScraperPlaywright(headless=True)
```

### Número de Páginas

```python
scraper.scrape(num_paginas=3, tomar_screenshots=True)
```

### Screenshots

```python
# Activar/desactivar capturas de pantalla
scraper.scrape(num_paginas=1, tomar_screenshots=True)
```

## 📁 Archivos Generados

- `propiedades_neiva_playwright_YYYYMMDD_HHMMSS.csv` - Datos en CSV
- `propiedades_neiva_playwright_YYYYMMDD_HHMMSS.json` - Datos en JSON
- `screenshot_pag1_YYYYMMDD_HHMMSS.png` - Capturas de pantalla
- `debug_html_YYYYMMDD_HHMMSS.html` - HTML para debugging

## 🔧 Debugging

Si no se extraen datos:

1. **Ejecuta en modo visible** (`headless=False`)
2. **Activa screenshots** (`tomar_screenshots=True`)
3. **Revisa el HTML generado** (archivo `debug_html_*.html`)
4. **Inspecciona el sitio** con F12 en el navegador
5. **Actualiza los selectores** en la función `extraer_datos_tarjeta()`

### Ejemplo de ajuste de selectores:

```python
# En la función extraer_propiedades(), línea ~50
selectores_posibles = [
    'article',
    '.card-detail',
    '[class*="PropertyCard"]',  # Añade tus selectores aquí
    '[class*="property-card"]',
    # ... más selectores
]
```

## 📚 Funciones Principales

### `scrape(num_paginas, tomar_screenshots)`
Ejecuta el scraping completo

### `extraer_propiedades(page)`
Extrae todas las propiedades de la página actual

### `hacer_scroll(page)`
Hace scroll para cargar contenido dinámico

### `tomar_screenshot(page, nombre)`
Captura la pantalla para análisis

### `guardar_html_debug(page)`
Guarda el HTML para inspeccionar selectores

### `exportar_csv(nombre_archivo)`
Exporta resultados a CSV

### `exportar_json(nombre_archivo)`
Exporta resultados a JSON

## 🎓 Ejemplos de Uso Avanzado

### Extraer datos específicos:

```python
scraper = MetroCuadradoScraperPlaywright(headless=False)
scraper.scrape(num_paginas=5)

# Filtrar solo apartamentos
apartamentos = [p for p in scraper.propiedades if 'apartamento' in p['titulo'].lower()]

# Guardar solo apartamentos
import csv
with open('solo_apartamentos.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=apartamentos[0].keys())
    writer.writeheader()
    writer.writerows(apartamentos)
```

### Cambiar navegador:

```python
# En la función iniciar_navegador()
# Cambiar chromium por firefox o webkit
browser = playwright.firefox.launch(headless=self.headless)
```

## 📊 Estructura de Datos

Cada propiedad contiene:

```json
{
  "titulo": "Apartamento en venta en Neiva",
  "precio": "$250.000.000",
  "ubicacion": "Centro, Neiva",
  "area": "85 m²",
  "habitaciones": "3",
  "banos": "2",
  "link": "https://www.metrocuadrado.com/...",
  "fecha_extraccion": "2026-02-06 15:30:45"
}
```

## ⚠️ Consideraciones

1. **Estructura del sitio**: Los sitios web cambian frecuentemente. Los selectores pueden necesitar actualización.

2. **Uso responsable**: 
   - No sobrecargues el servidor (hay pausas de 3 segundos entre páginas)
   - Respeta el `robots.txt`
   - Usa solo con fines educativos

3. **Rendimiento**: Playwright es más lento que requests pero más robusto para sitios modernos.

## 🆚 Playwright vs BeautifulSoup

| Característica | Playwright | BeautifulSoup |
|----------------|-----------|---------------|
| Contenido dinámico | ✅ Sí | ❌ No |
| Velocidad | 🐢 Más lento | 🚀 Rápido |
| JavaScript | ✅ Ejecuta | ❌ No ejecuta |
| Screenshots | ✅ Sí | ❌ No |
| Interactividad | ✅ Clicks, scroll | ❌ Solo HTML |
| Facilidad | 🟡 Media | 🟢 Fácil |

## 📚 Recursos de Aprendizaje

- [Documentación Oficial de Playwright](https://playwright.dev/python/)
- [Playwright Python API](https://playwright.dev/python/docs/api/class-playwright)
- [Selectores CSS](https://developer.mozilla.org/es/docs/Web/CSS/CSS_Selectors)

## 🐛 Problemas Comunes

### "playwright install" falla
```bash
# Instalar solo Chromium
playwright install chromium
```

### Timeout errors
```python
# Aumentar timeout en línea ~41
page.wait_for_selector('article', timeout=20000)  # 20 segundos
```

### No encuentra selectores
- Abre `debug_html_*.html` y busca las clases CSS correctas
- Actualiza `selectores_posibles` en la línea ~50

---

💡 **Tip**: Empieza con `headless=False` y `num_paginas=1` para ver cómo funciona todo antes de ejecutar scraping masivo.
