#derived from https://github.com/JosePMarques/MP2RAGE-related-scripts/tree/master

import os
import tarfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import subprocess
import glob
import nibabel as nib
import numpy as np
import warnings

warnings.filterwarnings('ignore')

#constants
RAW_MRI_FOLDER = "pre_mri"  # The folder where the tar files are located

def extract_and_remove_single_tar(file_path, folder_path, pbar):
    folder_name = os.path.basename(file_path).replace(".tar.gz", "")
    output_folder_path = os.path.join(folder_path, '')
    
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    
    with tarfile.open(file_path, "r:gz") as tar_ref:
        tar_ref.extractall(path=output_folder_path)

    os.remove(file_path)
    pbar.update(1)  # Increment the progress bar

def extract_and_remove_tar_files(folder_path):
    # Fetch all the tar files in the directory
    tar_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.startswith("sub-") and f.endswith(".tar.gz")]

    # Initialize tqdm progress bar
    with tqdm(total=len(tar_files)) as pbar:
        # Use ThreadPoolExecutor to parallelize the task
        with ThreadPoolExecutor() as executor:
            executor.map(extract_and_remove_single_tar, tar_files, [folder_path] * len(tar_files), [pbar] * len(tar_files))

def MP2RAGErobustfunc(INV1, INV2, beta):
    return (np.conj(INV1) * INV2 - beta) / (INV1**2 + INV2**2 + 2*beta)

def rootsquares_pos(a, b, c):
    return (-b + np.sqrt(b**2 - 4*a*c)) / (2*a)

def rootsquares_neg(a, b, c):
    return (-b - np.sqrt(b**2 - 4*a*c)) / (2*a)

def process_images(uni_filename, inv1_filename, inv2_filename, output_filename):
    print(uni_filename)
    # Load Data
    UNIhdr = nib.load(uni_filename)
    UNIimg = np.array(UNIhdr.dataobj).astype(float)

    INV1hdr = nib.load(inv1_filename)
    INV1img = np.array(INV1hdr.dataobj).astype(float)

    INV2hdr = nib.load(inv2_filename)
    INV2img = np.array(INV2hdr.dataobj).astype(float)

    # Compute correct INV1 dataset
    INV1img = np.sign(UNIimg) * INV1img
    INV1pos = rootsquares_pos(-UNIimg, INV2img, -INV2img**2 * UNIimg)
    INV1neg = rootsquares_neg(-UNIimg, INV2img, -INV2img**2 * UNIimg)

    INV1final = INV1img
    INV1final[np.abs(INV1img-INV1pos) > np.abs(INV1img-INV1neg)] = INV1neg[np.abs(INV1img-INV1pos) > np.abs(INV1img-INV1neg)]
    INV1final[np.abs(INV1img-INV1pos) <= np.abs(INV1img-INV1neg)] = INV1pos[np.abs(INV1img-INV1pos) <= np.abs(INV1img-INV1neg)]

    # Calculate lambda (Regularization)
    multiplyingFactor = 10  # Set this value as required
    noiselevel = multiplyingFactor * np.mean(INV2img[:, -10:, -10:])
    MP2RAGEimgRobustPhaseSensitive = MP2RAGErobustfunc(INV1final, INV2img, noiselevel**2)

    # Save data
    new_image = nib.Nifti1Image(MP2RAGEimgRobustPhaseSensitive, affine=UNIhdr.affine)
    nib.save(new_image, output_filename)


def run_single_denoise_script(subdir):
    filelist_uni = glob.glob(os.path.join(subdir, "sub-*_ses-*_acq-mp2rage_T1w.nii.gz"))
    filelist_inv1 = glob.glob(os.path.join(subdir, "sub-*_ses-*_inv-1_mp2rage.nii.gz"))
    filelist_inv2 = glob.glob(os.path.join(subdir, "sub-*_ses-*_inv-2_mp2rage.nii.gz"))

    if filelist_uni and filelist_inv1 and filelist_inv2:
        parent_folder_name = os.path.basename(os.path.dirname(subdir))
        filenameUNI = filelist_uni[0]
        filenameINV1 = filelist_inv1[0]
        filenameINV2 = filelist_inv2[0]

        # Set the output filename to "denoised.nii" in the same directory
        filenameOUT = os.path.join(subdir, "denoised.nii")

        regularization = 10  # set this as required
        process_images(filenameUNI, filenameINV1, filenameINV2, filenameOUT)

def run_denoise_script(input_folder="pre_mri"):
    # Initialize tqdm progress bar
    with tqdm(total=len(os.listdir(input_folder))) as pbar:
        # Use ThreadPoolExecutor to parallelize the task
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for subdir in os.listdir(input_folder):
                if subdir.startswith("sub-"):
                    full_subdir_path = os.path.join(input_folder, subdir, "ses-01", "anat")
                    if os.path.exists(full_subdir_path):
                        futures.append(executor.submit(run_single_denoise_script, full_subdir_path))
                        
            for future in as_completed(futures):
                pbar.update(1)



if __name__ == "__main__":
    extract_and_remove_tar_files(RAW_MRI_FOLDER)
    run_denoise_script(input_folder=RAW_MRI_FOLDER)    
