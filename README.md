# Web Scraper - Inmuebles

Proyecto educativo de web scraping para extraer información de propiedades inmobiliarias en Neiva desde MetroCuadrado y exportarlas a CSV.

## 📋 Requisitos

- Python 3.7 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación

1. **Crear un entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   ```

2. **Activar el entorno virtual:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Uso

Ejecuta el script principal:

```bash
python scraper.py
```

El script:
- Extraerá información de propiedades de MetroCuadrado
- Generará un archivo CSV con los datos
- El archivo se guardará con un timestamp (ejemplo: `propiedades_neiva_20260206_153045.csv`)

## 📊 Datos Extraídos

El CSV contiene las siguientes columnas:
- **titulo**: Nombre/descripción de la propiedad
- **precio**: Precio de venta o arriendo
- **ubicacion**: Ubicación de la propiedad
- **area**: Área en m²
- **habitaciones**: Número de habitaciones
- **banos**: Número de baños
- **link**: URL de la propiedad
- **fecha_extraccion**: Fecha y hora de extracción

## ⚙️ Configuración

Puedes modificar el número de páginas a extraer editando el archivo `scraper.py`:

```python
# En la función main()
scraper.obtener_propiedades(num_paginas=2)  # Cambia el número aquí
```

## ⚠️ Notas Importantes

1. **Selectores CSS**: Los sitios web cambian frecuentemente su estructura. Si el scraper no encuentra datos, es posible que necesites actualizar los selectores CSS en la función `extraer_datos_propiedad()`.

2. **Uso Responsable**: 
   - Respeta el archivo `robots.txt` del sitio
   - No hagas requests excesivos (el script incluye pausas)
   - Usa los datos solo con fines educativos

3. **Términos de Servicio**: Asegúrate de cumplir con los términos de servicio de MetroCuadrado.

## 🔧 Solución de Problemas

Si no se extraen datos:
1. Verifica que la URL esté correcta
2. Inspecciona el HTML del sitio con las herramientas de desarrollador del navegador
3. Actualiza los selectores CSS según la estructura actual del sitio

## 📚 Recursos de Aprendizaje

- [Documentación de BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Library](https://requests.readthedocs.io/)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)

## 📝 Licencia

Este proyecto es solo para fines educativos.
