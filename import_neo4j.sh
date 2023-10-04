#!/bin/bash
# 
# This script runs the Neo4j bulk data import.
#
# Place a copy of this script outside this Git Repository and set the <variables> below.
#

# Absolute path to Neo4j home directory
#    Add quotes if the path contains spaces, e.g.,
#    export NEO4J_HOME="/Users/User/Library/Application Support/Neo4j Desktop/Application/relate-data/dbmss/dbms-0a85af40-86b9-4245-8d96-f51dba4acdc0"
export NEO4J_HOME=<path_to_neo4j_home>

# Absolute path to Neo4j bin directory
#    On MacOS: NEO4J_BIN="$NEO4J_HOME"/bin
export NEO4J_BIN=<path_to_neo4j_bin_directory>

export NEO4J_USERNAME=<neo4j_username>
export NEO4J_PASSWORD=<neo4j_password>
export NEO4J_DATABASE=<neo4j_database_name>

# Uncomment the export statement below to set an optional Neo4j Graph Stylesheet (GraSS)
#   A GraSS file can be exported from the Neo4j browser by running the :style command and then clicking the download icon.
#   Example GraSS from this repo:
#   export NEO4J_STYLESHEET_URL=https://raw.githubusercontent.com/sbl-sdsc/kg-import/main/styles/style.grass

#export NEO4J_STYLESHEET_URL=<url_of_neo4j_grass_file>

# Absolute paths to node and relationship metadata file directories
export NEO4J_METADATA=<path_to_metadata_directory>

# Absolute paths to node and relationship data file directories
export NEO4J_DATA=<path_to_data_directory>

# Absolute path to kg-import Git repository
export KGIMPORT_GITREPO=<path_to_this_git_repository>

# Run the Neo4j bulk data import
$KGIMPORT_GITREPO/scripts/neo4j_bulk_import.sh
