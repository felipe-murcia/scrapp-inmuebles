import os
import json
from pathlib import Path

def contar_inmuebles_mexico():
    """
    Lee la carpeta 'mexico' y cuenta:
    - Total de archivos JSON
    - Total de registros (inmuebles) en todos los arrays
    """
    # Obtener el directorio actual del script
    directorio_actual = Path(__file__).parent
    carpeta_mexico = directorio_actual / "mexico"
    
    # Verificar que la carpeta existe
    if not carpeta_mexico.exists():
        print(f"Error: La carpeta '{carpeta_mexico}' no existe.")
        return
    
    total_archivos_json = 0
    total_registros = 0
    archivos_con_error = []
    
    # Recorrer todos los archivos en la carpeta mexico
    for archivo in carpeta_mexico.iterdir():
        if archivo.suffix.lower() == '.json':
            total_archivos_json += 1
            
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    
                    # Si es una lista, contar los elementos
                    if isinstance(datos, list):
                        total_registros += len(datos)
                    # Si es un diccionario, contar como 1 registro
                    elif isinstance(datos, dict):
                        total_registros += 1
                        
            except json.JSONDecodeError as e:
                archivos_con_error.append((archivo.name, f"Error JSON: {e}"))
            except Exception as e:
                archivos_con_error.append((archivo.name, str(e)))
    
    # Mostrar resultados
    print("=" * 50)
    print("CONTEO DE INMUEBLES - CARPETA MEXICO")
    print("=" * 50)
    print(f"Total de archivos JSON: {total_archivos_json}")
    print(f"Total de registros (inmuebles): {total_registros}")
    print("=" * 50)
    
    if archivos_con_error:
        print("\nArchivos con errores:")
        for nombre, error in archivos_con_error:
            print(f"  - {nombre}: {error}")

if __name__ == "__main__":
    contar_inmuebles_mexico()
