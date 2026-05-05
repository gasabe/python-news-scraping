# python-news-scraping


### Responsabilidad de cada modulo

- `src/main.py`: punto de entrada del script. Lee argumentos, coordina la
  busqueda, filtra resultados por palabra clave y guarda el CSV.
- `src/scraper.py`: construye la URL de busqueda y usa Playwright para obtener
  enlaces de noticias.
- `src/parser.py`: extrae autor, fecha, titulo, descripcion, imagen y URL desde
  cada noticia.
- `src/storage.py`: guarda la informacion extraida en un archivo CSV.
- `src/utils.py`: contiene funciones auxiliares para requests, URLs absolutas y
  pausas entre peticiones.

## Instalacion

Clonar el repositorio:

```bash
git clone https://github.com/gasabe/python-news-scraping.git
cd python-news-scraping
```

Crear y activar un entorno virtual:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

Instalar las dependencias del proyecto:

```powershell
pip install -r requirements.txt
```

Instalar los navegadores necesarios para Playwright:

```powershell
playwright install
```

## Uso

### Caso 1: busqueda interactiva

Si no se pasa una palabra clave por argumento, el programa la solicita por
consola:

```powershell
py src/main.py
```

Ejemplo:

```text
Ingrese una palabra clave: economia
```

### Caso 2: busqueda por argumento

Tambien se puede indicar la palabra clave directamente:

```powershell
py src/main.py --keyword "economia"
```

Forma corta:

```powershell
py src/main.py -k "economia"
```

### Caso 3: limitar la cantidad de noticias a guardar

Por defecto se guardan hasta 10 noticias. Ese limite se puede modificar con
`--max-results`:

```powershell
py src/main.py --keyword "economia" --max-results 5
```

Forma corta:

```powershell
py src/main.py -k "economia" -n 5
```

### Caso 4: usar otra URL de busqueda

Por defecto el script usa el buscador de Perfil:

```powershell
py src/main.py --keyword "politica" --url "https://www.perfil.com"
```

Tambien se puede pasar una plantilla de busqueda completa usando `{keyword}`:

```powershell
py src/main.py --keyword "politica" --url "https://www.perfil.com/buscador?q={keyword}#gsc.tab=0&gsc.q={keyword}&gsc.page=1"
```

Importante: cambiar la URL no alcanza para soportar cualquier diario. Cada sitio
puede tener una ruta de busqueda, selectores HTML y formato de enlaces distintos.
La extraccion de enlaces actual sigue pensada para resultados de Perfil /
Google Custom Search.

## Salida generada

Los resultados se guardan en la carpeta `data/` con un nombre basado en la
palabra clave buscada:

```text
data/noticias_economia.csv
data/noticias_politica.csv
```

El CSV contiene las columnas pedidas por la consigna:

```text
autor,fecha_publicacion,titulo,descripcion,url_imagen,url_noticia
```

Ejemplo de ejecucion:

```powershell
py src/main.py --keyword "economia" --max-results 10
```

Ejemplo de salida en consola:

```text
Buscando noticias relacionadas con: economia
URL de busqueda: https://www.perfil.com/buscador?q=economia#gsc.tab=0&gsc.q=economia&gsc.page=1
Se encontraron 2 enlaces para analizar.
[1/2] Extrayendo: https://www.perfil.com/noticias/deportes/...
Proceso finalizado. Archivo generado: data/noticias_economia.csv
```

## Criterios de filtrado

La consigna pide extraer articulos que contengan una palabra clave determinada
en el titulo o descripcion.

En este proyecto el filtro se aplica sobre:

- titulo
- descripcion
- URL de la noticia

La URL se incluye como apoyo porque en algunos portales la seccion o tema de la
noticia aparece en la direccion aunque no siempre figure de forma literal en el
titulo o la descripcion.

El filtro tambien normaliza texto para comparar sin distinguir mayusculas,
minusculas ni acentos. Por ejemplo:

```text
"Economia" coincide con "economia"
"dolar" coincide con "dolar"
"economia" coincide aunque las palabras aparezcan separadas
```

## Scraping responsable

Para reducir la posibilidad de bloqueo y evitar sobrecargar el sitio, el script
incluye:

- User-Agent similar al de un navegador real.
- Timeouts en las peticiones HTTP.
- Pausas entre requests mediante `polite_delay`.
- Uso de Playwright solo para cargar el buscador dinamico.

Pendiente de mejora:

- Consultar y respetar `robots.txt` de forma automatizada antes de scrapear.
- Hacer configurable el delay entre peticiones.
- Agregar reintentos controlados ante errores temporales.

## Limitaciones actuales

- El scraper esta adaptado al buscador y estructura actual de Perfil.
- `--url` puede cambiar la direccion de busqueda, pero no convierte el scraper
  en generico para cualquier portal.
- Si el sitio cambia sus selectores, metadatos o comportamiento del buscador,
  puede requerir ajustes.
- La extraccion de articulos es secuencial, por lo que puede ser lenta si se
  analizan muchas noticias.
- No hay tests automatizados todavia.
- No se incluye Dockerfile en esta primera version.
