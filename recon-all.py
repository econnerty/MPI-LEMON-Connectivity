import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import constants


def run_recon_all(subdir):
    nii_file_path = os.path.join(subdir, 'ses-01', 'anat', 'denoised.nii')
    subject_name = os.path.basename(subdir)
    cmd = [
        'recon-all',
        '-i', nii_file_path,
        '-s', subject_name,
        '-all'
    ]
    
    # Create or open a log file to capture stdout and stderr
    with open(f"./logs/log_{subject_name}.txt", "w") as log_file:
        print(f"Processing: {subject_name}")  # Print subject currently being processed
        
        try:
            subprocess.run(cmd, stdout=log_file, stderr=log_file, check=True)
            print(f"Successfully processed {subject_name}")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while processing {subject_name}: {e}")




def main():
    # Get a list of all folders within 'pre_mri'
    pre_mri_path = 'pre_mri'  # Update this to the full path if necessary
    subdirs = [os.path.join(pre_mri_path, d) for d in os.listdir(pre_mri_path) if os.path.isdir(os.path.join(pre_mri_path, d))]

    # Run recon-all in parallel with batches of 4
    with ThreadPoolExecutor(max_workers=constants.NUM_OF_CPU_CORES) as executor:
        executor.map(run_recon_all, subdirs)

if __name__ == "__main__":
    main()
