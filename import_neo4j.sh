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
export NEO4J_BIN=<path_to_neo4j_bin>

export NEO4J_USERNAME=<neo4j_username>
export NEO4J_PASSWORD=<neo4j_password>
export NEO4J_DATABASE=<neo4j_database_name>

# Absolute paths to node and relationship metadata file directories
export NODE_METADATA=<path_to_node_metadata_files>
export RELATIONSHIP_METADATA=<path_to_relationship_metadata_files>

# Absolute paths to node and relationship data file directories
export NODE_DATA=<path_to_node_csv_files>
export RELATIONSHIP_DATA=<path_to_relationship_csv_files>

# Absolute path to kg-import Git repository
export KGIMPORT_GITREPO=<path_to_this_git_repository>

# Run the Neo4j bulk data import
$KGIMPORT_GITREPO/scripts/neo4j_bulk_import.sh