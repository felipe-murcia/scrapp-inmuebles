"""
Scraper para QuintoAndar (Brasil) usando Playwright sync API.
Extrae propiedades en alquiler o compra por ciudad y tipo.

Uso rápido:
    py scraper_quintoandar.py
    py scraper_quintoandar.py --modalidad alugar --ciudad sao-paulo-sp-brasil --tipo apartamento --output resultado.json
    py scraper_quintoandar.py --modalidad comprar --ciudad rio-de-janeiro-rj-brasil --tipo casa

Notas:
 - Instalar: `pip install -r requirements.txt` y luego `playwright install`.
 - Modalidades disponibles: alugar, comprar
 - Tipos disponibles: apartamento, casa
"""

from playwright.sync_api import sync_playwright
import json
import argparse
import re
import os


# ── Configuración de ciudades y tipos disponibles ──────────────────────────────
CIUDADES_DISPONIBLES = [
    "sao-paulo-sp-brasil",
    "rio-de-janeiro-rj-brasil",
    "belo-horizonte-mg-brasil",
    "curitiba-pr-brasil",
    "brasilia-df-brasil",
    "porto-alegre-rs-brasil",
    "salvador-ba-brasil",
    "fortaleza-ce-brasil",
    "recife-pe-brasil",
    "manaus-am-brasil",
]

TIPOS_DISPONIBLES = ["apartamento", "casa"]
MODALIDADES_DISPONIBLES = ["alugar", "comprar"]

BASE_URL = "https://www.quintoandar.com.br/{modalidad}/imovel/{ciudad}/{tipo}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_amenities(text: str) -> dict:
    """
    Extrae m2, quartos y vagas del texto de amenidades.
    Ejemplo: '45 m² · 2 quartos · 1 vaga'
    """
    m2 = quartos = vagas = None

    m2_match = re.search(r'([\d,\.]+)\s*m²', text)
    if m2_match:
        m2 = m2_match.group(1).strip()

    quartos_match = re.search(r'([\d]+)\s*quarto', text)
    if quartos_match:
        quartos = quartos_match.group(1).strip()

    vagas_match = re.search(r'([\d]+)\s*vaga', text)
    if vagas_match:
        vagas = vagas_match.group(1).strip()

    return {"m2": m2, "quartos": quartos, "vagas": vagas}


def scrape_page(url: str, modalidad: str, ciudad: str, tipo: str,
                headless: bool = True, max_items: int = 100) -> list:
    """Extrae propiedades de una URL de QuintoAndar."""
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
        )
        page = context.new_page()

        print(f"Abriendo: {url}")
        page.goto(url, timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Hacer clic en "Ver más" hasta alcanzar max_items o que no haya más botón
        print("Cargando ítems con botón 'Ver más'...")
        round_num = 0
        while True:
            cards = page.query_selector_all('[data-testid="house-card-container-rent"]')
            count = len(cards)
            print(f"  Ronda {round_num}: {count} ítems encontrados")
            if count >= max_items:
                break
            load_more_btn = page.query_selector('.LoadMoreButton_wrapper__1Mf3P')
            if not load_more_btn:
                print("  No hay más botón 'Ver más', fin de resultados.")
                break
            load_more_btn.scroll_into_view_if_needed()
            load_more_btn.click()
            page.wait_for_timeout(2500)
            round_num += 1

        cards = page.query_selector_all('[data-testid="house-card-container-rent"]')
        print(f"\nTotal tarjetas encontradas: {len(cards)}")

        for idx, card in enumerate(cards[:max_items]):
            try:
                # Título / descripción
                titulo_el = card.query_selector(
                    '.FindHouseCard_descriptionText__wT0XQ'
                )
                titulo = titulo_el.inner_text().strip() if titulo_el else None

                # Precio
                precio_el = card.query_selector('.EKXjIf.EqjlRj')
                precio = precio_el.inner_text().strip() if precio_el else None

                # Amenidades (m², quartos, vagas)
                amenities_el = card.query_selector(
                    '.FindHouseCard_amenitiesText__QNzFn'
                )
                amenities_text = amenities_el.inner_text().strip() if amenities_el else ""
                amenities = parse_amenities(amenities_text)

                item = {
                    "tipo": modalidad,
                    "categoria": tipo,
                    "titulo": titulo,
                    "precio": precio,
                    "ubicacion": ciudad,
                    "m2": amenities["m2"],
                    "quartos": amenities["quartos"],
                    "vagas": amenities["vagas"],
                }
                results.append(item)
                print(f"  [{idx + 1}] {titulo or '(sin título)'} — {precio or '(sin precio)'}")

            except Exception as e:
                print(f"  Error en tarjeta {idx + 1}: {e}")
                continue

        browser.close()

    return results


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scraper QuintoAndar Brasil con Playwright"
    )
    parser.add_argument(
        "--modalidad",
        choices=MODALIDADES_DISPONIBLES,
        default="alugar",
        help="Modalidad: alugar o comprar (default: alugar)",
    )
    parser.add_argument(
        "--ciudad",
        default="sao-paulo-sp-brasil",
        help="Ciudad en formato slug, ej: sao-paulo-sp-brasil (default: sao-paulo-sp-brasil)",
    )
    parser.add_argument(
        "--tipo",
        choices=TIPOS_DISPONIBLES,
        default="apartamento",
        help="Tipo de inmueble: apartamento o casa (default: apartamento)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Archivo JSON de salida (default: quintoandar_<ciudad>_<tipo>.json)",
    )
    parser.add_argument(
        "-max", "--max",
        type=int,
        default=100,
        help="Máximo de ítems a extraer (default: 100)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        dest="no_headless",
        help="Mostrar el navegador (desactiva modo headless)",
    )
    args = parser.parse_args()

    url = BASE_URL.format(
        modalidad=args.modalidad,
        ciudad=args.ciudad,
        tipo=args.tipo,
    )

    output_file = args.output or f"quintoandar_{args.modalidad}_{args.ciudad}_{args.tipo}.json"

    print("=" * 60)
    print(f"  QuintoAndar Scraper")
    print(f"  URL       : {url}")
    print(f"  Modalidad : {args.modalidad}")
    print(f"  Ciudad    : {args.ciudad}")
    print(f"  Tipo      : {args.tipo}")
    print(f"  Max items : {args.max}")
    print(f"  Output    : {output_file}")
    print("=" * 60)

    data = scrape_page(
        url=url,
        modalidad=args.modalidad,
        ciudad=args.ciudad,
        tipo=args.tipo,
        headless=not args.no_headless,
        max_items=args.max,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nGuardados {len(data)} ítems en '{output_file}'")


if __name__ == "__main__":
    main()
