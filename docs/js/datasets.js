/*
 * Listado de tablas del INE incluidas en Extremadura en Datos.
 * Cada entrada contiene el identificador de la tabla (`id`), la categoría,
 * la métrica, la periodicidad y el ámbito geográfico (GEO).  Este fichero
 * se genera a partir del Excel de configuración y se utiliza en la web
 * para construir el selector de indicadores.
 */

const DATASETS = [
  { id: "50913", category: "Precios", metric: "IPC Base 2021", periodicity: "Mensual", geo: "CCAA" },
  { id: "13912", category: "Industria y Empresa", metric: "Resumen de sociedades mercantiles", periodicity: "Mensual", geo: "CCAA" },
  { id: "13913", category: "Industria y Empresa", metric: "Sociedades mercantiles constituídas", periodicity: "Mensual", geo: "CCAA" },
  { id: "13923", category: "Industria y Empresa", metric: "Sociedades mercantiles disueltas", periodicity: "Mensual", geo: "Provincia" },
  { id: "26061", category: "Industria y Empresa", metric: "Índice de Producción Industrial. (Base 2015)", periodicity: "Mensual", geo: "CCAA" },
  { id: "26002", category: "Industria y Empresa", metric: "Índices de cifras de negocios en la industria (Base 2015)", periodicity: "Mensual", geo: "CCAA" },
  { id: "25992", category: "Industria y Empresa", metric: "Índice de cifra de negocios comercio al por menor (Precios Constantes)", periodicity: "Mensual", geo: "CCAA" },
  { id: "8027", category: "Industria y Empresa", metric: "Situación, expectativas e indice de confianza", periodicity: "Trimestral", geo: "CCAA" },
  { id: "2941", category: "Turismo", metric: "Viajeros, pernoctaciones por tipo de alojamiento", periodicity: "Mensual", geo: "CCAA" },
  { id: "2074", category: "Turismo", metric: "Viajeros y pernoctaciones totales", periodicity: "Mensual", geo: "CCAA" },
  { id: "2942", category: "Turismo", metric: "Establecimientos estimados, plazas estimadas y personal empleado por tipo de alojamiento", periodicity: "Mensual", geo: "CCAA" },
  { id: "2940", category: "Turismo", metric: "Estancia media, por tipo de alojamiento", periodicity: "Mensual", geo: "CCAA" },
  { id: "10839", category: "Turismo", metric: "Gasto de los turistas internacionales", periodicity: "Mensual", geo: "CCAA" },
  { id: "3204", category: "Vivienda", metric: "Hipotecas constituidas sobre fincas urbanas por entidad que concede el préstamo", periodicity: "Mensual", geo: "Provincia" },
  { id: "6150", category: "Vivienda", metric: "Compraventa de viviendas según régimen y estado", periodicity: "Mensual", geo: "CCAA y Provincia" },
  { id: "6149", category: "Vivienda", metric: "Viviendas transmitidas según título de adquisición", periodicity: "Mensual", geo: "CCAA y Provincia" },
  { id: "25171", category: "Vivienda", metric: "Índice de Precios de Vivienda (IPV). Base 2015", periodicity: "Trimestral", geo: "CCAA" },
  { id: "6147", category: "Vivienda", metric: "Total fincas rústicas transmitidas según título de adquisición", periodicity: "Mensual", geo: "CCAA y Provincia" },
  { id: "6062", category: "Empleo", metric: "Coste laboral por hora efectiva, comunidad autónoma, sectores de actividad", periodicity: "Trimestral", geo: "CCAA" },
  { id: "6063", category: "Empleo", metric: "Tiempo de trabajo por trabajador y mes por comunidad autónoma, tipo de jornada, sectores de actividad", periodicity: "Trimestral", geo: "CCAA" },
  { id: "3996", category: "Empleo", metric: "Tasas de actividad, paro y empleo por provincia y sexo", periodicity: "Trimestral", geo: "Provincia" }
];