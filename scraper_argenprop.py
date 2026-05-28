"""
Scraper para ArgenProp usando Playwright sync API.
Extrae propiedades según categoría, tipo, ciudad y cantidad de páginas.

Uso:
    py scraper_argenprop.py --categoria departamentos --tipo alquiler --ciudad cordoba-arg --pagina 1
    py scraper_argenprop.py --categoria casa --tipo venta --ciudad buenos-aires-arg --pagina 3

Categorías válidas: departamentos, casa, local, campo
Tipos válidos: venta, alquiler

Notas:
 - Instalar: `pip install -r requirements.txt` y luego `playwright install`.
 - La salida queda en: {ciudad}-{tipo}-{categoria}.json
"""

from playwright.sync_api import sync_playwright
import json
import argparse
import sys


CATEGORIAS_VALIDAS = {"departamentos", "casas", "locales", "campos"}
TIPOS_VALIDOS = {"venta", "alquiler"}

# Mapeo de categoría al segmento de URL que usa ArgenProp
CATEGORIA_URL = {
    "departamentos": "departamentos",
    "casa": "casas",
    "local": "locales-comerciales",
    "campo": "campos",
}


def build_url(categoria: str, tipo: str, ciudad: str) -> str:
    cat_slug = CATEGORIA_URL.get(categoria, categoria)
    # ArgenProp: https://www.argenprop.com/departamentos/venta/cordoba-arg
    return f"https://www.argenprop.com/{cat_slug}/{tipo}/{ciudad}"


def get_icon_sibling_text(card, icon_class: str) -> str:
    """
    Busca un <i> con la clase dada dentro de card y retorna el texto
    del <span> hermano siguiente.
    """
    icon = card.query_selector(f"i.{icon_class}")
    if not icon:
        return ""
    # El span suele ser hermano del <i> dentro del mismo contenedor
    parent = icon.evaluate_handle("el => el.parentElement")
    if not parent:
        return ""
    span = parent.query_selector("span")
    if span:
        return span.inner_text().strip()
    return ""


def scrape(categoria: str, tipo: str, ciudad: str, pagina: int, headless: bool = True) -> list:
    url_base = build_url(categoria, tipo, ciudad)
    url = url_base if pagina == 1 else f"{url_base}?pagina-{pagina}"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        print(f"[Página {pagina}] Cargando: {url}")

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
        except Exception as e:
            print(f"  Error al cargar la página: {e}")
            browser.close()
            return results

        # Scroll para cargar lazy items
        for _ in range(5):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(600)

        items = page.query_selector_all(".listing__item")
        print(f"  Items encontrados: {len(items)}")

        if not items:
            print("  No se encontraron items.")
            browser.close()
            return results

        for item in items:
            try:
                # Título / dirección
                titulo_el = item.query_selector(".card__address")
                titulo = titulo_el.inner_text().strip() if titulo_el else ""

                # Precio
                precio_el = item.query_selector(".card__price")
                precio = precio_el.inner_text().strip() if precio_el else ""

                # m2 — icono superficie cubierta
                m2 = get_icon_sibling_text(item, "basico1-icon-superficie_cubierta")
                if "m²" not in m2:
                    m2 = ""

                # Baños
                bano = get_icon_sibling_text(item, "basico1-icon-cantidad_banos")
                if not any(kw in bano.lower() for kw in ["baño", "baños"]):
                    bano = ""

                # Habitaciones / dormitorios
                habitacion = get_icon_sibling_text(item, "basico1-icon-cantidad_dormitorios")
                if "dorm." not in habitacion.lower():
                    habitacion = ""

                # Estado / antigüedad
                estado = get_icon_sibling_text(item, "basico1-icon-antiguedad")

                entry = {
                    "categoria": categoria,
                    "titulo": titulo,
                    "precio": precio,
                    "ubicacion": ciudad,
                    "tipo": tipo,
                    "m2": m2,
                    "bano": bano,
                    "habitacion": habitacion,
                    "estado": estado,
                }
                results.append(entry)
                print(f"  [{len(results)}] {titulo[:50]} | {precio}")

            except Exception as e:
                print(f"  Error procesando item: {e}")
                continue

        browser.close()

    return results


def main():
    parser = argparse.ArgumentParser(description="Scraper ArgenProp")
    parser.add_argument(
        "--categoria",
        required=True,
        choices=list(CATEGORIAS_VALIDAS),
        help="Tipo de propiedad: departamentos, casa, local, campo",
    )
    parser.add_argument(
        "--tipo",
        required=True,
        choices=list(TIPOS_VALIDOS),
        help="Operación: venta o alquiler",
    )
    parser.add_argument(
        "--ciudad",
        required=True,
        help="Ciudad a buscar según slug de ArgenProp (ej: cordoba-arg, buenos-aires-arg)",
    )
    parser.add_argument(
        "--pagina",
        required=True,
        type=int,
        help="Número de página a extraer (ej: 1, 2, 3...)",
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Mostrar el navegador (modo no-headless)",
    )
    args = parser.parse_args()

    if args.pagina <= 0:
        print("Error: --pagina debe ser mayor a 0.")
        sys.exit(1)

    print(f"\n=== ArgenProp Scraper ===")
    print(f"  Categoría : {args.categoria}")
    print(f"  Tipo      : {args.tipo}")
    print(f"  Ciudad    : {args.ciudad}")
    print(f"  Página    : {args.pagina}")
    print(f"  URL base  : {build_url(args.categoria, args.tipo, args.ciudad)}\n")

    data = scrape(
        categoria=args.categoria,
        tipo=args.tipo,
        ciudad=args.ciudad,
        pagina=args.pagina,
        headless=not args.visible,
    )

    output_file = f"argentina-{args.ciudad}-{args.tipo}-{args.categoria}-pagina{args.pagina}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nTotal extraídos: {len(data)}")
    print(f"Archivo guardado: {output_file}")


if __name__ == "__main__":
    main()
