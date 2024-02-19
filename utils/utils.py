import zipfile
import os

def zip_directory(directory_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                zipf.write(os.path.join(root, file), 
                           os.path.relpath(os.path.join(root, file), 
                                           os.path.join(directory_path, '..')))
                
def update_progress(total_files, progress_bar, i):
    """Update the progress of the upload to the client."""
    # Calculate the percentage completion
    # Calculate the percentage completion
    percent_complete = int(100 * (int(i) + 1) / int(total_files))
    
    # Update the progress bar with the current percentage
    progress_bar.progress(percent_complete)