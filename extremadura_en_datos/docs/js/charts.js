/*
 * Funciones de visualización para Extremadura en Datos.
 *
 * Este módulo depende de Chart.js (versión 4) y utiliza el API de
 * `fetch()` para cargar los datos JSON generados por los scripts de
 * Python.  Cada fichero JSON es un array de objetos con las
 * propiedades `Fecha` y `Valor` además de otras dimensiones.  La
 * propiedad `Fecha` debe encontrarse en formato ISO (ej. '2025-09-01T00:00:00').
 */

/**
 * Dibuja un gráfico de líneas en un elemento canvas con Chart.js.
 *
 * @param {string} canvasId ID del elemento `<canvas>` donde se dibujará la gráfica.
 * @param {string[]} labels Array de etiquetas para el eje X (fechas en formato legible).
 * @param {number[]} data Array de valores numéricos correspondientes a cada fecha.
 * @param {string} title Título que aparecerá encima de la gráfica.
 */
function createLineChart(canvasId, labels, data, title) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  // Destruir gráfico anterior si existe
  if (window.chartInstance) {
    window.chartInstance.destroy();
  }
  window.chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: title,
          data: data,
          borderColor: '#0070c0',
          backgroundColor: 'rgba(0,112,192,0.1)',
          tension: 0.1,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: {
            display: true,
            text: 'Fecha',
          },
        },
        y: {
          title: {
            display: true,
            text: 'Valor',
          },
        },
      },
    },
  });
}

/**
 * Carga los datos de un indicador desde un fichero JSON y dibuja la gráfica.
 *
 * @param {string} tableId Identificador de la tabla (p. ej. '50913').
 * @param {string} metric Nombre de la métrica (para mostrar en el título).
 */
async function loadDatasetAndDraw(tableId, metric) {
  try {
    const response = await fetch(`../data/processed/${tableId}.json`);
    if (!response.ok) {
      throw new Error('No se pudo cargar el fichero');
    }
    const jsonData = await response.json();
    // Ordenar por fecha ascendente
    jsonData.sort((a, b) => new Date(a.Fecha) - new Date(b.Fecha));
    const labels = jsonData.map(item => {
      const d = new Date(item.Fecha);
      return d.toLocaleDateString('es-ES', { year: 'numeric', month: 'short' });
    });
    const values = jsonData.map(item => item.Valor);
    createLineChart('chart-canvas', labels, values, metric);
  } catch (err) {
    console.error(err);
    alert('Error al cargar los datos de la tabla ' + tableId);
  }
}

/**
 * Inicializa el selector de indicadores en la página y añade sus
 * correspondientes manejadores de eventos.
 */
function initDatasetSelector() {
  const select = document.getElementById('dataset-select');
  // Añadir opciones agrupadas por categoría
  const categories = {};
  DATASETS.forEach(ds => {
    if (!categories[ds.category]) {
      categories[ds.category] = [];
    }
    categories[ds.category].push(ds);
  });
  for (const cat in categories) {
    const optgroup = document.createElement('optgroup');
    optgroup.label = cat;
    categories[cat].forEach(ds => {
      const option = document.createElement('option');
      option.value = ds.id;
      option.textContent = ds.metric;
      option.dataset.metric = ds.metric;
      optgroup.appendChild(option);
    });
    select.appendChild(optgroup);
  }
  // Manejador de cambio
  select.addEventListener('change', event => {
    const selectedOption = event.target.selectedOptions[0];
    const tableId = selectedOption.value;
    const metric = selectedOption.dataset.metric;
    loadDatasetAndDraw(tableId, metric);
  });
  // Seleccionar la primera opción por defecto
  if (select.options.length > 0) {
    const first = select.options[0];
    first.selected = true;
    loadDatasetAndDraw(first.value, first.dataset.metric);
  }
}