import sys
import os
from PyQt5.QtWidgets import QApplication, QFileDialog
from pathlib import Path

def select_base_directory():
    app = QApplication(sys.argv)
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    
    if dialog.exec_():
        selected_dirs = dialog.selectedFiles()
        return selected_dirs[0]  # Return selected directory path
    return None

base_dir = select_base_directory()
print(base_dir)
file_extension = ".jpg" # case insensitive
file_count = len(list(Path(base_dir).rglob(f"*{file_extension}")))
print(f"Number of {file_extension} files: {file_count}")

if base_dir:
    for root_dir, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.lower().endswith(".jpg"):
                full_path = os.path.join(root_dir, filename)
                print(f"Processing: {full_path}")
                
                # --- PLACEHOLDER START ---
                # Insert your image-processing logic here
                # For example: open the image, add watermark, resize, etc.
                # --- PLACEHOLDER END ---
else:
    print("No directory selected.")
