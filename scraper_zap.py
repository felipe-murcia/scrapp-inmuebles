"""
Scraper para Zap Imoveis (Brasil) usando Playwright sync API.
Extrae propiedades por modalidad, tipo y ciudad con paginacion automatica.
"""

import argparse
import json

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


MODALIDADES_DISPONIBLES = ["aluguel", "venda", "lancamentos"]
TIPOS_DISPONIBLES = ["apartamentos", "casas", "loja-salao", "terrenos", "comercial"]
BASE_URL = "https://www.zapimoveis.com.br/{modalidad}/{tipo}/{ciudad}/"


def build_url(modalidad: str, tipo: str, ciudad: str, pagina: int) -> str:
    url = BASE_URL.format(modalidad=modalidad, tipo=tipo, ciudad=ciudad)
    tipo_singular = tipo[:-1] if tipo.endswith("s") else tipo
    params = [f"tipos={tipo_singular}_residencial"]
    if pagina > 1:
        params.append(f"pagina={pagina}")
    return url + "?" + "&".join(params)


def text_or_none(element) -> str | None:
    if not element:
        return None
    text = element.inner_text().strip()
    return text or None


def scrape_page(page, modalidad: str, tipo: str, ciudad: str, pagina: int) -> list[dict]:
    results = []
    url = build_url(modalidad, tipo, ciudad, pagina)
    print(f"  Abriendo pagina {pagina}: {url}")

    page.goto(url, timeout=90000, wait_until="domcontentloaded")

    try:
        page.wait_for_selector('li[data-cy="rp-property-cd"]', timeout=15000)
    except PlaywrightTimeoutError:
        print("  No se encontraron tarjetas en la pagina.")
        return results

    cards = page.query_selector_all('li[data-cy="rp-property-cd"]')
    print(f"  Tarjetas encontradas: {len(cards)}")

    for idx, card in enumerate(cards, start=1):
        try:
            titulo = text_or_none(card.query_selector('h2[data-cy="rp-cardProperty-location-txt"]'))
            if not titulo:
                titulo = card.get_attribute("title")
            if not titulo:
                titulo = text_or_none(card.query_selector("a[title]"))

            precio = text_or_none(card.query_selector('[data-cy="rp-cardProperty-price-txt"] .typo-title-small'))
            if not precio:
                precio = text_or_none(card.query_selector('[data-cy="rp-cardProperty-price-txt"]'))

            item = {
                "categoria": tipo,
                "titulo": titulo,
                "precio": precio,
                "ubicacion": ciudad,
                "tipo": modalidad,
                "m2": text_or_none(card.query_selector('li[data-cy="rp-cardProperty-propertyArea-txt"]')),
                "vagas": text_or_none(card.query_selector('li[data-cy="rp-cardProperty-bathroomQuantity-txt"]')),
                "quartos": text_or_none(card.query_selector('li[data-cy="rp-cardProperty-bedroomQuantity-txt"]')),
            }
            results.append(item)
            print(f"    [{idx}] {item['titulo'] or '(sin titulo)'} - {item['precio'] or '(sin precio)'}")
        except Exception as error:
            print(f"    Error en tarjeta {idx}: {error}")

    return results


def scrape(
    modalidad: str,
    tipo: str,
    ciudad: str,
    max_items: int = 100,
    headless: bool = True,
) -> list[dict]:
    all_results = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            extra_http_headers={"Accept-Language": "pt-BR,pt;q=0.9"},
        )
        page = context.new_page()

        pagina = 1
        while len(all_results) < max_items:
            page_results = scrape_page(page, modalidad, tipo, ciudad, pagina)
            if not page_results:
                break
            all_results.extend(page_results)
            if len(page_results) < 24:
                break
            pagina += 1

        browser.close()

    return all_results[:max_items]


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper Zap Imoveis Brasil con Playwright")
    parser.add_argument("--modalidad", choices=MODALIDADES_DISPONIBLES, default="aluguel")
    parser.add_argument("--tipo", choices=TIPOS_DISPONIBLES, default="apartamentos")
    parser.add_argument("--ciudad", default="ce+fortaleza")
    parser.add_argument("--output", default=None)
    parser.add_argument("-max", "--max", type=int, default=100)
    parser.add_argument("--no-headless", action="store_true", dest="no_headless")
    args = parser.parse_args()

    output_file = args.output or f"zap_{args.modalidad}_{args.ciudad.replace('+', '-')}_{args.tipo}.json"
    results = scrape(
        modalidad=args.modalidad,
        tipo=args.tipo,
        ciudad=args.ciudad,
        max_items=args.max,
        headless=not args.no_headless,
    )

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print(f"Guardados {len(results)} items en '{output_file}'")


if __name__ == "__main__":
    main()