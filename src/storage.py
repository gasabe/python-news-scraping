import csv
from pathlib import Path


def save_to_csv(news: list[dict], output_path: str) -> None:
    """
    Guarda la lista de noticias en un archivo CSV.

    Args:
        news: lista de diccionarios con datos de noticias.
        output_path: ruta donde se va a generar el archivo CSV.
    """

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "autor",
        "fecha_publicacion",
        "titulo",
        "descripcion",
        "url_imagen",
        "url_noticia",
    ]

    # utf-8-sig ayuda a que Excel abra bien los caracteres especiales.
    with open(output_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(news)
