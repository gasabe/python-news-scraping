# python-news-scraping

Un script de Python que busca noticias en un portal de noticias según una
palabra clave, extrae la información relevante de cada artículo y guarda
los resultados en un archivo CSV.

Fue desarrollado como ejercicio de web scraping y resuelve los requisitos
principales: búsqueda por palabra clave, extracción de datos de artículos,
persistencia en CSV, modularización del código, manejo de `robots.txt`,
User-Agent, timeouts y uso de Playwright para el buscador dinámico.

## ¿Qué hace?

1. Busca noticias en Perfil.com usando la palabra clave que le indiques.
2. Entra a cada artículo encontrado y extrae el autor, fecha, título, descripción, imagen y URL.
3. Filtra las noticias si la palabra clave aparece en el título o en la descripción.
4. Guarda todo en un archivo CSV listo para abrir en Excel o Google Sheets.

## Instalación

**1. Clonar el repositorio:**

```bash
git clone https://github.com/gasabe/python-news-scraping.git
cd python-news-scraping
```

**2. Crear un entorno virtual:**

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

Si tu instalación no reconoce el comando `py`, podés usar `python`:

```powershell
python -m venv venv
```

Si estás en Mac o Linux, el comando para activarlo es:

```bash
source venv/bin/activate
```

**3. Instalar las dependencias:**

```powershell
pip install -r requirements.txt
```

**4. Instalar el navegador para Playwright:**

```powershell
playwright install
```

Esto descarga Chromium, que el scraper usa para interactuar con el buscador
dinámico de Perfil. Solo se ejecuta una vez.

## Uso

### Búsqueda rápida

```powershell
py src/main.py -k "donald trump"
```

### Búsqueda con límite de resultados

```powershell
py src/main.py -k "inteligencia artificial" -n 5
```

### Filtrar por un año específico

```powershell
py src/main.py -k "donald trump" --year 2025
```

### Noticias de cualquier año

```powershell
py src/main.py -k "elon musk"
```

### Modo interactivo

Si no le pasás una palabra clave con `-k`, el programa te la pide por consola:

```powershell
py src/main.py
```

```text
Ingrese una palabra clave: economia
```

### Combinar opciones

Podés usar varios argumentos juntos:

```powershell
py src/main.py -k "donald trump" -n 3 --year 2025
```

El filtro por año es opcional. Si no indicás `--year`, el script guarda
noticias de cualquier año.

## Argumentos disponibles

| Argumento | Corto | Descripción | Por defecto |
|---|---|---|---|
| `--keyword` | `-k` | Palabra clave para buscar | Se pide por consola |
| `--max-results` | `-n` | Máximo de noticias a guardar | 10 |
| `--year` | | Año de publicación para filtrar resultados | Sin filtro por año |
| `--all-years` | | Ignora el filtro por año si se combina con `--year` | No hace falta usarlo normalmente |
| `--url` | `-u` | URL base o plantilla de búsqueda | Perfil.com |

## ¿Dónde se guardan los resultados?

Los archivos CSV van a la carpeta `data/`, con un nombre basado en la palabra
clave que buscaste:

```text
data/noticias_donald_trump.csv
data/noticias_elon_musk.csv
```

Cada archivo tiene estas columnas:

```text
autor, fecha_publicacion, titulo, descripcion, url_imagen, url_noticia
```

Las fechas están en formato ISO 8601 (por ejemplo: `2025-03-15T10:30:00-03:00`).
El CSV usa codificación `utf-8-sig` para que Excel abra bien los acentos y
caracteres especiales sin necesidad de configuraciones adicionales.

### Ejemplo de ejecución

```powershell
py src/main.py -k "donald trump" --year 2025
```

```text
Buscando noticias relacionadas con: donald trump
URL de búsqueda: https://www.perfil.com/buscador?q=donald+trump#gsc.tab=0&gsc.q=donald%20trump&gsc.page=1
Cargando resultados del buscador...
Esperando que aparezcan las noticias...
Se encontraron 13 enlaces candidatos para analizar.
[1/13] Extrayendo: https://www.perfil.com/noticias/internacional/...
[2/13] Extrayendo: https://www.perfil.com/noticias/politica/...
...
Proceso finalizado. Archivo generado: data/noticias_donald_trump.csv
```

## Criterio de filtrado

La consigna del ejercicio pide que las noticias contengan la palabra clave
en el **título** o la **descripción**. Por eso el script usa esos dos campos
para decidir si una noticia coincide con la búsqueda. La URL se extrae y se
guarda en el CSV, pero no se usa como criterio de coincidencia.

- **Normaliza el texto**: ignora mayúsculas, minúsculas y acentos.
  - `"Economía"` coincide con `"economia"`
  - `"dólar"` coincide con `"dolar"`

- **Para búsquedas con varias palabras** (como "donald trump"):
  - Primero busca la frase completa.
  - Si no la encuentra, acepta que aparezca cualquiera de las palabras en el
    título o en la descripción.

Esta decisión interpreta el requisito como una coincidencia en el título **o**
en la descripción, sin exigir que la palabra clave aparezca en ambos campos.

- **Filtro por año**: por defecto no se filtra por año. Si querés limitar los
  resultados a un año específico, podés usar `--year`.

## Decisiones de implementación

- **Portal elegido**: Perfil.com, porque es un portal real de noticias con
  buscador público y artículos con metadatos suficientes para extraer la
  información pedida.
- **Playwright para la búsqueda**: el buscador de Perfil carga resultados con
  JavaScript. Playwright permite obtener esos enlaces de forma confiable.
- **Requests y BeautifulSoup para artículos**: una vez obtenidas las URLs, la
  extracción de cada noticia se hace con `requests` y `BeautifulSoup`, que son
  más livianos que abrir un navegador por cada artículo.
- **JSON-LD y meta tags**: se priorizan datos estructurados porque suelen ser
  más estables que los selectores visuales del sitio.
- **CSV**: se eligió CSV por simplicidad de entrega y porque puede abrirse en
  herramientas comunes como Excel o Google Sheets.

## Scraping responsable

Para evitar sobrecargar el sitio y reducir la posibilidad de bloqueo, el
script incluye:

- Consulta `robots.txt` antes de acceder al buscador y a cada noticia.
- User-Agent de un navegador real.
- Timeouts en todas las peticiones HTTP.
- Pausas entre requests para no saturar el servidor.
- Playwright solo se usa para el buscador dinámico; la extracción de cada
  artículo usa `requests` que es más liviano.

## Cómo está organizado el código

El proyecto está dividido en módulos, cada uno con una responsabilidad clara:

| Módulo | Qué hace |
|---|---|
| `src/main.py` | Punto de entrada. Lee argumentos, coordina todo el flujo, filtra y guarda |
| `src/scraper.py` | Construye la URL del buscador y usa Playwright para obtener los enlaces de noticias |
| `src/parser.py` | Entra a cada noticia y extrae los datos usando JSON-LD y meta tags |
| `src/storage.py` | Escribe los resultados en un archivo CSV |
| `src/utils.py` | Funciones auxiliares: requests, URLs absolutas, robots.txt, pausas |

## Limitaciones conocidas

- El scraper está adaptado al buscador de Perfil.com (Google Custom Search).
- Cambiar la URL con `--url` permite buscar en otra dirección, pero no convierte
  al scraper en genérico para cualquier portal. Cada sitio tiene selectores y
  estructura HTML distintos.
- Si Perfil cambia sus selectores, metadatos o el comportamiento del buscador,
  puede requerir ajustes.
- La extracción es secuencial, así que con muchos resultados puede tardar
  algunos minutos.

