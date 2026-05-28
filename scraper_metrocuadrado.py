"""
Scraper para Metrocuadrado (Neiva) usando Playwright sync API.
Extrae precio, título, barrio y especificaciones (m2, baños, habitaciones).

Uso rápido:
    py scraper_metrocuadrado.py --url "https://www.metrocuadrado.com/inmuebles/neiva/" --output resultados.json

Notas:
 - Instalar: `pip install -r requirements.txt` y luego `playwright install`.
 - Selectores: property-card__detail-price, property-card__detail-title, property-card__detail-top__left, pt-main-specs
"""

from playwright.sync_api import sync_playwright
import json
import argparse
from urllib.parse import urljoin
import time


def extract_first_word(text):
    """Extrae la primera palabra de un texto (categoría)."""
    if not text:
        return ''
    words = text.strip().split()
    return words[0] if words else ''


def scrape(url, headless=True, max_items=50):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        
        # Esperar carga inicial
        page.wait_for_timeout(2000)
        
        # Scroll para cargar lazy-loaded items
        print("Haciendo scroll para cargar items...")
        for i in range(10):
            page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
            page.wait_for_timeout(1000)
            price_count = len(page.query_selector_all('.property-card__detail-price'))
            print(f"  Scroll {i+1}: {price_count} items encontrados")
            if price_count >= max_items:
                break

        # Obtener todas las tarjetas (por clase property-card)
        print("\nBuscando tarjetas...")
        property_cards = page.query_selector_all('.property-card__content')
        print(f"Tarjetas encontradas: {len(property_cards)}")
        
        # Si no encuentra por property-card, intenta otros selectores
        if not property_cards:
            print("No encontró .property-card__content, buscando alternativas...")
            property_cards = page.query_selector_all('[class*="property-card__content"]')
            print(f"Alternativa encontrada: {len(property_cards)} elementos")

        # Procesar cada tarjeta
        for idx, card in enumerate(property_cards):
            try:
                # Extraer precio
                price_elem = card.query_selector('.property-card__detail-price')
                precio = price_elem.inner_text().strip() if price_elem else ''

                # Extraer título
                title_elem = card.query_selector('.property-card__detail-title')
                titulo = title_elem.inner_text().strip() if title_elem else ''

                # Extraer categoría (primera palabra)
                categoria = extract_first_word(titulo)

                # Extraer barrio
                barrio_elem = card.query_selector('.property-card__detail-top__left')
                barrio = barrio_elem.inner_text().strip() if barrio_elem else ''

                # Extraer especificaciones
                m2 = ''
                banos = ''
                habitaciones = ''
                
                specs_elem = card.query_selector('pt-main-specs')
                if specs_elem:
                    m2 = specs_elem.get_attribute('squaremeter') or ''
                    banos = specs_elem.get_attribute('toilets') or ''
                    habitaciones = specs_elem.get_attribute('bedrooms') or ''

                # Agregar solo si tiene precio
                if precio:
                    results.append({
                        'categoria': categoria,
                        'titulo': titulo,
                        'precio': precio,
                        'barrio': barrio,
                        'm2': m2,
                        'banos': banos,
                        'habitaciones': habitaciones
                    })
                    print(f"  [{len(results)}] {titulo[:40]} - {precio}")

                if len(results) >= max_items:
                    break

            except Exception as e:
                print(f"Error en tarjeta {idx}: {e}")
                continue

        browser.close()
        print(f"\nTotal extraído: {len(results)} items\n")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scraper Metrocuadrado con selectores específicos')
    parser.add_argument('--url', '-u', default='https://www.metrocuadrado.com/inmuebles', help='URL completa a scrapear (si se proporciona, ignora --concepto/--ciudad)')
    parser.add_argument('--concepto', choices=['venta', 'arriendo'], default='venta', help='Concepto de operación: "venta" o "arriendo"')
    parser.add_argument('--ciudad', '-c', default='neiva', help='Ciudad o municipio (ej: neiva)')
    parser.add_argument('--output', '-o', default='resultados.json', help='Archivo JSON de salida (por defecto se genera según ciudad/tipo)')
    parser.add_argument('--no-headless', action='store_true', help='No headless (abre navegador visible)')
    parser.add_argument('--max', type=int, default=100, help='Máximo de anuncios a extraer')
    args = parser.parse_args()

    headless = not args.no_headless  # Headless por defecto

    # Normalizar ciudad
    ciudad = args.ciudad.strip().lower().replace(' ', '-')

    # Construir URL si no fue provista
    if args.url:
        target_url = f"{args.url}/{args.concepto}/{ciudad}"
    else:
        target_url = f"https://www.metrocuadrado.com/inmuebles/{args.concepto}/{ciudad}"

    # Construir nombre de salida por defecto si el usuario no lo personalizó
    if args.output == 'resultados.json' or not args.output:
        output_file = f"inmueble-metro-{args.concepto}-{ciudad}.json"
    else:
        output_file = args.output

    print(f"Iniciando scraping: {target_url} (headless={headless})")
    data = scrape(target_url, headless=headless, max_items=args.max)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Guardado {len(data)} items en {output_file}")
