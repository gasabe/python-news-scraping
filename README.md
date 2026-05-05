# python-news-scraping

Un script de Python que busca noticias en un portal de noticias según una
palabra clave, extrae la información relevante de cada artículo y guarda
los resultados en un archivo CSV.

Fue desarrollado como ejercicio de web scraping y cumple con los requisitos
de extracción de datos, filtrado por palabra clave, manejo de robots.txt
y uso de Playwright para el buscador dinámico.

## ¿Qué hace?

1. Busca noticias en Perfil.com usando la palabra clave que le indiques.
2. Entra a cada artículo encontrado y extrae el autor, fecha, título, descripción, imagen y URL.
3. Filtra las noticias para quedarte solo con las que mencionan la keyword en el título o descripción.
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
py src/main.py -k "elon musk" --all-years
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
py src/main.py -k "donald trump" -n 3 --year 2025 --all-years
```

## Argumentos disponibles

| Argumento | Corto | Descripción | Por defecto |
|---|---|---|---|
| `--keyword` | `-k` | Palabra clave para buscar | Se pide por consola |
| `--max-results` | `-n` | Máximo de noticias a guardar | 10 |
| `--year` | | Año de publicación | Año actual |
| `--all-years` | | Traer noticias de cualquier año | Desactivado |
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
Se encontraron 13 enlaces candidatos para analizar.
[1/13] Extrayendo: https://www.perfil.com/noticias/internacional/...
[2/13] Extrayendo: https://www.perfil.com/noticias/politica/...
...
Proceso finalizado. Archivo generado: data/noticias_donald_trump.csv
```

## ¿Cómo funciona el filtro de palabras clave?

La consigna del ejercicio pide que las noticias contengan la palabra clave
en el **título** o la **descripción**. El script aplica el filtro de esta
forma:

- **Normaliza el texto**: ignora mayúsculas, minúsculas y acentos.
  - `"Economía"` coincide con `"economia"`
  - `"dólar"` coincide con `"dolar"`

- **Para búsquedas con varias palabras** (como "donald trump"):
  - Primero busca la frase completa.
  - Si no la encuentra, acepta coincidencias donde aparezcan todas las
    palabras por separado (aunque no estén juntas).
  - Como apoyo, también busca en la URL de la noticia, porque a veces el
    tema aparece en la dirección aunque no en el título.

- **Filtro por año**: por defecto se guardan solo noticias del año actual
  para evitar resultados viejos. Se puede cambiar con `--year` o desactivar
  con `--all-years`.

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

## Ideas para mejorar

- Hacer configurable la pausa entre peticiones.
- Agregar reintentos automáticos ante errores de red.
- Tests automatizados.
- Empaquetar en Docker para facilitar la ejecución.
- Soporte para otros portales de noticias.
