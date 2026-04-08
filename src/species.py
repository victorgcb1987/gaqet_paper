from pathlib import Path

import json
import shutil
import subprocess

class Species:
    

    def __init__ (self, species_name, taxon_id, accesion, assembly_level, outdir):
        self.taxon_id = taxon_id
        self.refseq_accesion = accesion
        self.user_submitted_accession = "NA"
        self.name = species_name
        self.assembly_level = assembly_level
        self.outdir = Path(outdir)
        self.filepath = self.outdir / self.name
        self.filepath = None
        self.RefSeq_annot = None
        self.RefSeq_assembly = None
        self.UserSubmitted_annot = None
        self.UserSubmitted_assembly = None
        self.log = "\nLOG START\n"


    def get_user_submitted_accession(self):
        cmd = "datasets summary genome accession {}".format(self.refseq_accesion)
        self.log += f"Obtaining user submitted accession for {self.name}, RefSeq accession {self.refseq_accesion}\n"
        try:
            results = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if results.returncode != 0:
                self.log += f"Command failed: {results.stderr}\n"
                return
            metadata = json.loads(results.stdout.decode())
            if "reports" in metadata and isinstance(metadata["reports"], list) and metadata["reports"]:
                self.user_submitted_accession = metadata["reports"][0].get("paired_accession", "NA")
            else:
                self.log += f"No user submitted accession found for {self.refseq_accesion}.\n"
        except json.JSONDecodeError as e:
            self.log += f"JSON load error: {e}\n"
        except Exception as e:
            self.log += f"Unexpected error: {e}\n"


    def print_metadata(self):
        msg = "Species: {}\n".format(self.name)
        msg += "\tAssembly level: {}\n".format(self.assembly_level)
        msg += "\tRefSeq accesion: {}\n".format(self.refseq_accesion)
        msg += "\t\tRefSeq annot filepath: {}\n".format(self.RefSeq_annot)
        msg += "\t\tRefSeq assembly filepath: {}\n".format(self.RefSeq_assembly)
        msg += "\tUser Submitted accession: {}\n".format(self.user_submitted_accession)
        msg += "\t\tUser Submitted annot filepath: {}\n".format(self.UserSubmitted_annot)
        msg += "\t\tUser Submitted assembly filepath: {}\n".format(self.UserSubmitted_assembly)
        print(msg)


    def print_log(self):
        print(self.log)

    def get_taxonomic_data(self):    
        cmd = "datasets summary taxonomy taxon \"{}\"".format(self.name).replace("_", " ")
        metadata = subprocess.run(cmd, shell=True, capture_output=True)
        
        if metadata.returncode == 0:
            metadata = json.loads(metadata.stdout)
            tax_metadata = metadata["reports"][0]["taxonomy"]["classification"]
            species = tax_metadata["species"]["name"]
            taxid = tax_metadata["species"]["id"]
            genus = tax_metadata["genus"]["name"]
            family = tax_metadata["family"]["name"]
            tax_class = tax_metadata["class"]["name"]
            self.taxon_id = taxid

    def download_accession(self, type=""):
        self.filepath = self.outdir / self.name
        if type == "RefSeq":
            cmd = f"datasets download genome accession {self.refseq_accesion} --include genome,gff3 --filename {self.filepath}.zip"
        if type == "UserSubmitted":
            cmd = f"datasets download genome accession {self.user_submitted_accession} --include genome,gff3 --filename {self.filepath}.zip"
        results = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if results.returncode != 0:
            self.log += f"Command failed: {results.stderr}\n"
            return
        cmd = f"unzip -o -d {self.filepath} {self.filepath}.zip"
        results = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if results.returncode != 0:
                self.log += f"Command failed: {results.stderr}\n"
                return
        else:
            try:
                ncbi_dir = self.filepath / "ncbi_dataset"
                annot = list(ncbi_dir.rglob("*.gff"))[0]
            except:
                if type == "RefSeq":
                    self.log += f"gff for {self.name}, RefSeq accession {self.refseq_accesion} not found"
                if type == "UserSubmitted":
                    self.log += f"gff for {self.name}, UserSubmitted accession {self.user_submitted_accesion} not found"
                return
 
            if type == "RefSeq":
                renamed_gff = f"{self.name}_RefSeq_{self.refseq_accesion}.gff"
            if type == "UserSubmitted":
                renamed_gff = f"{self.name}_UserSubmitted_{self.user_submitted_accession}.gff"
            annot.replace(self.filepath / renamed_gff)
            try:
                assembly = list(ncbi_dir.rglob("*.fna"))[0]
            except:
                self.log += f"Assembly fasta for {self.name} not found"
            assembly_fpath = self.filepath / assembly.name
            if not assembly_fpath.is_file():
                shutil.copy(assembly, assembly_fpath)
            self.assembly = assembly_fpath
            shutil.rmtree(self.filepath / "ncbi_dataset")
            Path(f"{self.filepath}.zip").unlink(missing_ok=False)
        if type == "RefSeq":
            self.RefSeq_annot = self.filepath / renamed_gff
            self.RefSeq_assembly = assembly_fpath
        elif type == "UserSubmitted":
            self.UserSubmitted_annot = self.filepath / renamed_gff
            self.UserSubmitted_assembly = assembly_fpath