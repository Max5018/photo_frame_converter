from PIL import Image, ExifTags, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime
import locale
import sys
import os
import yaml
from PyQt5.QtWidgets import QApplication, QFileDialog

# pyinstaller --onefile image_converter.py

os.system('cls') # # Clears the console screen for formatted text with pyinstaller

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    # https://coderslegacy.com/solving-common-problems-and-errors-pyinstaller/
    #try:
    #    # PyInstaller creates a temp folder and stores path in _MEIPASS
    #    base_path = sys._MEIPASS
    #except Exception:
    #    base_path = os.path.abspath(".")
    #return os.path.join(base_path, relative_path)

    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    #print(os.path.join(application_path, relative_path))
    return os.path.join(application_path, relative_path)

print("start")
# Load the YAML file
with open(resource_path("config.yaml"), "r") as file:
    config = yaml.safe_load(file)

max_width = config["max_width"]
max_height = config["max_height"]
out_dir = config["path_out"]
# Define the file path and the string to append
missing_date_file = resource_path("missing_date_file.txt")
error_file = resource_path("error_file.txt")


def get_photo_date_german(exif):
    #exif = img._getexif()
    if not exif:
        return "-1 Keine EXIF-Daten gefunden"
    for tag_id, value in exif.items():
        tag = ExifTags.TAGS.get(tag_id)
        if tag == "DateTimeOriginal":
            try:
                # Set locale to German
                locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")  # May vary by system
            except locale.Error:
                return "-1 German locale not available on this system"

            dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
            #return dt.strftime("%d. %B %Y")  # e.g., "23. Juni 2025" 
            # https://stackoverflow.com/questions/904928/python-strftime-date-without-leading-0
            return dt.strftime("%#d. %B %Y")  # e.g., "23. Juni 2025"

    return "-1 Aufnahmedatum nicht gefunden"

def add_bottom_text(img, text="Sample Text"):
    padding= config["padding"]
    font_size= config["font_size"]
    font_path=resource_path("Roboto_SemiCondensed-Regular.ttf")
    radius = config["radius"]
    bg_color=(255, 255, 255, 175)
    #border_color=(150, 150, 150, 255)   # Bright grey

    draw = ImageDraw.Draw(img)
    # Use custom font or default
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()
    #text_width, text_height = draw.textsize(text, font=font)
    text_width = draw.textlength(text, font=font)
    text_height = font_size
    # Coordinates: centered horizontally, above the bottom by padding
    x = 10 #(img.width - text_width) / 2
    y = img.height - text_height - padding - 20
    
    box_width = text_width + 2 * padding + 20
    box_height = text_height + 2 * padding

    # Create transparent overlay for rectangle
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(x, y), (x + box_width, y + box_height)],
        radius=radius,
        fill=bg_color
        #fill=bg_color,
        #outline=border_color,
        #width=3
    )

    # Merge overlay with base image
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    # Draw text
    draw = ImageDraw.Draw(img)  # Redraw to avoid transparency issues
    draw.text((x+20, y+8), text, font=font, fill="black")

    img = img.convert("RGB")
    return img

def select_base_directory():
    app = QApplication(sys.argv)
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    
    if dialog.exec_():
        selected_dirs = dialog.selectedFiles()
        return selected_dirs[0].replace("/","\\")  # Return selected directory path
    return None

def resize_image_keep_aspect(image, output_size): # output_size: width, height
    """
    Resize an image to fit within output_size (width, height), preserving aspect ratio.
    Upscales if the image is smaller than output_size.
    """
    original_width, original_height = image.size
    target_width, target_height = output_size

    # Calculate the scaling factor
    scale = min(target_width / original_width, target_height / original_height)

    # Compute new size
    new_size = (int(original_width * scale), int(original_height * scale))

    # Resize the image
    resized_img = image.resize(new_size, Image.LANCZOS)

    return resized_img

