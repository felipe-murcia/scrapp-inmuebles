const fs = require('fs');
const path = require('path');

// Carpeta donde están los archivos JSON
const carpetaMexico = path.join(__dirname, 'mexico');

// Archivos de salida
const archivoSalida = path.join(__dirname, 'mexico_inmuebles_consolidado.json');
const archivoSalidaConDuplicados = path.join(__dirname, 'mexico_inmuebles_con_duplicados.json');
const archivoSalidaCSV = path.join(__dirname, 'mexico_inmuebles_consolidado.csv');

/**
 * Determina el tipo de inmueble (renta o venta) basándose en el nombre del archivo
 * @param {string} nombreArchivo - Nombre del archivo JSON
 * @returns {string} - 'renta' o 'venta'
 */
function determinarTipo(nombreArchivo) {
    const nombreLower = nombreArchivo.toLowerCase();
    if (nombreLower.includes('-renta-')) {
        return 'renta';
    } else if (nombreLower.includes('-venta-')) {
        return 'venta';
    }
    return 'desconocido';
}

/**
 * Genera una clave única para un inmueble excluyendo el campo "tipo" y "estado"
 * @param {object} inmueble - Objeto inmueble
 * @returns {string} - Clave única basada en los campos del inmueble
 */
function generarClaveUnica(inmueble) {
    // Crear copia sin el campo "tipo" y "estado"
    const { tipo, estado, ...sinTipoNiEstado } = inmueble;
    return JSON.stringify(sinTipoNiEstado);
}

/**
 * Elimina duplicados del array de inmuebles, manteniendo el campo "tipo"
 * Si hay duplicados, se prioriza el que tiene el atributo "estado"
 * @param {array} inmuebles - Array de inmuebles
 * @returns {array} - Array sin duplicados
 */
function eliminarDuplicados(inmuebles) {
    const vistos = new Map();
    let duplicadosEliminados = 0;

    console.log('\n--- REGISTROS DUPLICADOS ELIMINADOS ---');

    inmuebles.forEach(inmueble => {
        const clave = generarClaveUnica(inmueble);
        const claveConTipo = `${clave}_${inmueble.tipo}`;
        
        if (!vistos.has(claveConTipo)) {
            // Primera vez que vemos este registro
            vistos.set(claveConTipo, inmueble);
        } else {
            // Ya existe un duplicado, verificar cuál tiene "estado"
            const existente = vistos.get(claveConTipo);
            const existenteTieneEstado = existente.estado !== undefined && existente.estado !== null && existente.estado !== '';
            const nuevoTieneEstado = inmueble.estado !== undefined && inmueble.estado !== null && inmueble.estado !== '';
            
            let eliminado;
            if (!existenteTieneEstado && nuevoTieneEstado) {
                // El nuevo tiene estado y el existente no, reemplazar
                eliminado = existente;
                vistos.set(claveConTipo, inmueble);
                console.log(`[${duplicadosEliminados + 1}] ELIMINADO (sin estado): ${eliminado.titulo || 'Sin título'}`);
                console.log(`    Tipo: ${eliminado.tipo} | Precio: ${eliminado.precio || 'N/A'} | Ubicación: ${eliminado.ubicacion || 'N/A'}`);
            } else {
                // Se elimina el nuevo, se queda el existente
                eliminado = inmueble;
                console.log(`[${duplicadosEliminados + 1}] ELIMINADO: ${eliminado.titulo || 'Sin título'}`);
                console.log(`    Tipo: ${eliminado.tipo} | Precio: ${eliminado.precio || 'N/A'} | Ubicación: ${eliminado.ubicacion || 'N/A'}`);
            }
            duplicadosEliminados++;
        }
    });

    console.log('--- FIN DUPLICADOS ---\n');

    const sinDuplicados = Array.from(vistos.values());
    console.log(`\nTotal duplicados eliminados: ${duplicadosEliminados}`);
    return sinDuplicados;
}

/**
 * Escapa un valor para CSV (maneja comas, comillas y saltos de línea)
 * @param {any} valor - Valor a escapar
 * @returns {string} - Valor escapado para CSV
 */
function escaparCSV(valor) {
    if (valor === null || valor === undefined) {
        return '';
    }
    const str = String(valor);
    // Si contiene comas, comillas o saltos de línea, envolver en comillas
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
        return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
}

/**
 * Exporta un array de objetos a formato CSV
 * @param {array} datos - Array de objetos a exportar
 * @param {string} rutaArchivo - Ruta del archivo CSV de salida
 */
function exportarCSV(datos, rutaArchivo) {
    if (datos.length === 0) {
        console.log('No hay datos para exportar a CSV.');
        return;
    }

    // Obtener todas las columnas únicas de todos los objetos
    const columnas = [...new Set(datos.flatMap(obj => Object.keys(obj)))];
    
    // Crear cabecera
    const cabecera = columnas.map(col => escaparCSV(col)).join(',');
    
    // Crear filas
    const filas = datos.map(obj => {
        return columnas.map(col => escaparCSV(obj[col])).join(',');
    });

    // Unir todo
    const contenidoCSV = [cabecera, ...filas].join('\n');
    
    // Guardar archivo con BOM para Excel
    fs.writeFileSync(rutaArchivo, '\ufeff' + contenidoCSV, 'utf-8');
    console.log(`Archivo CSV guardado: ${rutaArchivo}`);
}

