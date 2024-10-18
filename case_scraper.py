import argparse
import json
import os
import re
import tarfile

import requests
import xmltodict
from bs4 import BeautifulSoup
from tqdm import tqdm


class DataDownloader:
    def __init__(self, base_url, output_dir):
        self.base_url = base_url
        self.output_dir = os.path.abspath(output_dir)  # Convertir en chemin absolu
        os.makedirs(
            self.output_dir, exist_ok=True
        )  # Créer le dossier s'il n'existe pas
        self.links = []  # Attribut pour stocker les liens

    def scrape_links(self):
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Récupérer les liens des fichiers .tar.gz
        for link in soup.find_all("a"):
            href = link.get("href")
            # Exclure le fichier spécifique
            if (
                href.endswith(".tar.gz")
                and href != "Freemium_cass_global_20231119-100000.tar.gz"
            ):
                self.links.append(href)  # Ajouter les liens à l'attribut

    def download_and_extract(self):
        # Ajouter une barre de progression pour le téléchargement de chaque fichier
        with tqdm(
            total=len(self.links), desc="Téléchargement et extraction", unit="fichier"
        ) as bar:
            for link in self.links:
                file_url = f"{self.base_url}/{link}"
                file_name = os.path.join(self.output_dir, link.split("/")[-1])

                # Télécharger le fichier .tar.gz avec une barre de progression
                with requests.get(file_url, stream=True) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get("content-length", 0))
                    with open(file_name, "wb") as f, tqdm(
                        desc=f"Téléchargement: {file_name}",
                        total=total_size,
                        unit="iB",
                        unit_scale=True,
                        unit_divisor=1024,
                        leave=False,  # Ne pas laisser la barre de téléchargement à la fin
                    ) as bar_download:
                        for data in r.iter_content(chunk_size=1024):
                            f.write(data)
                            bar_download.update(len(data))

                # Extraire le fichier .tar.gz
                if tarfile.is_tarfile(file_name):
                    with tarfile.open(file_name) as tar:
                        tar.extractall(path=self.output_dir)

                # Supprimer le fichier .tar.gz après extraction
                os.remove(file_name)

                # Mettre à jour la barre de progression globale
                bar.update(1)

    def convert_xml_to_json(self):
        # Rechercher de manière récursive tous les fichiers XML
        xml_files = []
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith(".xml"):
                    xml_files.append(os.path.join(root, file))

        # Conversion des fichiers XML en JSON avec une barre de progression
        with tqdm(
            total=len(xml_files), desc="Conversion XML vers JSON", unit="fichier"
        ) as bar:
            for xml_file in xml_files:
                with open(xml_file, "r", encoding="utf-8", errors="ignore") as f:
                    xml_content = f.read()

                # Remplacer <br clear="none"/> par <br>
                modified_xml_content = re.sub(
                    r'<br\s+clear="none"\s*/?>', "<br/>", xml_content
                )

                # Supprimer les balises <p> et </p>
                modified_xml_content = re.sub(r"</?p\s*.*?>", "", modified_xml_content)

                # Conversion du XML en JSON
                json_data = xmltodict.parse(modified_xml_content)

                # Enregistrer le fichier JSON
                json_file = xml_file.replace(".xml", ".json")
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)

                bar.update(1)


def main():
    parser = argparse.ArgumentParser(
        description="Télécharger et convertir des fichiers XML à partir d'une page web."
    )
    parser.add_argument(
        "url", type=str, help="URL de la page contenant les fichiers .tar.gz"
    )
    parser.add_argument(
        "output_dir", type=str, help="Dossier de sortie relatif au script"
    )

    args = parser.parse_args()

    # Exécuter le téléchargement et la conversion
    downloader = DataDownloader(args.url, args.output_dir)
    downloader.scrape_links()

    downloader.download_and_extract()  # Pas besoin de passer les liens

    downloader.convert_xml_to_json()


if __name__ == "__main__":
    main()
