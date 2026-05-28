"""
Scraper para ZonaProp (Argentina) usando Playwright sync API.
Extrae propiedades a partir de una URL de búsqueda.

Uso:
    py scraper_zonaprop.py --url "https://www.zonaprop.com.ar/departamentos-venta-cordoba-en-construccion.html" --paginas 3 --limite 50
    py scraper_zonaprop.py --url "https://www.zonaprop.com.ar/casas-alquiler-buenos-aires.html" --paginas 2

Notas:
 - Instalar: `pip install -r requirements.txt` y luego `playwright install`.
 - --paginas: cantidad de páginas a recorrer (cada página tiene ~20 inmuebles).
 - --limite: cantidad máxima de inmuebles a extraer.
"""

from playwright.sync_api import sync_playwright
import json
import argparse
import re
import os


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_url_segments(url: str) -> dict:
    """
    Extrae segmentos de la URL de ZonaProp.
    Ejemplo: https://www.zonaprop.com.ar/departamentos-venta-cordoba-en-construccion.html
    Retorna: { categoria, tipo, ubicacion, estado }
    """
    # Obtener la parte del path sin dominio y sin extensión
    # Ej: /departamentos-venta-cordoba-en-construccion.html  ->  departamentos-venta-cordoba-en-construccion
    path = url.split("zonaprop.com.ar/")[-1].replace(".html", "").split("?")[0].rstrip("/")

    parts = path.split("-")

    # El esquema de ZonaProp es: {categoria}-{tipo}-{ubicacion}[-{estado}]
    # Necesitamos identificar categoria, tipo y ubicacion.
    # tipo suele ser: venta, alquiler, alquiler-temporario
    TIPOS = {"venta", "alquiler", "alquiler-temporario", "arriendo"}

    categoria = None
    tipo = None
    ubicacion = None
    estado = None

    # Buscar el índice del tipo
    tipo_idx = None
    for i, part in enumerate(parts):
        if part in TIPOS:
            tipo_idx = i
            break
        # alquiler-temporario ocupa 2 palabras
        if i < len(parts) - 1 and f"{part}-{parts[i+1]}" in TIPOS:
            tipo_idx = i
            tipo = f"{part}-{parts[i+1]}"
            break

    if tipo_idx is not None:
        categoria = "-".join(parts[:tipo_idx])
        if tipo is None:
            tipo = parts[tipo_idx]
            rest = parts[tipo_idx + 1:]
        else:
            rest = parts[tipo_idx + 2:]

        # La ubicacion es la palabra siguiente al tipo
        # El estado es el resto (puede ser multi-palabra como "en-construccion")
        if rest:
            ubicacion = rest[0]
            if len(rest) > 1:
                estado = "-".join(rest[1:])
    else:
        # fallback: usar partes por posición
        categoria = parts[0] if len(parts) > 0 else None
        tipo = parts[1] if len(parts) > 1 else None
        ubicacion = parts[2] if len(parts) > 2 else None
        estado = "-".join(parts[3:]) if len(parts) > 3 else None

    return {
        "categoria": categoria,
        "tipo": tipo,
        "ubicacion": ubicacion,
        "estado": estado,
    }


def build_page_url(base_url: str, page: int) -> str:
    """
    Construye la URL de paginación de ZonaProp.
    Página 1 = URL original. Página 2+ = URL con sufijo -pagina-N
    """
    if page == 1:
        return base_url
    # Insertar -pagina-N antes de .html
    return re.sub(r"\.html$", f"-pagina-{page}.html", base_url)


def extract_feature(spans, keyword: str) -> str | None:
    """Extrae el texto de un span que contenga la palabra clave."""
    for span in spans:
        text = span.inner_text().strip()
        if keyword.lower() in text.lower():
            return text
    return None


def scrape_page(page, url: str, segments: dict) -> list[dict]:
    """Navega a la URL y extrae todos los inmuebles listados."""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)

    # Esperar que carguen las listings
    try:
        page.wait_for_selector("[class*='postingCard']", timeout=15000)
    except Exception:
        print(f"  [!] No se encontraron resultados en: {url}")
        return []

    cards = page.query_selector_all("[class*='postingCard-module__posting-card-']")
    if not cards:
        # Fallback: buscar por data-qa
        cards = page.query_selector_all("[data-qa='posting PROPERTY']")

    results = []

    for card in cards:
        inmueble = {
            "categoria": segments["categoria"],
            "titulo": None,
            "precio": None,
            "ubicacion": segments["ubicacion"],
            "tipo": segments["tipo"],
            "m2": None,
            "bano": None,
            "habitacion": None,
            "estado": segments["estado"],
        }

        # Título / dirección
        titulo_el = card.query_selector("[class*='postingLocations-module__location-address']")
        if titulo_el:
            inmueble["titulo"] = titulo_el.inner_text().strip()

        # Precio
        precio_el = card.query_selector("[class*='postingPrices-module__price']")
        if precio_el:
            inmueble["precio"] = precio_el.inner_text().strip()

        # Features: m², baños, dormitorios
        feature_spans = card.query_selector_all("[class*='postingMainFeatures-module__posting-main-features-span']")

        m2_text = extract_feature(feature_spans, "m²")
        if m2_text:
            inmueble["m2"] = m2_text

        bano_text = extract_feature(feature_spans, "baño")
        if bano_text:
            inmueble["bano"] = bano_text

        hab_text = extract_feature(feature_spans, "dorm")
        if hab_text:
            inmueble["habitacion"] = hab_text

        results.append(inmueble)

    return results


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scraper ZonaProp Argentina")
    parser.add_argument("--url", required=True, help="URL de búsqueda de ZonaProp")
    parser.add_argument("--paginas", type=int, default=1, help="Número de páginas a recorrer (default: 1)")
    parser.add_argument("--limite", type=int, default=None, help="Límite máximo de inmuebles a extraer")
    args = parser.parse_args()

    url = args.url.strip()
    segments = parse_url_segments(url)

    print(f"URL base    : {url}")
    print(f"Categoría   : {segments['categoria']}")
    print(f"Tipo        : {segments['tipo']}")
    print(f"Ubicación   : {segments['ubicacion']}")
    print(f"Estado      : {segments['estado']}")
    print(f"Páginas     : {args.paginas}")
    print(f"Límite      : {args.limite or 'sin límite'}")
    print("-" * 50)

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for page_num in range(1, args.paginas + 1):
            page_url = build_page_url(url, page_num)
            print(f"[Página {page_num}] {page_url}")
            results = scrape_page(page, page_url, segments)
            print(f"  -> {len(results)} inmuebles encontrados")
            all_results.extend(results)

            if args.limite and len(all_results) >= args.limite:
                all_results = all_results[: args.limite]
                print(f"  -> Límite alcanzado ({args.limite} inmuebles)")
                break

        browser.close()

    # Nombre de archivo basado en el path de la URL
    path_segment = url.split("zonaprop.com.ar/")[-1].replace(".html", "").split("?")[0].rstrip("/")
    output_file = f"{path_segment}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print("-" * 50)
    print(f"Total extraídos : {len(all_results)}")
    print(f"Archivo guardado: {output_file}")


if __name__ == "__main__":
    main()
