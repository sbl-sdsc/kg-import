import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import papermill as pm
import subprocess
import neo4j_utils


def import_from_csv():
    setup()
    pm.execute_notebook("PrepareNeo4jBulkImport.ipynb", "PrepareNeo4jBulkImport_out.ipynb");
    run_bulk_import()
    neo4j_utils.start()
    add_indices()


def setup():
    # Check environment variables and directory structure
    #load_dotenv(".env.colab")
    
    NEO4J_HOME = os.environ.get("NEO4J_HOME")
    if not NEO4J_HOME:
        sys.exit("NEO4J_HOME environment variable has not been set")
    if not os.path.exists(NEO4J_HOME):
        sys.exit(f"Neo4j HOME directory not found: {NEO4J_HOME}")
    
    NEO4J_IMPORT = os.path.join(NEO4J_HOME, "import")
    if not os.path.exists(NEO4J_HOME):
        sys.exit(f"Neo4j import directory not found: {NEO4J_HOME}")
    
    NEO4J_METADATA = os.environ.get("NEO4J_METADATA")
    if not os.path.exists(NEO4J_METADATA):
        sys.exit(f"Metadata directory not found: {NEO4J_METADATA}")
    
    NEO4J_METADATA_NODES = os.path.join(NEO4J_METADATA, "nodes")
    if not os.path.exists(NEO4J_METADATA_NODES):
        sys.exit(f"Metadata directory not found: {NEO4J_METADATA_NODES}")
    
    NEO4J_METADATA_RELATIONSHIPS = os.path.join(NEO4J_METADATA, "relationships")
    if not os.path.exists(NEO4J_METADATA_RELATIONSHIPS):
        sys.exit(f"Metadata directory not found: {NEO4J_METADATA_RELATIONSHIPS}")
    
    NEO4J_DATA = os.environ.get("NEO4J_DATA")
    if not os.path.exists(NEO4J_DATA):
        sys.exit(f"Data directory not found: {NEO4J_DATA}")
    
    NEO4J_DATA_NODES = os.path.join(NEO4J_DATA, "nodes")
    if not os.path.exists(NEO4J_DATA_NODES):
        sys.exit(f"Data directory not found: {NEO4J_DATA_NODES}")
    
    NEO4J_DATA_RELATIONSHIPS = os.path.join(NEO4J_DATA, "relationships")
    if not os.path.exists(NEO4J_DATA_RELATIONSHIPS):
        sys.exit(f"Data directory not found: {NEO4J_DATA_RELATIONSHIPS}")
    
    # create a timestamped logfile
    date_time = datetime.fromtimestamp(time.time())
    timestamp = date_time.strftime("%Y-%m-%d-%H%M%S")
    LOGDIR = os.path.join(NEO4J_HOME, "logs")
    os.makedirs(LOGDIR, exist_ok=True)
    LOGFILE = os.path.join(LOGDIR, f"import.log.{timestamp}")

    # Clean import directory

    for file in Path(NEO4J_IMPORT).glob('*.csv'):
        os.remove(file)

    # args.txt contains arguments for the neo4j_admin tool
    if os.path.exists(os.path.join(NEO4J_IMPORT, "args.txt")):
        os.remove(os.path.join(NEO4J_IMPORT, "args.txt"))

    # TODO
    # remove indices.cypher

    # Copy data and metadata files into the import directory
    # The header line is removed since the column names and types are provided in a separate file for bulk download.

    for input_file in Path(NEO4J_DATA_NODES).glob('*.csv'):
        output_file = os.path.join(NEO4J_IMPORT, f"{input_file.stem}_n.csv")
        copy_without_header(input_file, output_file)

    for input_file in Path(NEO4J_DATA_RELATIONSHIPS).glob('*.csv'):
        output_file = os.path.join(NEO4J_IMPORT, f"{input_file.stem}_r.csv")
        copy_without_header(input_file, output_file)


def copy_without_header(input_file, output_file):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        next(f_in)  # Skip the first line
        shutil.copyfileobj(f_in, f_out)


