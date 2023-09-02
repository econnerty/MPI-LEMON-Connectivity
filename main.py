import subprocess
import constants
import os

def set_environment():
    freesurfer_home = constants.FREESURFER_HOME
    os.environ["FREESURFER_HOME"] = freesurfer_home
    subprocess.run([f"source {freesurfer_home}/SetUpFreeSurfer.sh"], shell=True, executable='/bin/bash')

def run_preprocess_mri():
    try:
        # Execute the preprocess_mri.py script
        subprocess.run(["python", "-u" ,"preprocess-mri.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing preprocess-mri.py: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def run_recon_all():
    try:
        # Execute the preprocess_mri.py script
        subprocess.run(["python", "-u","recon-all.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing preprocess-mri.py: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
   #set_environment()
    #run_preprocess_mri()
    run_recon_all()
