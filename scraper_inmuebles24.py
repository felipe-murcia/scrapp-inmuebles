"""
Scraper para Inmuebles24.com usando Playwright sync API.
Extrae precio, título, ubicación, m2, baños y recámaras de listados de propiedades.

Uso rápido:
    py scraper_inmuebles24.py --ciudad buenos-aires --categoria departamentos --tipo alquiler --concepto capital-federal

URLs:
    Opción 1: https://www.inmuebles24.com/{categoria}-en-{tipo}-en-{ciudad}-provincia-{concepto}.html
    Opción 2: https://www.inmuebles24.com/{categoria}-en-{tipo}-en-{ciudad}-provincia-{concepto}-pagina-{pagina}.html

Notas:
 - Instalar: `pip install -r requirements.txt` y luego `playwright install`.

Ejemplos:
    # Ejemplo básico
    py scraper_inmuebles24.py --ciudad buenos-aires --categoria departamentos --tipo alquiler --concepto capital-federal

    # Con paginación
    py scraper_inmuebles24.py --ciudad buenos-aires --categoria casas --tipo venta --concepto capital-federal --paginas 3

    # Mostrar navegador (debug)
    py scraper_inmuebles24.py --ciudad cordoba --categoria departamentos --tipo alquiler --concepto cordoba --no-headless
"""

from playwright.sync_api import sync_playwright
import json
import argparse
import re
import os
from pathlib import Path


def construir_url(categoria, tipo, ciudad, concepto, pagina=None):
    """
    Construye la URL según el número de página.
    - Página 1 o None: usa la URL sin número de página
    - Página 2+: usa la URL con -pagina-{numero}
    """
    base = f"https://www.inmuebles24.com/{categoria}-en-{tipo}-en-{ciudad}-provincia-{concepto}"
    
    if pagina is None or pagina == 1:
        return f"{base}.html"
    else:
        return f"{base}-pagina-{pagina}.html"


def esperar_captcha(page, timeout_captcha=30):
    """
    Espera a que el usuario resuelva el captcha manualmente.
    """
    print("\n" + "="*60)
    print("⚠️  CAPTCHA DETECTADO - ACCIÓN MANUAL REQUERIDA")
    print("="*60)
    print(f"Tienes {timeout_captcha} segundos para hacer clic en 'No soy robot'")
    print("Esperando...")
    print("="*60 + "\n")
    
    # Esperar el tiempo indicado para que el usuario resuelva el captcha
    page.wait_for_timeout(timeout_captcha * 1000)
    print("✅ Continuando con el scraping...\n")


