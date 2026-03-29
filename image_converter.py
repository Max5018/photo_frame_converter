from PIL import Image, ExifTags, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime
import locale

img_h_pana = "P1440846.JPG"
img_v_pana = "P1440916.JPG"
img_h_andr = "20250623_180807.jpg"
img_v_andr = "20250623_180800.jpg"

max_width = 2000
max_height = 1200

def get_photo_date_german(exif):
    #exif = img._getexif()
    if not exif:
        return "Keine EXIF-Daten gefunden"
    for tag_id, value in exif.items():
        tag = ExifTags.TAGS.get(tag_id)
        if tag == "DateTimeOriginal":
            try:
                # Set locale to German
                locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")  # May vary by system
            except locale.Error:
                return "German locale not available on this system"

            dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
            #return dt.strftime("%d. %B %Y")  # e.g., "23. Juni 2025" 
            # https://stackoverflow.com/questions/904928/python-strftime-date-without-leading-0
            return dt.strftime("%#d. %B %Y")  # e.g., "23. Juni 2025"

    return "Aufnahmedatum nicht gefunden"

def add_bottom_text(img, text="Sample Text"):
    padding=10
    font_size=30
    font_path="Roboto_SemiCondensed-Regular.ttf"
    radius = 50
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

    #items = ["P1440846.JPG","P1440916.JPG","20250623_180807.jpg","20250623_180800.jpg"]
    items = [img_h_pana,img_v_pana,img_h_andr,img_v_andr]
    #items = [img_h_pana]
    for x in items:
        print(x)
        img = Image.open(x)
        exif_data = img.info.get("exif")
        exif = img._getexif()

        # Extract EXIF data and get orientation if present
        if exif and orientation in exif:
            rotation = exif[orientation]
            print("EXIF orientation:", rotation)
        else:
            print("No EXIF orientation tag found.")

        # https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image
        if   rotation == 3 : 
            img=img.rotate(180, expand=True)
        elif rotation == 6 : 
            img=img.rotate(270, expand=True)
        elif rotation == 8 : 
            img=img.rotate(90, expand=True)

        # scale image ("scale inside")
        img.thumbnail((max_width, max_height), Image.LANCZOS)

        text = get_photo_date_german(exif)
        print(text)
        img = add_bottom_text(img,text=text)

        # zurückdrehen
        if   rotation == 3 : 
            img=img.rotate(180, expand=True)
        elif rotation == 6 : 
            img=img.rotate(90, expand=True)
        elif rotation == 8 : 
            img=img.rotate(270, expand=True)

        new_name = Path(x).stem+"_small.jpg" # https://stackoverflow.com/questions/678236/how-do-i-get-the-filename-without-the-extension-from-a-path-in-python
        print(new_name)
        if exif_data:
            #rewrite exif to image
            img.save(new_name, "JPEG", quality=85, exif=exif_data)
        else:
            img.save(new_name, "JPEG", quality=85)


except Exception as e: 
    print(e)
    pass