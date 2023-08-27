#!/bin/bash

# Set the FreeSurfer environment variables
export FREESURFER_HOME=/home/aiisc/Downloads/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

# Run the Python script
python3 main.py
