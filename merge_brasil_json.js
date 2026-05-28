const fs = require('fs');
const path = require('path');

const carpetaBrasil = path.join(__dirname, 'brasil');
const archivoSalida = path.join(__dirname, 'brasil_inmuebles_consolidado.json');

function determinarTipo(nombreArchivo) {
  const nombre = nombreArchivo.toLowerCase();
  if (nombre.includes('_aluguel_')) return 'aluguel';
  if (nombre.includes('_venda_')) return 'venda';
  if (nombre.includes('_lancamentos_')) return 'lancamentos';
  return 'desconocido';
}

function normalizarValor(valor) {
  if (valor === null || valor === undefined) return '';
  return String(valor).replace(/\s+/g, ' ').trim().toLowerCase();
}

function claveDeduplicacion(registro) {
  // Si existe id/url/codigo, suele ser la forma mas estable de identificar un inmueble.
  const candidatoId = registro.id || registro.codigo || registro.code || registro.url || registro.link;
  if (candidatoId) {
    return `id:${normalizarValor(candidatoId)}`;
  }

  // Fallback: usar firma de contenido con valores normalizados.
  const normalizado = {};
  Object.keys(registro)
    .sort()
    .forEach((k) => {
      normalizado[k] = normalizarValor(registro[k]);
    });

  return `sig:${JSON.stringify(normalizado)}`;
}

function combinarBrasil() {
  if (!fs.existsSync(carpetaBrasil)) {
    console.error(`No existe la carpeta: ${carpetaBrasil}`);
    process.exit(1);
  }

  const archivos = fs
    .readdirSync(carpetaBrasil)
    .filter((a) => a.toLowerCase().endsWith('.json'));

  if (archivos.length === 0) {
    console.error('No se encontraron archivos JSON en la carpeta brasil.');
    process.exit(1);
  }

  const vistos = new Map();
  let totalLeidos = 0;
  let errores = 0;

  for (const archivo of archivos) {
    const ruta = path.join(carpetaBrasil, archivo);
    const tipoArchivo = determinarTipo(archivo);

    try {
      const contenido = fs.readFileSync(ruta, 'utf-8');
      const datos = JSON.parse(contenido);

      if (!Array.isArray(datos)) {
        console.warn(`Saltando ${archivo}: no contiene un arreglo JSON.`);
        continue;
      }

      for (const item of datos) {
        const registro = {
          ...item,
          tipo: item.tipo || tipoArchivo,
        };

        totalLeidos += 1;
        const clave = claveDeduplicacion(registro);
        if (!vistos.has(clave)) {
          vistos.set(clave, registro);
        }
      }
    } catch (error) {
      errores += 1;
      console.error(`Error leyendo ${archivo}: ${error.message}`);
    }
  }

  const consolidados = Array.from(vistos.values());
  fs.writeFileSync(archivoSalida, JSON.stringify(consolidados, null, 2), 'utf-8');

  console.log('============================================');
  console.log(`Archivos procesados: ${archivos.length}`);
  console.log(`Registros leidos: ${totalLeidos}`);
  console.log(`Registros unicos: ${consolidados.length}`);
  console.log(`Duplicados eliminados: ${totalLeidos - consolidados.length}`);
  console.log(`Archivos con error: ${errores}`);
  console.log(`Salida: ${archivoSalida}`);
  console.log('============================================');
}

combinarBrasil();