def process_single_image(full_path,newFile):
    try:
        # Get orientation tag ID
        for orientation in ExifTags.TAGS:
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        # https://jdhao.github.io/2019/07/31/image_rotation_exif_info/
        # rotation: 1: 0°
        #           3: 180°
        #           6: 90°
        #           8: 270°

        img = Image.open(full_path)
        exif_data = img.info.get("exif")
        exif = img._getexif()

        # Extract EXIF data and get orientation if present
        if exif and orientation in exif:
            rotation = exif[orientation]
            #print("EXIF orientation:", rotation)
        else:
            #print("No EXIF orientation tag found.")
            print(f"{bcolors.WARNING}\tNo EXIF orientation tag found.{bcolors.ENDC}")
            # write to errorfile - open the file in append mode and write the string
            errortext = "No EXIF orientation tag" + "\t" + full_path + "\n"
            with open(error_file, "a") as file:
                file.write(errortext)
            rotation = -1

        # https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image
        if   rotation == 3: 
            img=img.rotate(180, expand=True)
        elif rotation == 6: 
            img=img.rotate(270, expand=True)
        elif rotation == 8: 
            img=img.rotate(90, expand=True)
        
        # scale image ("scale inside") # scales only downwards
        # img.thumbnail((max_width, max_height), Image.LANCZOS)
        img = resize_image_keep_aspect(img, (max_width, max_height))

        text = get_photo_date_german(exif)
        #print(text)
        if text.startswith("-1"):
            print(f"{bcolors.WARNING}\tEXIF date not found.{bcolors.ENDC}")
            global fileindex
            fileindex = int(fileindex) + 1
            text_on_img="ohne Datum"
            if config["write_missing_date_number"] == True:
                text_on_img += " [" + str(fileindex) + "]"
            img = add_bottom_text(img,text=text_on_img)
            # write to errorfile - open the file in append mode and write the string
            errortext = text + "\t" + full_path + "\n"
            with open(error_file, "a") as file:
                file.write(errortext)
            if config["write_missing_date_number"] == True:
                with open(missing_date_file, "a") as file:
                    errortext = str(fileindex) + "\t" + full_path + "\n"
                    file.write(errortext)

        else:
            img = add_bottom_text(img,text=text)
        #special filter:
        #if not "März" in text: # Nur BIlder aus März
        #    return

        # zurückdrehen
        if   rotation == 3 : 
            img=img.rotate(180, expand=True)
        elif rotation == 6 : 
            img=img.rotate(90, expand=True)
        elif rotation == 8 : 
            img=img.rotate(270, expand=True)

        #new_name = Path(x).stem+"_small.jpg" # https://stackoverflow.com/questions/678236/how-do-i-get-the-filename-without-the-extension-from-a-path-in-python
        #print(new_name)
        # Create the target directory if it doesn't exist
        Path(newFile).parent.mkdir(parents=True, exist_ok=True)
        if exif_data:
            #rewrite exif to image
            img.save(newFile, "JPEG", quality=85, exif=exif_data)
        else:
            img.save(newFile, "JPEG", quality=85)


    except Exception as e: 
        print(e)
        pass

def get_first_value_of_last_line(file_path):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            if not lines:
                return None  # File is empty

            last_line = lines[-1].strip()

            values = last_line.split("\t")
            return values[0] if values else None
    except FileNotFoundError:
        print("File not found.")
        return None

fileindex = get_first_value_of_last_line(missing_date_file)

base_dir = select_base_directory()
print(base_dir)

# count files
# Set the desired file extension (e.g., '.txt', '.jpg')
file_extension = ".jpg" # case insensitive
# Count matching files
file_count = len(list(Path(base_dir).rglob(f"*{file_extension}")))
print(f"Number of {file_extension} files: {file_count}")
idx = 0
if base_dir:
    for root_dir, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.lower().endswith(".jpg"):
                idx = idx+1
                print(f"Processing file {idx} of {file_count}")
                full_path = os.path.join(root_dir, filename)
                print(f"\tfrom: {full_path}")
                newFile = full_path.replace(base_dir, out_dir)
                newFile = newFile.replace(".jpg", "_small.jpg")
                newFile = newFile.replace(".JPG", "_small.jpg")
                print(f"\tas:   {newFile}")

                # A: Überschreiben inaktiv und Datei existiert nicht; B: oder Überschreiben aktiv
                if config["overwrite"] == False and not Path(newFile).exists() or config["overwrite"] == True: 
                    process_single_image(full_path,newFile)
                else:
                    print(f"{bcolors.FAIL}\tskip: File already exists{bcolors.ENDC}")
                    #print("skip: File already exists")
else:
    print("No directory selected.")

