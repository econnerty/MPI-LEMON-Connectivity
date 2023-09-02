#!/bin/bash

# Set the FreeSurfer environment variables
export FREESURFER_HOME=/scratch/MPI-LEMON/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

# Run the Python script
python -u main.py