def dump_database(verbose=False):
    version = os.getenv("NEO4J_VERSION")
    password = os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    # if install path is not set, install Neo4j into the current directory
    neo4j_install_path = os.getenv("NEO4J_INSTALL_PATH", ".")
    neo4j_home = os.path.join(neo4j_install_path, version)
    neo4j_bin = os.getenv("NEO4J_BIN", os.path.join(neo4j_home, "bin"))
    neo4j_admin = os.path.join(neo4j_bin, "neo4j-admin")

    ret = subprocess.run([neo4j_admin, "database", "dump", NEO4J_DATABASE, "--to-path=" + neo4j_home])
    if verbose:
        print(ret.stdout.decode())


def drop_database(verbose=True):
    NEO4J_HOME = os.environ.get("NEO4J_HOME")
    NEO4J_BIN = os.environ.get("NEO4J_BIN")
    NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    
    # Cypher-shell requires database names to be quoted by tick marks if there are non-alphanumeric characters in the name.
    NEO4J_DATABASE_QUOTED = f"`{NEO4J_DATABASE}`"
    
    command = f"{NEO4J_BIN}/cypher-shell -d system -u {NEO4J_USERNAME} -p {NEO4J_PASSWORD} DROP DATABASE {NEO4J_DATABASE_QUOTED} IF EXISTS;"
    ret = subprocess.run(command, capture_output=True, check=True, shell=True)
    if verbose:
        print(ret.stdout.decode())

    # remove the database file
    # TODO remove the transaction files as well
    database_dir = os.path.join(NEO4J_HOME, "data", "databases", NEO4J_DATABASE)
    shutil.rmtree(database_dir, ignore_errors=True)


def run_bulk_import(verbose=False):
    NEO4J_HOME = os.environ.get("NEO4J_HOME")
    NEO4J_IMPORT = os.path.join(NEO4J_HOME, "import")
    NEO4J_BIN = os.environ.get("NEO4J_BIN")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    
    # Cypher-shell requires database names to be quoted by tick marks if there are non-alphanumeric characters in the name.
    NEO4J_DATABASE_QUOTED = f"`{NEO4J_DATABASE}`"
    
    # run import
    neo4j_admin = os.path.join(NEO4J_BIN, "neo4j-admin")
    command = f"cd {NEO4J_IMPORT}; ls; {neo4j_admin} database import full --overwrite-destination --skip-bad-relationships --skip-duplicate-nodes --multiline-fields --array-delimiter='|' @args.txt {NEO4J_DATABASE_QUOTED}"
    ret = subprocess.run(command, capture_output=True, check=True, shell=True)
    if verbose:
        print(ret.stdout.decode())
    

def create_database(verbose=False):
    NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    NEO4J_BIN = os.environ.get("NEO4J_BIN")
    # Cypher-shell requires database names to be quoted by tick marks if there are non-alphanumeric characters in the name.
    NEO4J_DATABASE_QUOTED = f"`{NEO4J_DATABASE}`"

    # compose the cypher shell command
    cypher_shell = os.path.join(NEO4J_BIN, "cypher-shell")
    command = f"{cypher_shell} -d system -u {NEO4J_USERNAME} -p {NEO4J_PASSWORD} 'CREATE OR REPLACE DATABASE {database_name}';"

    # run command to create the database
    ret = subprocess.run(command, capture_output=True, check=True, shell=True)
    if verbose:
        print(ret.stdout.decode())
        

def add_indices(verbose=False):
    NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
    NEO4J_HOME = os.environ.get("NEO4J_HOME")
    NEO4J_IMPORT = os.path.join(NEO4J_HOME, "import")
    NEO4J_BIN = os.environ.get("NEO4J_BIN")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    
    # Cypher-shell requires database names to be quoted by tick marks if there are non-alphanumeric characters in the name.
    NEO4J_DATABASE_QUOTED = f"`{NEO4J_DATABASE}`"

    # compose the cypher shell command
    cypher_shell = os.path.join(NEO4J_BIN, "cypher-shell")
    cypher_script = os.path.join(NEO4J_IMPORT, "indices.cypher")
    command = f"{cypher_shell} -d {NEO4J_DATABASE} -u {NEO4J_USERNAME} -p {NEO4J_PASSWORD} -f {cypher_script}"

    # run command to add the indices and constraints
    ret = subprocess.run(command, capture_output=True, check=True, shell=True)
    if verbose:
        print(ret.stdout.decode())
