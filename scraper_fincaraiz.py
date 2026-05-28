"""
Scraper para Fincaraiz usando Playwright sync API.
Extrae precio, título, ubicación y especificaciones (m2, baños, habitaciones).

Uso rápido:
    py scraper_fincaraiz.py --url "https://www.fincaraiz.com.co/venta/ibague/tolima/nuevos" --output resultados.json

Notas:
 - Instalar: `pip install -r requirements.txt` y luego `playwright install`.
 - Selectores adaptados para la estructura de Fincaraiz
"""

from playwright.sync_api import sync_playwright
import json
import argparse
from urllib.parse import urljoin
import time
import re


def extract_first_word(text):
    """Extrae la primera palabra de un texto (categoría)."""
    if not text:
        return ''
    words = text.strip().split()
    return words[0] if words else ''


def scrape(url, headless=True, max_items=50):
    results = []
    current_page = 1
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        while len(results) < max_items:
            print(f"\n{'='*60}")
            print(f"PÁGINA {current_page}")
            print(f"{'='*60}")
            
            # Navegar a la URL (primera vez o siguiente página)
            page.goto(url, timeout=60000)
            
            # Esperar carga inicial
            page.wait_for_timeout(3000)
            
            # Scroll para cargar lazy-loaded items
            print("Haciendo scroll para cargar items...")
            for i in range(10):
                page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
                page.wait_for_timeout(1500)
                # Intentar varios selectores posibles para contar items
                price_count = len(page.query_selector_all('[class*="price"]'))
                print(f"  Scroll {i+1}: {price_count} items encontrados")

            # Obtener todas las tarjetas de propiedades
            print("\nBuscando tarjetas...")
            # Selector específico para Fincaraiz
            property_cards = page.query_selector_all('.listingCard')
            print(f"Tarjetas encontradas: {len(property_cards)}")
            
            # Si no encuentra, intenta selector alternativo
            if not property_cards:
                print("No encontró .listingCard, buscando alternativas...")
                property_cards = page.query_selector_all('.listingBoxCard')
                print(f"Alternativa encontrada: {len(property_cards)} elementos")

            # Si no hay tarjetas, terminar
            if not property_cards:
                print("No se encontraron más tarjetas. Finalizando...")
                break

            # Procesar cada tarjeta
            items_in_page = 0
            for idx, card in enumerate(property_cards):
                try:
                    # Extraer precio usando selector específico
                    precio = ''
                    price_elem = card.query_selector('.main-price')
                    if price_elem:
                        precio = price_elem.inner_text().strip()

                    # Extraer ubicación (tipo de propiedad y ciudad)
                    ubicacion = ''
                    location_elem = card.query_selector('.lc-location')
                    if location_elem:
                        ubicacion = location_elem.inner_text().strip()
                        # Extraer categoría de la ubicación (primera palabra)
                        categoria = extract_first_word(ubicacion)
                    else:
                        categoria = ''

                    # Extraer título del proyecto
                    titulo = ''
                    title_elem = card.query_selector('.lc-title')
                    if title_elem:
                        titulo = title_elem.inner_text().strip()

                    # Extraer especificaciones usando los selectores de tipología
                    habitaciones = ''
                    banos = ''
                    m2 = ''
                    
                    # Buscar todos los items de tipología
                    typology_items = card.query_selector_all('.lc-typologyTag__item strong')
                    for item in typology_items:
                        text = item.inner_text().strip()
                        
                        # Extraer habitaciones (patrón "3 Habs.")
                        hab_match = re.search(r'(\d+)\s*Hab', text, re.IGNORECASE)
                        if hab_match:
                            habitaciones = hab_match.group(1)
                        
                        # Extraer baños (patrón "2 Baños")
                        bath_match = re.search(r'(\d+)\s*Baño', text, re.IGNORECASE)
                        if bath_match:
                            banos = bath_match.group(1)
                        
                        # Extraer m² (patrón "71.96 m²")
                        area_match = re.search(r'([\d,\.]+)\s*m²', text)
                        if area_match:
                            m2 = area_match.group(1)

                    # Agregar solo si tiene precio
                    if precio:
                        results.append({
                            'categoria': categoria,
                            'titulo': titulo,
                            'precio': precio,
                            'ubicacion': ubicacion,
                            'm2': m2,
                            'banos': banos,
                            'habitaciones': habitaciones,
                            'antiguedad': args.antiguedad
                        })
                        items_in_page += 1
                        print(f"  [{len(results)}] {titulo[:40] if titulo else ubicacion[:40]} - {precio}")

                    if len(results) >= max_items:
                        break

                except Exception as e:
                    print(f"Error en tarjeta {idx}: {e}")
                    continue

            print(f"\nExtraídos {items_in_page} items de esta página. Total acumulado: {len(results)}")

            # Si ya alcanzamos el máximo, salir
            if len(results) >= max_items:
                print(f"Alcanzado el límite de {max_items} items.")
                break

            # Buscar el enlace a la siguiente página
            current_page += 1
            next_page_selector = f'a.ant-pagination-item-link[href*="pagina{current_page}"]'
            next_page_link = page.query_selector(next_page_selector)
            
            if next_page_link:
                # Obtener el href de la siguiente página
                next_url = next_page_link.get_attribute('href')
                if next_url:
                    # Construir URL completa si es relativa
                    if next_url.startswith('/'):
                        next_url = f"https://www.fincaraiz.com.co{next_url}"
                    url = next_url
                    print(f"\nNavegando a página {current_page}: {url}")
                else:
                    print("No se encontró más páginas.")
                    break
            else:
                print("No se encontró enlace a la siguiente página. Finalizando...")
                break

        browser.close()
        print(f"\n{'='*60}")
        print(f"Total extraído: {len(results)} items de {current_page} página(s)")
        print(f"{'='*60}\n")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scraper Fincaraiz con extracción por texto')
    parser.add_argument('--url', '-u', help='URL completa a scrapear (ej: https://www.fincaraiz.com.co/venta/ibague/tolima/nuevos)')
    parser.add_argument('--concepto', choices=['venta', 'arriendo'], default='venta', help='Concepto de operación: "venta" o "arriendo"')
    parser.add_argument('--ciudad', '-c', default='ibague', help='Ciudad o municipio (ej: ibague)')
    parser.add_argument('--departamento', '-d', default='tolima', help='Departamento (ej: tolima)')
    parser.add_argument('--antiguedad', '-a', default='nuevos', help='Antigüedad de la propiedad: "nuevos" o "usados"')
    parser.add_argument('--output', '-o', default='resultados.json', help='Archivo JSON de salida')
    parser.add_argument('--no-headless', action='store_true', help='No headless (abre navegador visible)')
    parser.add_argument('--max', type=int, default=60, help='Máximo de anuncios a extraer')
    args = parser.parse_args()

    headless = not args.no_headless  # Headless por defecto

    # Normalizar nombres
    ciudad = args.ciudad.strip().lower().replace(' ', '-')
    departamento = args.departamento.strip().lower().replace(' ', '-')

    # Construir URL si no fue provista
    if args.url:
        target_url = args.url
    else:
        # Formato: https://www.fincaraiz.com.co/{concepto}/{ciudad}/{departamento}/{antiguedad}
        target_url = f"https://www.fincaraiz.com.co/{args.concepto}/{ciudad}/{departamento}/{args.antiguedad}"

    # Construir nombre de salida por defecto si el usuario no lo personalizó
    if args.output == 'resultados.json' or not args.output:
        output_file = f"inmueble-fincaraiz-{args.concepto}-{args.antiguedad}-{ciudad}.json"
    else:
        output_file = args.output

    print(f"Iniciando scraping: {target_url} (headless={headless})")
    data = scrape(target_url, headless=headless, max_items=args.max)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Guardado {len(data)} items en {output_file}")