/**
 * Lee todos los archivos JSON de la carpeta mexico y los combina
 */
function combinarJsons() {
    console.log('Iniciando proceso de combinación de archivos JSON...\n');
    
    // Verificar que la carpeta existe
    if (!fs.existsSync(carpetaMexico)) {
        console.error(`Error: La carpeta "${carpetaMexico}" no existe.`);
        process.exit(1);
    }

    // Obtener todos los archivos .json de la carpeta
    const archivos = fs.readdirSync(carpetaMexico).filter(archivo => 
        archivo.endsWith('.json')
    );

    console.log(`Se encontraron ${archivos.length} archivos JSON.\n`);

    // Array para almacenar todos los inmuebles combinados
    let todosLosInmuebles = [];
    let contadorRenta = 0;
    let contadorVenta = 0;
    let contadorDesconocido = 0;

    // Procesar cada archivo
    archivos.forEach((archivo, index) => {
        const rutaArchivo = path.join(carpetaMexico, archivo);
        const tipo = determinarTipo(archivo);

        try {
            // Leer y parsear el archivo JSON
            const contenido = fs.readFileSync(rutaArchivo, 'utf-8');
            const inmuebles = JSON.parse(contenido);

            // Verificar que sea un array
            if (!Array.isArray(inmuebles)) {
                console.warn(`Advertencia: ${archivo} no contiene un array. Saltando...`);
                return;
            }

            // Agregar el campo "tipo" a cada inmueble y añadir al array principal
            const inmueblesConTipo = inmuebles.map(inmueble => ({
                ...inmueble,
                tipo: tipo,
            }));

            todosLosInmuebles = todosLosInmuebles.concat(inmueblesConTipo);

            // Contar por tipo
            if (tipo === 'renta') {
                contadorRenta += inmuebles.length;
            } else if (tipo === 'venta') {
                contadorVenta += inmuebles.length;
            } else {
                contadorDesconocido += inmuebles.length;
            }

            // Mostrar progreso cada 50 archivos
            if ((index + 1) % 50 === 0) {
                console.log(`Procesados ${index + 1}/${archivos.length} archivos...`);
            }

        } catch (error) {
            console.error(`Error procesando ${archivo}: ${error.message}`);
        }
    });

    // Guardar archivo con duplicados (antes de eliminar)
    console.log('\nGuardando archivo CON duplicados (para comparación)...');
    fs.writeFileSync(archivoSalidaConDuplicados, JSON.stringify(todosLosInmuebles, null, 2), 'utf-8');
    console.log(`Archivo guardado: ${archivoSalidaConDuplicados}`);

    // Eliminar duplicados
    console.log('\nEliminando duplicados...');
    const totalAntesDeDuplicados = todosLosInmuebles.length;
    todosLosInmuebles = eliminarDuplicados(todosLosInmuebles);

    // Recontar por tipo después de eliminar duplicados
    contadorRenta = todosLosInmuebles.filter(i => i.tipo === 'renta').length;
    contadorVenta = todosLosInmuebles.filter(i => i.tipo === 'venta').length;
    contadorDesconocido = todosLosInmuebles.filter(i => i.tipo === 'desconocido').length;

    // Guardar el archivo combinado
    console.log('\nGuardando archivo SIN duplicados (final)...');
    fs.writeFileSync(archivoSalida, JSON.stringify(todosLosInmuebles, null, 2), 'utf-8');

    // Exportar a CSV
    console.log('\nExportando a CSV...');
    exportarCSV(todosLosInmuebles, archivoSalidaCSV);

    // Mostrar resumen
    console.log('\n========== RESUMEN ==========');
    console.log(`Total de archivos procesados: ${archivos.length}`);
    console.log(`Total de inmuebles antes de eliminar duplicados: ${totalAntesDeDuplicados}`);
    console.log(`Total de inmuebles después de eliminar duplicados: ${todosLosInmuebles.length}`);
    console.log(`  - Renta: ${contadorRenta}`);
    console.log(`  - Venta: ${contadorVenta}`);
    if (contadorDesconocido > 0) {
        console.log(`  - Desconocido: ${contadorDesconocido}`);
    }
    console.log(`\nArchivos generados:`);
    console.log(`  - Con duplicados (JSON): ${archivoSalidaConDuplicados}`);
    console.log(`  - Sin duplicados (JSON): ${archivoSalida}`);
    console.log(`  - Sin duplicados (CSV):  ${archivoSalidaCSV}`);
    console.log('==============================');
}

// Ejecutar la función principal
combinarJsons();
