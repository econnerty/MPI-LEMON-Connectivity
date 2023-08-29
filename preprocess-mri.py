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
import constants

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



##This set of functions taken from  https://github.com/khanlab/tar2bids/blob/master/etc/mp2rage_genUniDen.py
def MP2RAGErobustfunc(INV1, INV2, beta):
    # matalb: MP2RAGErobustfunc=@(INV1,INV2,beta)(conj(INV1).*INV2-beta)./(INV1.^2+INV2.^2+2*beta);
    return (np.conj(INV1)*INV2-beta)/(INV1**2+INV2**2+2*beta)


def rootsquares_pos(a, b, c):
    # matlab:rootsquares_pos=@(a, b, c)(-b+sqrt(b. ^ 2 - 4 * a.*c))./(2*a)
    return (-b+np.sqrt(b**2 - 4*a*c))/(2*a)


def rootsquares_neg(a, b, c):
    # matlab: rootsquares_neg = @(a, b, c)(-b-sqrt(b. ^ 2 - 4 * a.*c))./(2*a)
    return (-b-np.sqrt(b**2 - 4*a*c))/(2*a)

def process_images(uni_filename, inv1_filename, inv2_filename, output_filename, integerformat=0):
    #########
    # load data
    #########
    MP2RAGEimg = nib.load(uni_filename)
    INV1img = nib.load(inv1_filename)
    INV2img = nib.load(inv2_filename)

    MP2RAGEimg_img = MP2RAGEimg.get_fdata()
    INV1img_img = INV1img.get_fdata()
    INV2img_img = INV2img.get_fdata()

    if MP2RAGEimg_img.min() >= 0 and MP2RAGEimg_img.max() >= 0.51:
       # converts MP2RAGE to -0.5 to 0.5 scale - assumes that it is getting only positive values
        MP2RAGEimg_img = (
            MP2RAGEimg_img - MP2RAGEimg_img.max()/2)/MP2RAGEimg_img.max()
        integerformat = 1
    else:
        integerformat = 0

    #########
    # computes correct INV1 dataset
    #########
    # gives the correct polarity to INV1
    INV1img_img = np.sign(MP2RAGEimg_img)*INV1img_img

    # because the MP2RAGE INV1 and INV2 is a sum of squares data, while the
    # MP2RAGEimg is a phase sensitive coil combination.. some more maths has to
    # be performed to get a better INV1 estimate which here is done by assuming
    # both INV2 is closer to a real phase sensitive combination

    # INV1pos=rootsquares_pos(-MP2RAGEimg.img,INV2img.img,-INV2img.img.^2.*MP2RAGEimg.img);
    INV1pos = rootsquares_pos(-MP2RAGEimg_img,
                              INV2img_img, -INV2img_img**2*MP2RAGEimg_img)
    INV1neg = rootsquares_neg(-MP2RAGEimg_img,
                              INV2img_img, -INV2img_img**2*MP2RAGEimg_img)

    INV1final = INV1img_img

    INV1final[np.absolute(INV1img_img-INV1pos) > np.absolute(INV1img_img-INV1neg)
              ] = INV1neg[np.absolute(INV1img_img-INV1pos) > np.absolute(INV1img_img-INV1neg)]
    INV1final[np.absolute(INV1img_img-INV1pos) <= np.absolute(INV1img_img-INV1neg)
              ] = INV1pos[np.absolute(INV1img_img-INV1pos) <= np.absolute(INV1img_img-INV1neg)]

    # usually the multiplicative factor shouldn't be greater then 10, but that
    # is not the ase when the image is bias field corrected, in which case the
    # noise estimated at the edge of the imagemight not be such a good measure

    multiplyingFactor = 55
    noiselevel = multiplyingFactor*np.mean(INV2img_img[:, -11:, -11:])

    # % MP2RAGEimgRobustScanner = MP2RAGErobustfunc(INV1img.img, INV2img.img, noiselevel. ^ 2)
    MP2RAGEimgRobustPhaseSensitive = MP2RAGErobustfunc(
        INV1final, INV2img_img, noiselevel**2)

    if integerformat == 0:
        MP2RAGEimg_img = MP2RAGEimgRobustPhaseSensitive
    else:
        MP2RAGEimg_img = np.round(4095*(MP2RAGEimgRobustPhaseSensitive+0.5))

    #########
    # save image
    #########
    MP2RAGEimg_img = nib.casting.float_to_int(MP2RAGEimg_img,'int16');
    new_MP2RAGEimg = nib.Nifti1Image(MP2RAGEimg_img, MP2RAGEimg.affine, MP2RAGEimg.header)
    nib.save(new_MP2RAGEimg, output_filename)



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
        with ThreadPoolExecutor(max_workers=constants.NUM_OF_CPU_CORES) as executor:
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
