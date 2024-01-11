import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import subprocess

def create_kg():
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

def drop_database():
    """Dropping database """
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    NEO4J_BIN = os.environ.get("NEO4J_BIN")
    NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
    NEO4J_HOME = os.environ.get("NEO4J_HOME")
    
    # Cypher-shell requires database names to be quoted by tick marks if there are non-alphanumeric characters in the name.
    database_name = f"\`{NEO4J_DATABASE}\`"
    cypher_shell = f"{NEO4J_BIN}/cypher-shell"
    #cypher_command = f"{NEO4J_BIN}/cypher-shell -d system -u {NEO4J_USERNAME} -p {NEO4J_PASSWORD} DROP DATABASE {NEO4J_DATABASE_QUOTED} IF EXISTS;"
    subprocess.run([cypher_shell, "-d", "system", "-u", NEO4J_USERNAME, "-p", NEO4J_PASSWORD, 
                    "DROP DATABASE", database_name, "IF EXISTS;"])
    #echo ERROR: Running cypher-shell. Make sure Neo4j Graph DBMS is running, and username and password are correct. | tee -a "$LOGFILE"
    database_dir = os.path.join(NEO4J_HOME, "data", "databases", NEO4J_DATABASE)
    shutil.rmtree(database_dir, ignore_errors=True)


def run_bulk_import():
    #(cd "$NEO4J_IMPORT";
    #"$NEO4J_BIN"/neo4j-admin database import full $NEO4J_DATABASE --overwrite-destination --skip-bad-relationships --skip-duplicate-nodes --multiline-fields --array-delimiter="|" @args.txt)
    NEO4J_HOME = os.environ.get("NEO4J_HOME")
    NEO4J_IMPORT = os.path.join(NEO4J_HOME, "import")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    NEO4J_BIN = os.environ.get("NEO4J_BIN")
    neo4j_admin = os.path.join(NEO4J_BIN, "neo4j-admin")
    subprocess.run([neo4j_admin, "database" "import", "full", NEO4J_DATABASE, "--overwrite-destination", "-skip-bad-relationships", 
                    "--skip-duplicate-nodes", "--multiline-fields", '--array-delimiter="|"', "@args.txt"])
    #echo ERROR: Neo4j bulk data import failed. Make sure Neo4j Graph DBMS is running, and username and password are correct. | tee -a "$LOGFILE"


def create_database():
    #echo Creating online database: "$NEO4J_DATABASE" ...
    #"$NEO4J_BIN"/cypher-shell -d system -u $NEO4J_USERNAME -p $NEO4J_PASSWORD "CREATE DATABASE $NEO4J_DATABASE_QUOTED;"
    #echo ERROR: Creating database failed. Make sure Neo4j Graph DBMS is running, and username and password are correct. | tee -a "$LOGFILE"

    NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE")
    # Cypher-shell requires database names to be quoted by tick marks if there are non-alphanumeric characters in the name.
    database_name = f"\`{NEO4J_DATABASE}\`"
    cypher_shell = f"{NEO4J_BIN}/cypher-shell"
    subprocess.run([cypher_shell, "-d", "system", "-u", NEO4J_USERNAME, "-p", NEO4J_PASSWORD, "CREATE DATABASE", database_name, ";"])