def scrape_pagina(page, categoria_input, ciudad, headless=True, max_items=50, esperar_captcha_tiempo=0):
    """
    Extrae los datos de una página ya cargada.
    """
    results = []
    
    # Esperar carga inicial
    page.wait_for_timeout(3000)
    
    # Si se solicita tiempo para captcha, esperar
    if esperar_captcha_tiempo > 0:
        esperar_captcha(page, esperar_captcha_tiempo)
    
    # Scroll para cargar lazy-loaded items
    print("  Haciendo scroll para cargar items...")
    for i in range(5):
        page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
        page.wait_for_timeout(1000)
    
    # Buscar las tarjetas de propiedades
    print("  Buscando tarjetas de propiedades...")
    
    # Selector principal para los items
    property_cards = page.query_selector_all('[class*="postingsList-module__card-container"]')
    
    if not property_cards:
        # Intentar selectores alternativos
        property_cards = page.query_selector_all('[data-qa="posting"]')
    
    if not property_cards:
        property_cards = page.query_selector_all('div[class*="posting-card"]')
    
    print(f"  Tarjetas encontradas: {len(property_cards)}")
    
    # Procesar cada tarjeta
    for idx, card in enumerate(property_cards):
        try:
            # Extraer precio
            precio = ''
            price_elem = card.query_selector('[class*="postingPrices-module__price"]')
            if price_elem:
                precio = price_elem.inner_text().strip().replace('\n', ' ')
            
            # Extraer título/ubicación
            titulo = ''
            title_elem = card.query_selector('[class*="postingLocations-module__location-address"]')
            if title_elem:
                titulo = title_elem.inner_text().strip()
            
            # Extraer características (m2, recámaras, baños)
            # Todos usan la misma clase, hay que diferenciar por contenido
            m2 = ''
            recamaras = ''
            banos = ''
            
            feature_spans = card.query_selector_all('[class*="postingMainFeatures-module__posting-main-features-span"]')
            
            for span in feature_spans:
                texto = span.inner_text().strip().lower()
                
                # Detectar metros cuadrados (m², m2, metros)
                if 'm²' in texto or 'm2' in texto or 'metros' in texto:
                    m2_match = re.search(r'([\d,\.]+)', texto)
                    if m2_match:
                        m2 = m2_match.group(1).replace(',', '')
                
                # Detectar recámaras/habitaciones/dormitorios
                elif 'rec' in texto or 'hab' in texto or 'dorm' in texto or 'cuarto' in texto:
                    rec_match = re.search(r'(\d+)', texto)
                    if rec_match:
                        recamaras = rec_match.group(1)
                
                # Detectar baños
                elif 'baño' in texto or 'bano' in texto or 'bath' in texto:
                    bano_match = re.search(r'(\d+)', texto)
                    if bano_match:
                        banos = bano_match.group(1)
            
            # Si no encontró con el selector específico, buscar alternativas
            if not m2 and not recamaras and not banos:
                all_spans = card.query_selector_all('span')
                for span in all_spans:
                    texto = span.inner_text().strip().lower()
                    if 'm²' in texto or 'm2' in texto:
                        m2_match = re.search(r'([\d,\.]+)', texto)
                        if m2_match and not m2:
                            m2 = m2_match.group(1).replace(',', '')
                    elif ('rec' in texto or 'hab' in texto or 'dorm' in texto) and not recamaras:
                        rec_match = re.search(r'(\d+)', texto)
                        if rec_match:
                            recamaras = rec_match.group(1)
                    elif ('baño' in texto or 'bano' in texto) and not banos:
                        bano_match = re.search(r'(\d+)', texto)
                        if bano_match:
                            banos = bano_match.group(1)
            
            # Agregar solo si tiene precio o título
            if precio or titulo:
                results.append({
                    'categoria': categoria_input.capitalize(),
                    'titulo': titulo,
                    'precio': precio,
                    'ubicacion': ciudad,
                    'm2': m2,
                    'banos': banos,
                    'recamaras': recamaras,
                    'estado': 'nuevo'
                })
                print(f"    [{len(results)}] {titulo[:40] if titulo else 'Sin título'}... - {precio}")
            
            if len(results) >= max_items:
                break
                
        except Exception as e:
            print(f"  Error en tarjeta {idx}: {e}")
            continue
    
    return results


def verificar_siguiente_pagina(page):
    """
    Verifica si existe una página siguiente.
    """
    # Buscar botón o link de página siguiente
    next_button = page.query_selector('[class*="pagination"]  a[rel="next"]')
    if next_button:
        return True
    
    # Buscar por texto "Siguiente" o ">"
    next_link = page.query_selector('a:has-text("Siguiente")')
    if next_link:
        return True
    
    # Buscar números de paginación
    pagination = page.query_selector('[class*="pagination"]')
    if pagination:
        return True
    
    return False


