import os
import sys
import time
import shutil
import pathlib
from datetime import datetime
from dotenv import load_dotenv

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
    os.makedirs(LOGDIR, exist_ok=False)
    LOGFILE = os.path.join(LOGDIR, f"import.log.{timestamp}")

    # Clean import directory

    for filename in os.listdir(NEO4J_IMPORT):
        if filename.endswith(".csv"):
            os.remove(os.path.join(NEO4J_IMPORT, filename))

    # args.txt contains arguments for the neo4j_admin tool
    os.remove(os.path.join(NEO4J_IMPORT, "args.txt"))

    # Copy data and metadata files into the import directory
    # The header line is removed since the column names and types are provided in a separate file for bulk download.

    for input_file in os.listdir(NEO4J_DATA_NODES):
        output_file = os.path.join(NEO4J_IMPORT, f"{pathlib.Path(input_file).stem}_n.csv")
        copy_without_header(input_file, output_file)


    for input_file in os.listdir(NEO4J_DATA_RELATIONSHIPS):
        output_file = os.path.join(NEO4J_IMPORT, f"{pathlib.Path(input_file).stem}_r.csv")
        copy_without_header(input_file, output_file)

              
def copy_without_header(input_file, output_file):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        next(f_in)  # Skip the first line
        shutil.copyfileobj(f_in, f_out)




