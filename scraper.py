"""
Web Scraper para MetroCuadrado - Inmuebles en Neiva
Este script extrae información de propiedades y la exporta a CSV
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime

class MetroCuadradoScraper:
    def __init__(self):
        self.base_url = "https://www.metrocuadrado.com/inmuebles/neiva/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.propiedades = []
    
    def obtener_propiedades(self, num_paginas=1):
        """Extrae información de propiedades de MetroCuadrado"""
        
        print(f"Iniciando scraping de {num_paginas} página(s)...")
        
        for pagina in range(1, num_paginas + 1):
            url = f"{self.base_url}?page={pagina}" if pagina > 1 else self.base_url
            print(f"\nExtrayendo página {pagina}: {url}")
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar los contenedores de propiedades
                # NOTA: Estos selectores pueden necesitar ajuste según la estructura actual del sitio
                listado = soup.find_all('div', class_='card-detail')
                
                if not listado:
                    print("No se encontraron propiedades con el selector actual.")
                    print("La estructura del sitio puede haber cambiado.")
                
                for item in listado:
                    try:
                        propiedad = self.extraer_datos_propiedad(item)
                        if propiedad:
                            self.propiedades.append(propiedad)
                    except Exception as e:
                        print(f"Error al extraer propiedad: {e}")
                        continue
                
                print(f"Propiedades encontradas en esta página: {len(listado)}")
                
                # Pausa entre requests para no sobrecargar el servidor
                if pagina < num_paginas:
                    time.sleep(2)
                    
            except requests.exceptions.RequestException as e:
                print(f"Error al obtener la página {pagina}: {e}")
                continue
        
        print(f"\n✓ Total de propiedades extraídas: {len(self.propiedades)}")
        return self.propiedades
    
    def extraer_datos_propiedad(self, item):
        """Extrae los datos individuales de cada propiedad"""
        
        # Título
        titulo_elem = item.find('h2', class_='card-title') or item.find('a', class_='card-title')
        titulo = titulo_elem.get_text(strip=True) if titulo_elem else "N/A"
        
        # Precio
        precio_elem = item.find('div', class_='card-price') or item.find('span', class_='price')
        precio = precio_elem.get_text(strip=True) if precio_elem else "N/A"
        
        # Ubicación
        ubicacion_elem = item.find('div', class_='card-location') or item.find('span', class_='location')
        ubicacion = ubicacion_elem.get_text(strip=True) if ubicacion_elem else "N/A"
        
        # Área
        area_elem = item.find('span', class_='area')
        area = area_elem.get_text(strip=True) if area_elem else "N/A"
        
        # Habitaciones
        habitaciones_elem = item.find('span', class_='rooms')
        habitaciones = habitaciones_elem.get_text(strip=True) if habitaciones_elem else "N/A"
        
        # Baños
        banos_elem = item.find('span', class_='bathrooms')
        banos = banos_elem.get_text(strip=True) if banos_elem else "N/A"
        
        # Link
        link_elem = item.find('a', href=True)
        link = link_elem['href'] if link_elem else "N/A"
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
    
    def exportar_csv(self, nombre_archivo=None):
        """Exporta los datos a un archivo CSV"""
        
        if not self.propiedades:
            print("No hay propiedades para exportar.")
            return
        
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"propiedades_neiva_{timestamp}.csv"
        
        try:
            with open(nombre_archivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
                campos = ['titulo', 'precio', 'ubicacion', 'area', 'habitaciones', 'banos', 'link', 'fecha_extraccion']
                writer = csv.DictWriter(csvfile, fieldnames=campos)
                
                writer.writeheader()
                writer.writerows(self.propiedades)
            
            print(f"\n✓ Datos exportados exitosamente a: {nombre_archivo}")
            print(f"  Total de registros: {len(self.propiedades)}")
            
        except Exception as e:
            print(f"Error al exportar CSV: {e}")


def main():
    """Función principal"""
    print("="*60)
    print("   SCRAPER DE PROPIEDADES - METROCUADRADO NEIVA")
    print("="*60)
    
    scraper = MetroCuadradoScraper()
    
    # Extraer propiedades (puedes cambiar el número de páginas)
    scraper.obtener_propiedades(num_paginas=2)
    
    # Exportar a CSV
    scraper.exportar_csv()
    
    print("\n" + "="*60)
    print("   PROCESO COMPLETADO")
    print("="*60)


if __name__ == "__main__":
    main()
