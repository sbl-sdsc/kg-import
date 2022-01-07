#!/bin/bash
#
# This script performs a bulk import of node and relationship csv files into a Neo4j Knowledge Graph.
# Data import is configured by node and relationship metadata that define data types and indices for rapid searching.
#

# exit when any command fails (see https://intoli.com/blog/exit-on-errors-in-bash-scripts/)
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\" command failed with exit code $?."' EXIT

# The following environment variables need to be set to run this script (see ../run.sh script).

echo 
echo Starting Neo4j Bulk Data Import ...
echo
echo Environment variables used by this script:
echo    NEO4J_HOME           : $NEO4J_HOME
echo    NEO4J_BIN            : $NEO4J_BIN
echo    NEO4J_USERNAME       : $NEO4J_USERNAME
echo    NEO4J_PASSWORD       : $NEO4J_PASSWORD
echo    NEO4J_DATABASE       : $NEO4J_DATABASE
echo    NODE_METADATA        : $NODE_METADATA
echo    RELATIONSHIP_METADATA: $RELATIONSHIP_METADATA
echo    NODE_DATA            : $NODE_DATA
echo    RELATIONSHIP_DATA    : $RELATIONSHIP_DATA
echo    KGIMPORT_GITREPO     : $KGIMPORT_GITREPO

# Paths to Neo4j subdirectories
NEO4J_IMPORT="$NEO4J_HOME"/import

# Path to logging directory
LOGDIR="$NEO4J_IMPORT"/logs/`date +%Y-%m-%d`
mkdir -p "$LOGDIR"
echo Logging to: $LOGDIR

echo
echo Cleaning the import directory: $NEO4J_IMPORT ...
# Clean any existing data files
rm -f "$NEO4J_IMPORT"/*_n.csv 
rm -f "$NEO4J_IMPORT"/*_r.csv 
rm -f "$NEO4J_IMPORT"/args.txt
rm -f "$NEO4J_IMPORT"/import.report 

echo
echo Copying data files into import directory: $NEO4J_IMPORT ...
# For the bulk import the header line is removed, since separate header files are used. 
# The tags _n and _r are appended to the file names to distinguish node and relationship files, respectively.
(cd $NODE_DATA;
for f in *.csv
do 
  tail -n +2 $f > "$NEO4J_IMPORT"/$(basename $f .csv)_n.csv
done)

(cd $RELATIONSHIP_DATA;
for f in *.csv
do 
  tail -n +2 $f > "$NEO4J_IMPORT"/$(basename $f .csv)_r.csv
done)

echo
echo Preparing data files for bulk import into $NEO4J_DATABASE using $KGIMPORT_GITREPO/notebooks/PrepareNeo4jBulkImport.ipynb
echo
# Active the conda environment to execute the data preparation script.
# The eval command is used to enable conda in bash 
# (see: https://github.com/conda/conda/issues/7980)
eval "$(conda shell.bash hook)"
conda activate kg-import
(cd $KGIMPORT_GITREPO/notebooks;
papermill PrepareNeo4jBulkImport.ipynb "$LOGDIR"/PrepareNeo4jBulkImport.ipynb)
conda deactivate

exit_code=0
if [ -s "$NEO4J_IMPORT"/mismatches_n.csv ]; then
    echo
    echo The following node data files do not match the metadata specification:
    cat "$NEO4J_IMPORT"/mismatches_n.csv
    exit_code=1
fi

if [ -s "$NEO4J_IMPORT"/mismatches_r.csv ]; then
    echo
    echo The following relationship data files do not match the metadata specification:
    cat "$NEO4J_IMPORT"/mismatches_r.csv
    exit_code=1
fi

if [ $exit_code -eq 1 ]; then
    echo 
    echo Terminating data import!
    exit $exit_code
fi

echo
echo Dropping database: $NEO4J_DATABASE ...
echo
"$NEO4J_BIN"/cypher-shell -d system -u $NEO4J_USERNAME -p $NEO4J_PASSWORD "DROP DATABASE $NEO4J_DATABASE IF EXISTS;"
rm -rf "$NEO4J_HOME"/data/databases/$NEO4J_DATABASE

echo
echo Importing data ...
echo
# *** Run bulk data import command ***
(cd "$NEO4J_IMPORT";
"$NEO4J_BIN"/neo4j-admin import --database=$NEO4J_DATABASE --skip-bad-relationships --skip-duplicate-nodes --multiline-fields --array-delimiter="|" @args.txt)

if [ -s "$NEO4J_IMPORT"/import.report ]; then
    echo
    echo Error message from import.report:
    cat "$NEO4J_IMPORT"/import.report
    echo Terminating data import
#    exit_code=1
#    exit $exit_code
fi

echo
echo Creating database: $NEO4J_DATABASE ...
echo
"$NEO4J_BIN"/cypher-shell -d system -u $NEO4J_USERNAME -p $NEO4J_PASSWORD "CREATE DATABASE $NEO4J_DATABASE;"

echo
echo Done: $NEO4J_DATABASE is ready for use
echo
