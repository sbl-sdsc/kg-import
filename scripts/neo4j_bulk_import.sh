#!/bin/bash
#
# This script performs a bulk import of node and relationship csv files into a Neo4j Knowledge Graph.
# Data import is configured by node and relationship metadata that define data types and indices for rapid searching.
#

# exit when any command fails (see https://intoli.com/blog/exit-on-errors-in-bash-scripts/)
set -e
# keep track of the last executed command
#trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
#trap 'echo "\"${last_command}\" command failed with exit code $?."' EXIT

# The following environment variables need to be set to run this script (see ../run.sh script).

echo 
echo Starting Neo4j Bulk Data Import ...
echo

# Paths to Neo4j subdirectories
NEO4J_IMPORT="$NEO4J_HOME"/import
if [[ ! -d "$NEO4J_IMPORT" ]]; then
  echo ERROR: Import directory "$NEO4J_IMPORT" does not exist.
  exit 1
fi

# Path to logging directory
LOGDIR="$NEO4J_IMPORT"/logs/`date +%Y-%m-%d-%H%M%S`
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR"/log
touch "$LOGFILE"
echo Logging to: "$LOGDIR"

echo Environment variables used by this script: | tee -a "$LOGFILE"
echo    NEO4J_HOME           : $NEO4J_HOME | tee -a "$LOGFILE"
echo    NEO4J_BIN            : $NEO4J_BIN | tee -a "$LOGFILE"
echo    NEO4J_USERNAME       : $NEO4J_USERNAME | tee -a "$LOGFILE"
echo    NEO4J_PASSWORD       : $NEO4J_PASSWORD | tee -a "$LOGFILE"
echo    NEO4J_DATABASE       : $NEO4J_DATABASE | tee -a "$LOGFILE"
echo    NODE_METADATA        : $NODE_METADATA | tee -a "$LOGFILE"
echo    RELATIONSHIP_METADATA: $RELATIONSHIP_METADATA | tee -a "$LOGFILE"
echo    NODE_DATA            : $NODE_DATA | tee -a "$LOGFILE"
echo    RELATIONSHIP_DATA    : $RELATIONSHIP_DATA | tee -a "$LOGFILE"
echo    KGIMPORT_GITREPO     : $KGIMPORT_GITREPO | tee -a "$LOGFILE"

if [[ ! -d "$NODE_METADATA" ]]; then
  echo ERROR: NODE_DATA directory "$NODE_METADATA" does not exist. | tee -a "$LOGFILE"
  exit 1
fi

if [[ ! -d "$RELATIONSHIP_METADATA" ]]; then
  echo ERROR: RELATIONSHIP_DATA directory "$RELATIONSHIP_METADATA" does not exist. | tee -a "$LOGFILE"
  exit 1
fi

if [[ ! -d "$NODE_DATA" ]]; then
  echo ERROR: NODE_DATA directory "$NODE_DATA" does not exist. | tee -a "$LOGFILE" 
  exit 1
fi

if [[ ! -d "$RELATIONSHIP_DATA" ]]; then
  echo ERROR: RELATIONSHIP_DATA directory "$RELATIONSHIP_DATA" does not exist. | tee -a "$LOGFILE"
  exit 1
fi

echo
echo Cleaning the import directory: $NEO4J_IMPORT ...
# Clean any existing data, argument, and report files
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
  echo Processing node file: $f >> "$LOGFILE"
done)

(cd $RELATIONSHIP_DATA;
for f in *.csv
do 
  tail -n +2 $f > "$NEO4J_IMPORT"/$(basename $f .csv)_r.csv
  echo Processing relationship file: $f >> "$LOGFILE"
done)

echo
echo Preparing data files for bulk import into $NEO4J_DATABASE using $KGIMPORT_GITREPO/notebooks/PrepareNeo4jBulkImport.ipynb
echo
# Active the conda environment to execute the data preparation script.
# The eval command is used to enable conda in bash 
# (see: https://github.com/conda/conda/issues/7980)
eval "$(conda shell.bash hook)"
conda activate kg-import
if [[ "${?}" -ne 0 ]]; then
  echo ERROR: Cannot activate conda environment kg-import. | tee -a "$LOGFILE"
  exit 1
fi
(cd $KGIMPORT_GITREPO/notebooks;
papermill PrepareNeo4jBulkImport.ipynb "$LOGDIR"/PrepareNeo4jBulkImport.ipynb)
if [[ "${?}" -ne 0 ]]; then
  echo ERROR: Neo4j Bulk Import preparation failed. Check your data and metadata files. | tee -a "$LOGFILE"
  echo ERROR: See "$LOGDIR"/PrepareNeo4jBulkImport.ipynb for details. | tee -a "$LOGFILE"
  exit 1
fi
conda deactivate

if [ -s "$NEO4J_IMPORT"/mismatches_n.csv ]; then
    echo
    echo The following node data files do not match the metadata specification: | tee -a "$LOGFILE"
    cat "$NEO4J_IMPORT"/mismatches_n.csv | tee -a "$LOGFILE"
    exit 1
fi

if [ -s "$NEO4J_IMPORT"/mismatches_r.csv ]; then
    echo
    echo The following relationship data files do not match the metadata specification: | tee -a "$LOGFILE"
    cat "$NEO4J_IMPORT"/mismatches_r.csv | tee -a "$LOGFILE"
    exit 1
fi

echo
echo Dropping database: $NEO4J_DATABASE ...
echo
# Cypher-shell requires database names to be quoted by tick marks if there are non-alphanumeric characters in the name.
NEO4J_DATABASE_QUOTED=\`$NEO4J_DATABASE\`
"$NEO4J_BIN"/cypher-shell -d system -u $NEO4J_USERNAME -p $NEO4J_PASSWORD "DROP DATABASE $NEO4J_DATABASE_QUOTED IF EXISTS;"
if [[ "${?}" -ne 0 ]]; then
  echo ERROR: Running cypher-shell. Make sure Neo4j Graph DBMS is running, and username and password are correct. | tee -a "$LOGFILE"
  exit 1
fi
rm -rf "$NEO4J_HOME"/data/databases/$NEO4J_DATABASE

echo
echo Importing data ...
echo
# *** Run bulk data import command ***
(cd "$NEO4J_IMPORT";
"$NEO4J_BIN"/neo4j-admin import --database=$NEO4J_DATABASE --force --skip-bad-relationships --skip-duplicate-nodes --multiline-fields --array-delimiter="|" @args.txt)
if [[ "${?}" -ne 0 ]]; then
  echo ERROR: Neo4j bulk data import failed. Make sure Neo4j Graph DBMS is running, and username and password are correct. | tee -a "$LOGFILE"
  exit 1
fi

if [ -s "$NEO4J_IMPORT"/import.report ]; then
     echo
     echo WARNING: Error messages from data import: | tee -a "$LOGFILE"
     cat "$NEO4J_IMPORT"/import.report | tee -a "$LOGFILE"
fi

echo
echo Creating database: $NEO4J_DATABASE ...
echo
"$NEO4J_BIN"/cypher-shell -d system -u $NEO4J_USERNAME -p $NEO4J_PASSWORD "CREATE DATABASE $NEO4J_DATABASE_QUOTED;"
if [[ "${?}" -ne 0 ]]; then
  echo ERROR: Creating database failed. Make sure Neo4j Graph DBMS is running, and username and password are correct. | tee -a "$LOGFILE"
  exit 1
fi

echo
echo Done: Datbase $NEO4J_DATABASE is ready for use.
echo
