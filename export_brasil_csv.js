const fs = require('node:fs');
const path = require('node:path');

const inputPath = path.join(__dirname, 'brasil_inmuebles.json');
const outputPath = path.join(__dirname, 'brasil_inmuebles.csv');

function escapeCsv(value) {
  if (value === null || value === undefined) return '';
  const str = String(value);
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replaceAll('"', '""')}"`;
  }
  return str;
}

function jsonToCsv() {
  if (!fs.existsSync(inputPath)) {
    console.error(`No se encontro el archivo: ${inputPath}`);
    process.exit(1);
  }

  const raw = fs.readFileSync(inputPath, 'utf-8');
  const data = JSON.parse(raw);

  if (!Array.isArray(data)) {
    console.error('El archivo JSON debe contener un arreglo de objetos.');
    process.exit(1);
  }

  if (data.length === 0) {
    fs.writeFileSync(outputPath, '', 'utf-8');
    console.log(`Archivo vacio generado: ${outputPath}`);
    return;
  }

  const headersSet = new Set();
  for (const row of data) {
    if (row && typeof row === 'object' && !Array.isArray(row)) {
      for (const key of Object.keys(row)) {
        headersSet.add(key);
      }
    }
  }

  const headers = Array.from(headersSet).sort((a, b) => a.localeCompare(b));
  const lines = [headers.map(escapeCsv).join(',')];

  for (const row of data) {
    const line = headers.map((header) => {
      const value = row && typeof row === 'object' ? row[header] : '';
      return escapeCsv(value);
    });
    lines.push(line.join(','));
  }

  // Se agrega BOM para mejorar apertura en Excel.
  fs.writeFileSync(outputPath, `\ufeff${lines.join('\n')}`, 'utf-8');

  console.log(`JSON leido: ${inputPath}`);
  console.log(`CSV generado: ${outputPath}`);
  console.log(`Filas exportadas: ${data.length}`);
  console.log(`Columnas: ${headers.length}`);
}

jsonToCsv();