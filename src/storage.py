import csv
from pathlib import Path


def save_to_csv(news: list[dict], output_path: str) -> None:
    """
    Guarda las noticias encontradas en un CSV.
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

    # utf-8-sig hace que Excel lea bien los acentos.
    with open(output_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(news)
