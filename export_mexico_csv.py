import os
import json
import pandas as pd
from pathlib import Path

def extraer_tipo_desde_nombre(nombre_archivo):
    """
    Extrae el tipo (venta o renta) del nombre del archivo.
    Ejemplo: inmueble-propiedades-renta-casas-df-11 -> renta
    El tipo está en la tercera posición (índice 2) al separar por guiones.
    """
    # Quitar la extensión .json
    nombre_sin_extension = nombre_archivo.replace('.json', '')
    # Separar por guiones
    partes = nombre_sin_extension.split('-')
    # El tipo está en la posición 2 (tercera palabra)
    if len(partes) >= 3:
        return partes[2]  # renta o venta
    return "desconocido"

def exportar_mexico_a_csv():
    # Ruta de la carpeta mexico
    carpeta_mexico = Path(__file__).parent / "mexico"
    
    # Lista para almacenar todos los datos
    todos_los_datos = []
    
    # Contar archivos procesados
    archivos_procesados = 0
    
    # Recorrer todos los archivos JSON en la carpeta mexico
    for archivo in carpeta_mexico.glob("*.json"):
        try:
            # Extraer el tipo del nombre del archivo
            tipo = extraer_tipo_desde_nombre(archivo.name)
            
            # Leer el contenido del archivo JSON
            with open(archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            # Si es una lista de objetos
            if isinstance(datos, list):
                for item in datos:
                    # Agregar la columna tipo
                    item['tipo'] = tipo
                    # Agregar el nombre del archivo fuente (opcional)
                    #item['archivo_fuente'] = archivo.name
                    todos_los_datos.append(item)
            # Si es un solo objeto
            elif isinstance(datos, dict):
                datos['tipo'] = tipo
                datos['archivo_fuente'] = archivo.name
                todos_los_datos.append(datos)
            
            archivos_procesados += 1
            
        except Exception as e:
            print(f"Error al procesar {archivo.name}: {e}")
    
    # Crear DataFrame
    df = pd.DataFrame(todos_los_datos)
    
    # Reorganizar columnas para que 'tipo' esté al principio
    if 'tipo' in df.columns:
        columnas = ['tipo'] + [col for col in df.columns if col != 'tipo']
        df = df[columnas]
    
    # Exportar a CSV
    archivo_salida = Path(__file__).parent / "mexico_inmuebles_export.csv"
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    
    print(f"\n{'='*60}")
    print(f"EXPORTACIÓN COMPLETADA")
    print(f"{'='*60}")
    print(f"Archivos procesados: {archivos_procesados}")
    print(f"Total de registros: {len(todos_los_datos)}")
    print(f"Archivo exportado: {archivo_salida}")
    print(f"\nDistribución por tipo:")
    print(df['tipo'].value_counts().to_string())
    print(f"\nColumnas en el archivo:")
    print(", ".join(df.columns.tolist()))

if __name__ == "__main__":
    exportar_mexico_a_csv()
