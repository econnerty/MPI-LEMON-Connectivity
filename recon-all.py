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
    cmd2 = [
        'mne',
        'watershed_bem',
        '-s', subject_name
    ]
    try:
        os.makedirs(f"./logs/{subject_name}", exist_ok=True)
    except Exception as e:
        print(f"Failed to create directory: {e}")
        return

    # Create or open a log file to capture stdout and stderr
    with open(f"./logs/{subject_name}/recon_all_{subject_name}.txt", "w") as log_file:
        print(f"Processing: {subject_name}")  # Print subject currently being processed
        
        try:
            subprocess.run(cmd, stdout=log_file, stderr=log_file, check=True) #recon all
            print(f"Successfully processed {subject_name}")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while processing {subject_name}: {e}")
    # Create or open a log file to capture stdout and stderr
    with open(f"./logs/{subject_name}/mne_watershed_{subject_name}.txt", "w") as log_file:
        print(f"Processing: {subject_name}")  # Print subject currently being processed   
        try:
            subprocess.run(cmd2, stdout=log_file, stderr=log_file, check=True) #bem solution
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