def scrape_inmuebles24(categoria, tipo, ciudad, concepto, headless=True, max_items=50, max_paginas=1, output=None, captcha_tiempo=120):
    """
    Función principal de scraping para Inmuebles24.
    
    Args:
        categoria: tipo de inmueble (departamentos, casas, locales, etc.)
        tipo: alquiler o venta
        ciudad: ciudad de búsqueda
        concepto: provincia/zona
        headless: ejecutar sin mostrar navegador
        max_items: máximo de items por página
        max_paginas: número máximo de páginas a recorrer
        output: archivo de salida
        captcha_tiempo: segundos para resolver captcha manualmente (0 = sin espera)
    """
    all_results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        pagina_actual = 1
        
        while pagina_actual <= max_paginas:
            # Construir URL según la página
            url = construir_url(categoria, tipo, ciudad, concepto, pagina_actual)
            print(f"\n{'='*60}")
            print(f"Página {pagina_actual}: {url}")
            print(f"{'='*60}")
            
            try:
                page.goto(url, timeout=60000)
                
                # Extraer datos de esta página (solo esperar captcha en la primera página)
                esperar_captcha_seg = captcha_tiempo if pagina_actual == 1 else 0
                resultados_pagina = scrape_pagina(page, categoria, ciudad, headless, max_items, esperar_captcha_seg)
                
                if not resultados_pagina:
                    print(f"  No se encontraron resultados en página {pagina_actual}. Terminando...")
                    break
                
                all_results.extend(resultados_pagina)
                print(f"  Subtotal: {len(resultados_pagina)} items (Total acumulado: {len(all_results)})")
                
                # Verificar si hay más páginas
                if pagina_actual < max_paginas:
                    tiene_siguiente = verificar_siguiente_pagina(page)
                    if not tiene_siguiente:
                        print("  No hay más páginas disponibles.")
                        break
                
                pagina_actual += 1
                
            except Exception as e:
                print(f"  Error al cargar página {pagina_actual}: {e}")
                break
        
        browser.close()
    
    # Guardar resultados
    if all_results:
        if output is None:
            output = f"inmueble-inmuebles24-{tipo}-{categoria}-{ciudad}-{concepto}.json"
        
        output_path = Path(__file__).parent / output
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETADO")
        print(f"{'='*60}")
        print(f"Total de registros: {len(all_results)}")
        print(f"Archivo guardado: {output_path}")
    else:
        print("\nNo se encontraron resultados.")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description='Scraper para Inmuebles24.com usando Playwright',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  py scraper_inmuebles24.py --ciudad buenos-aires --categoria departamentos --tipo alquiler --concepto capital-federal
  py scraper_inmuebles24.py --ciudad cordoba --categoria casas --tipo venta --concepto cordoba --paginas 3
  py scraper_inmuebles24.py --ciudad mendoza --categoria locales --tipo alquiler --concepto mendoza --no-headless
        """
    )
    
    parser.add_argument('--categoria', '-c', type=str, default='departamentos',
                        help='Categoría de inmueble (departamentos, casas, locales, terrenos, etc.)')
    parser.add_argument('--tipo', '-t', type=str, default='alquiler',
                        help='Tipo de operación (alquiler, venta)')
    parser.add_argument('--ciudad', type=str, default='buenos-aires',
                        help='Ciudad de búsqueda')
    parser.add_argument('--concepto', type=str, default='capital-federal',
                        help='Provincia o zona')
    parser.add_argument('--max', '-m', type=int, default=50,
                        help='Máximo de items por página (default: 50)')
    parser.add_argument('--paginas', '-p', type=int, default=1,
                        help='Número de páginas a recorrer (default: 1)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Archivo de salida JSON')
    parser.add_argument('--no-headless', action='store_true',
                        help='Mostrar el navegador durante el scraping')
    parser.add_argument('--captcha', type=int, default=120,
                        help='Segundos para resolver captcha manualmente (default: 120 = 2 minutos, usar 0 para desactivar)')
    
    args = parser.parse_args()
    
    scrape_inmuebles24(
        categoria=args.categoria,
        tipo=args.tipo,
        ciudad=args.ciudad,
        concepto=args.concepto,
        headless=not args.no_headless,
        max_items=args.max,
        max_paginas=args.paginas,
        output=args.output,
        captcha_tiempo=args.captcha
    )


if __name__ == "__main__":
    main()
