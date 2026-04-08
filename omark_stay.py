import os

from csv import DictReader
from pathlib import Path
from sys import argv

from src.species import Species


FILEPATHS = {"test": Path(os.path.dirname(os.path.realpath(__file__))).parent / "docs" / "test.tsv",
             "production": Path(os.path.dirname(os.path.realpath(__file__))).parent / "docs" / "metazoa_viridiplantae_fungi.tsv"}


def main():
    input = Path(argv[1]).absolute()
    out_dir = Path(argv[2])
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
    #os.chdir(out_dir)
    cwd = Path(os.getcwd())
    for record in DictReader(open(input), delimiter=","):
        species = Species(record["Organism Name"].replace(" ", "_"), 
                          record["Organism Taxonomic ID"], record["Assembly Accession"], 
                          record["Assembly Level"], out_dir)
        species.get_taxonomic_data()
        species.get_user_submitted_accession()
        species.print_metadata()
        species.download_accession(type="RefSeq")
        species.print_metadata()
        species.print_log()

        #species_dir = out_dir / species



if __name__ == "__main__":
    main()