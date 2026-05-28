"""
Web Scraper con Playwright para MetroCuadrado - Inmuebles en Neiva
Este script usa Playwright para extraer información de propiedades y exportarlas a CSV
"""

from playwright.sync_api import sync_playwright
import csv
import time
from datetime import datetime
import json


class MetroCuadradoScraperPlaywright:
    def __init__(self, headless=True):
        self.url = "https://www.metrocuadrado.com/inmuebles/neiva/"
        self.headless = headless
        self.propiedades = []
    
    def iniciar_navegador(self, playwright):
        """Inicia el navegador con Playwright"""
        # Puedes cambiar chromium por firefox o webkit
        browser = playwright.chromium.launch(headless=self.headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        return browser, page
    
    def esperar_carga(self, page):
        """Espera a que la página cargue completamente"""
        try:
            # Esperar a que el contenido principal se cargue
            page.wait_for_load_state('networkidle', timeout=15000)
            time.sleep(2)  # Tiempo adicional para JavaScript
        except Exception as e:
            print(f"Advertencia al esperar carga: {e}")
    
    def extraer_propiedades(self, page):
        """Extrae todas las propiedades de la página actual"""
        print("\nExtrayendo propiedades de la página...")
        
        # Esperar a que se carguen las tarjetas de propiedades
        try:
            # Estos selectores pueden necesitar ajuste según la estructura del sitio
            page.wait_for_selector('article, .card, [class*="card"], [class*="propert"]', timeout=10000)
        except Exception as e:
            print(f"No se encontró el selector esperado: {e}")
            print("Intentando con selectores alternativos...")
        
        # Obtener todas las tarjetas de propiedades
        # Ajusta estos selectores según la estructura real del sitio
        selectores_posibles = [
            'article',
            '.card-detail',
            '[class*="PropertyCard"]',
            '[class*="property-card"]',
            '[data-testid*="property"]',
            '.propert-item'
        ]
        
        tarjetas = []
        for selector in selectores_posibles:
            tarjetas = page.query_selector_all(selector)
            if tarjetas:
                print(f"✓ Encontradas {len(tarjetas)} tarjetas con selector: {selector}")
                break
        
        if not tarjetas:
            print("⚠ No se encontraron tarjetas. Guardando HTML para análisis...")
            self.guardar_html_debug(page)
            return []
        
        propiedades_extraidas = []
        
        for idx, tarjeta in enumerate(tarjetas, 1):
            try:
                propiedad = self.extraer_datos_tarjeta(tarjeta, page)
                if propiedad:
                    propiedades_extraidas.append(propiedad)
                    print(f"  [{idx}/{len(tarjetas)}] {propiedad['titulo'][:50]}...")
            except Exception as e:
                print(f"  Error en tarjeta {idx}: {e}")
                continue
        
        return propiedades_extraidas
    
    def extraer_datos_tarjeta(self, tarjeta, page):
        """Extrae los datos de una tarjeta de propiedad"""
        
        # Función auxiliar para extraer texto de manera segura
        def texto_seguro(selector, parent=tarjeta):
            try:
                elemento = parent.query_selector(selector)
                return elemento.inner_text().strip() if elemento else "N/A"
            except:
                return "N/A"
        
        def atributo_seguro(selector, atributo, parent=tarjeta):
            try:
                elemento = parent.query_selector(selector)
                return elemento.get_attribute(atributo) if elemento else "N/A"
            except:
                return "N/A"
        
        # Título - múltiples selectores posibles
        titulo = (texto_seguro('h2') or 
                 texto_seguro('h3') or 
                 texto_seguro('[class*="title"]') or 
                 texto_seguro('a'))
        
        # Precio
        precio = (texto_seguro('[class*="price"]') or 
                 texto_seguro('[class*="Price"]') or
                 texto_seguro('.price'))
        
        # Ubicación
        ubicacion = (texto_seguro('[class*="location"]') or 
                    texto_seguro('[class*="address"]') or
                    texto_seguro('[class*="zone"]'))
        
        # Área
        area = (texto_seguro('[class*="area"]') or 
               texto_seguro('[class*="Area"]') or
               texto_seguro('[title*="m²"]'))
        
        # Habitaciones
        habitaciones = (texto_seguro('[class*="room"]') or 
                       texto_seguro('[class*="bedroom"]') or
                       texto_seguro('[title*="habitacion"]'))
        
        # Baños
        banos = (texto_seguro('[class*="bath"]') or 
                texto_seguro('[title*="baño"]'))
        
        # Link
        link = atributo_seguro('a', 'href')
        if link != "N/A" and not link.startswith('http'):
            link = f"https://www.metrocuadrado.com{link}"
        
        return {
            'titulo': titulo,
            'precio': precio,
            'ubicacion': ubicacion,
            'area': area,
            'habitaciones': habitaciones,
            'banos': banos,
            'link': link,
            'fecha_extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def guardar_html_debug(self, page):
        """Guarda el HTML de la página para depuración"""
        try:
            html_content = page.content()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_html_{timestamp}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✓ HTML guardado en: {filename}")
            print("  Abre este archivo para inspeccionar la estructura y ajustar los selectores.")
        except Exception as e:
            print(f"Error al guardar HTML: {e}")
    
    def hacer_scroll(self, page):
        """Hace scroll en la página para cargar contenido dinámico"""
        try:
            print("Haciendo scroll para cargar más contenido...")
            page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight / 2);
            """)
            time.sleep(1)
            page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            time.sleep(2)
        except Exception as e:
            print(f"Error al hacer scroll: {e}")
    
    def tomar_screenshot(self, page, nombre="screenshot.png"):
        """Toma una captura de pantalla de la página"""
        try:
            page.screenshot(path=nombre, full_page=True)
            print(f"✓ Screenshot guardado: {nombre}")
        except Exception as e:
            print(f"Error al tomar screenshot: {e}")
    
    def scrape(self, num_paginas=1, tomar_screenshots=False):
        """Ejecuta el scraping completo"""
        print("="*70)
        print("   SCRAPER CON PLAYWRIGHT - METROCUADRADO NEIVA")
        print("="*70)
        print(f"\nConfiguración:")
        print(f"  - Modo headless: {self.headless}")
        print(f"  - Páginas a extraer: {num_paginas}")
        print(f"  - Screenshots: {tomar_screenshots}")
        
        with sync_playwright() as playwright:
            browser, page = self.iniciar_navegador(playwright)
            
            try:
                for num_pag in range(1, num_paginas + 1):
                    url = f"{self.url}?page={num_pag}" if num_pag > 1 else self.url
                    print(f"\n{'='*70}")
                    print(f"Página {num_pag}/{num_paginas}: {url}")
                    print('='*70)
                    
                    # Navegar a la URL
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    
                    # Esperar a que cargue
                    self.esperar_carga(page)
                    
                    # Hacer scroll para cargar contenido dinámico
                    self.hacer_scroll(page)
                    
                    # Tomar screenshot si se solicita
                    if tomar_screenshots:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        self.tomar_screenshot(page, f"screenshot_pag{num_pag}_{timestamp}.png")
                    
                    # Extraer propiedades
                    propiedades = self.extraer_propiedades(page)
                    self.propiedades.extend(propiedades)
                    
                    print(f"\n✓ Propiedades extraídas: {len(propiedades)}")
                    
                    # Pausa entre páginas
                    if num_pag < num_paginas:
                        print("Esperando antes de la siguiente página...")
                        time.sleep(3)
                
            finally:
                browser.close()
        
        print(f"\n{'='*70}")
        print(f"✓ SCRAPING COMPLETADO - Total: {len(self.propiedades)} propiedades")
        print('='*70)
        
        return self.propiedades
    
    def exportar_csv(self, nombre_archivo=None):
        """Exporta los datos a un archivo CSV"""
        
        if not self.propiedades:
            print("\n⚠ No hay propiedades para exportar.")
            return
        
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"propiedades_neiva_playwright_{timestamp}.csv"
        
        try:
            with open(nombre_archivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
                campos = ['titulo', 'precio', 'ubicacion', 'area', 
                         'habitaciones', 'banos', 'link', 'fecha_extraccion']
                writer = csv.DictWriter(csvfile, fieldnames=campos)
                
                writer.writeheader()
                writer.writerows(self.propiedades)
            
            print(f"\n✓ Datos exportados exitosamente a: {nombre_archivo}")
            print(f"  Total de registros: {len(self.propiedades)}")
            
        except Exception as e:
            print(f"\n✗ Error al exportar CSV: {e}")
    
    def exportar_json(self, nombre_archivo=None):
        """Exporta los datos a un archivo JSON"""
        
        if not self.propiedades:
            print("\n⚠ No hay propiedades para exportar.")
            return
        
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"propiedades_neiva_playwright_{timestamp}.json"
        
        try:
            with open(nombre_archivo, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.propiedades, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"✓ Datos exportados a JSON: {nombre_archivo}")
            
        except Exception as e:
            print(f"✗ Error al exportar JSON: {e}")


def main():
    """Función principal"""
    
    # Crear instancia del scraper
    # headless=False mostrará el navegador (útil para aprender/debuggear)
    # headless=True ejecutará el navegador en segundo plano (más rápido)
    scraper = MetroCuadradoScraperPlaywright(headless=False)
    
    # Ejecutar el scraping
    # num_paginas: cantidad de páginas a extraer
    # tomar_screenshots: capturar pantallas para análisis
    scraper.scrape(num_paginas=1, tomar_screenshots=True)
    
    # Exportar resultados
    scraper.exportar_csv()
    scraper.exportar_json()
    
    print("\n" + "="*70)
    print("   PROCESO FINALIZADO")
    print("="*70)


if __name__ == "__main__":
    main()
