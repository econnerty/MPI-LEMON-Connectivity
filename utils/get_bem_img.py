import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import mne
import matplotlib.pyplot as plt

def run_plot_bem_for_subject(subject_path, subjects_dir):
    subject = os.path.basename(subject_path)
    plot_bem_kwargs = dict(
        subject=subject,
        subjects_dir=subjects_dir,
        brain_surfaces="white",
        orientation="coronal",
        slices=[50, 100, 150, 200]
    )
    try:
        fig = mne.viz.plot_bem(**plot_bem_kwargs)
        plt.savefig(f"temp/{subject}.jpg")
        plt.close(fig)
        return True
    except Exception as e:
        print(f"Failed to create JPG for {subject}. Error: {e}")
        return False

def zip_images(zip_name, image_paths):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for img in image_paths:
            zipf.write(img, os.path.basename(img))

def main(input_folder="/scratch/MPI-LEMON/freesurfer/subjects"):
    if not os.path.exists("temp"):
        os.mkdir("temp")
    
    with tqdm(total=len(os.listdir(input_folder))) as pbar:
        with ThreadPoolExecutor() as executor:
            futures = []
            for subdir in os.listdir(input_folder):
                if subdir.startswith("sub-"):
                    full_subdir_path = os.path.join(input_folder, subdir)
                    if os.path.exists(full_subdir_path):
                        futures.append(executor.submit(run_plot_bem_for_subject, full_subdir_path, input_folder))
            
            # Gather successful images
            successful_images = [f"temp/{os.path.basename(future._result)}.jpg" for future in futures if future.result()]
            
            # Zip the images
            zip_images("output.zip", successful_images)

if __name__ == "__main__":
    main()

