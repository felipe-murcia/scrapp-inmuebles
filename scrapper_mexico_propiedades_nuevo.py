"""
Scraper para Propiedades.com (México) usando Playwright sync API.
Extrae precio, título, ubicación, m2, baños y recámaras de listados de propiedades.

Uso rápido:
    py scrapper_mexico_propiedades.py --ciudad monterrey --tipo departamentos --concepto renta --output resultados.json

Notas:
 - Instalar: `pip install -r requirements.txt` y luego `playwright install`.

 # Ejemplo básico (Monterrey, departamentos en renta)
py scrapper_mexico_propiedades.py

# Con parámetros personalizados
py scrapper_mexico_propiedades.py --ciudad guadalajara --tipo casas --concepto venta --max 50
py scrapper_mexico_propiedades.py --ciudad monterrey --tipo casas --concepto renta --max 50 --no-headless -p 5

# Mostrar navegador (debug)
py scrapper_mexico_propiedades.py --no-headless

"""

from playwright.sync_api import sync_playwright
import json
import argparse
import re


def scrape(url, ciudad, tipo, headless=True, max_items=50):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        
        # Esperar carga inicial
        page.wait_for_timeout(3000)
        
        # Scroll para cargar lazy-loaded items
        print("Haciendo scroll para cargar items...")
        for i in range(10):
            page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
            page.wait_for_timeout(1500)
            # Contar artículos encontrados
            article_count = len(page.query_selector_all('.sc-623147a8-1'))
            print(f"  Scroll {i+1}: {article_count} items encontrados")
            if article_count >= max_items:
                break

        # Obtener todas las tarjetas de propiedades (article con clase específica)
        print("\nBuscando tarjetas de propiedades...")
        property_cards = page.query_selector_all('.sc-623147a8-1')
        print(f"Tarjetas encontradas: {len(property_cards)}")
        
        # Si no encuentra con clase específica, intenta alternativas
        if not property_cards:
            print("No encontró sc-623147a8-1, buscando alternativas...")
            property_cards = page.query_selector_all('article[class*="sc-623147a8-1"]')
            print(f"Alternativa encontrada: {len(property_cards)} elementos")

        # Formatear categoría (capitalizar primera letra)
        categoria = tipo.capitalize() if tipo else ''

        # Procesar cada tarjeta
        for idx, card in enumerate(property_cards):
            try:
                # Extraer precio
                price_elem = card.query_selector('.sc-c1af3d6f-2.bxbIOz')
                if not price_elem:
                    price_elem = card.query_selector('[class*="sc-c1af3d6f-2"]')
                precio = price_elem.inner_text().strip().replace('\n', ' ') if price_elem else ''

                # Extraer título
                title_elem = card.query_selector('a.pcom-property-card-body-main-info-street')
                if not title_elem:
                    title_elem = card.query_selector('[class*="pcom-property-card-body-main-info-street"]')
                titulo = title_elem.inner_text().strip() if title_elem else ''

                # Extraer recámaras (buscar span con class amenities-label que contenga "Recámara")
                recamaras = ''
                amenities_labels = card.query_selector_all('span.amenities-label')
                for label in amenities_labels:
                    label_text = label.inner_text()
                    if 'Recámara' in label_text or 'Recamara' in label_text:
                        # El número está generalmente antes del texto o en el mismo elemento
                        recamara_match = re.search(r'(\d+)', label_text)
                        if recamara_match:
                            recamaras = recamara_match.group(1)
                        else:
                            # Buscar en el elemento anterior (hermano)
                            parent = label.evaluate_handle('el => el.parentElement')
                            parent_text = parent.inner_text() if parent else ''
                            recamara_match = re.search(r'(\d+)', parent_text)
                            if recamara_match:
                                recamaras = recamara_match.group(1)
                        break

                # Extraer baños (buscar span con class amenities-label que contenga "Baño")
                banos = ''
                for label in amenities_labels:
                    label_text = label.inner_text()
                    if 'Baño' in label_text or 'Bano' in label_text:
                        bano_match = re.search(r'(\d+)', label_text)
                        if bano_match:
                            banos = bano_match.group(1)
                        else:
                            parent = label.evaluate_handle('el => el.parentElement')
                            parent_text = parent.inner_text() if parent else ''
                            bano_match = re.search(r'(\d+)', parent_text)
                            if bano_match:
                                banos = bano_match.group(1)
                        break

                # Extraer metros cuadrados: buscar elemento que contenga m<sup>2</sup>
                m2 = ''
                # Buscar todos los h3 y encontrar el que tenga m<sup>2</sup>
                h3_elements = card.query_selector_all('h3')
                for h3 in h3_elements:
                    h3_html = h3.inner_html()
                    if 'm<sup>2</sup>' in h3_html or 'm²' in h3_html:
                        h3_text = h3.inner_text()
                        # Extraer solo el número antes de "m" (ej: "125 m²" -> "125")
                        m2_match = re.search(r'([\d,\.]+)\s*m', h3_text)
                        if m2_match:
                            m2 = m2_match.group(1).replace(',', '')
                        break

                # Agregar solo si tiene precio o título
                if precio or titulo:
                    results.append({
                        'categoria': categoria,
                        'titulo': titulo,
                        'precio': precio,
                        'ubicacion': ciudad,
                        'm2': m2,
                        'banos': banos,
                        'recamaras': recamaras,
                        'estado': 'Nuevo'
                    })
                    print(f"  [{len(results)}] {titulo[:50] if titulo else 'Sin título'} - {precio}")

                if len(results) >= max_items:
                    break

            except Exception as e:
                print(f"Error en tarjeta {idx}: {e}")
                continue

        browser.close()
        print(f"\nTotal extraído: {len(results)} items\n")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scraper Propiedades.com México con Playwright')
    parser.add_argument('--ciudad', '-c', default='monterrey', help='Ciudad (ej: monterrey, guadalajara, cdmx)')
    parser.add_argument('--tipo', '-t', default='departamentos', help='Tipo de propiedad (ej: departamentos, casas, terrenos)')
    parser.add_argument('--concepto', choices=['venta', 'renta'], default='renta', help='Concepto: "venta" o "renta"')
    parser.add_argument('--output', '-o', default='', help='Archivo JSON de salida (por defecto se genera automáticamente)')
    parser.add_argument('--no-headless', action='store_true', help='Mostrar navegador (no headless)')
    parser.add_argument('--max', type=int, default=100, help='Máximo de anuncios a extraer')
    parser.add_argument('--pagina', '-p', type=int, default=1, help='Número de página (ej: 1, 2, 3...)')
    args = parser.parse_args()

    headless = not args.no_headless

    # Normalizar parámetros
    ciudad = args.ciudad.strip().lower().replace(' ', '-')
    tipo = args.tipo.strip().lower().replace(' ', '-')
    concepto = args.concepto.strip().lower()

    # Construir URL: https://propiedades.com/{ciudad}/{tipo}-{concepto}/nuevo
    target_url = f"https://propiedades.com/{ciudad}/{tipo}-{concepto}/nuevo"
    
    # Agregar parámetro de página si es mayor a 1
    if args.pagina > 1:
        target_url += f"?pagina={args.pagina}"

    # Construir nombre de salida si no se especificó
    if not args.output:
        if args.pagina > 1:
            output_file = f"inmueble-propiedades-{concepto}-{tipo}-nuevo-{ciudad}-{args.pagina}.json"
        else:
            output_file = f"inmueble-propiedades-{concepto}-{tipo}-nuevo-{ciudad}-1.json"
    else:
        output_file = args.output

    print(f"Iniciando scraping: {target_url} (headless={headless})")
    data = scrape(target_url, ciudad=ciudad, tipo=tipo, headless=headless, max_items=args.max)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Guardado {len(data)} items en {output_file}")
