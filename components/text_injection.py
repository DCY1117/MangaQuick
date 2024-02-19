from PIL import ImageFont, Image, ImageDraw
import os
import cv2

def text_injection(file, texts, blocks, font, fontSize):
    """
    Injects text into an image at specified blocks using a given font style and size.

    Parameters:
    - file: The uploaded file (UploadedFile object) to be processed.
    - texts: List of strings, where each string is the text to be injected into the corresponding block.
    - blocks: List of tuples defining the blocks (x, y, width, height) or output from connected component analysis.
    - font_name: Name of the font file to use for text rendering.
    - font_size: Size of the font.
    """
    # Load the font and calculate the font size
    font_style = ImageFont.truetype(f'text_fonts/{font}', int(fontSize))

    # Extract file name without extension
    name, _ = os.path.splitext(file.name)
    mask_name = f'{name}_mask.png'

    # Load the image to be edited
    image = Image.open(f'prediction/inpainting/{name}/{mask_name}')

    # Determine the color for text based on background
    block_colors = get_block_colors(file, blocks)

    # Create a drawable image
    image_copy = image.copy()
    image_copy_draw = ImageDraw.Draw(image_copy)

    # Inject text into the image
    inject_text(texts, blocks, font_style, image_copy_draw, block_colors)

    # Save image
    os.makedirs(f'prediction/translated/', exist_ok=True)
    image_copy.save(f'prediction/translated/{name}.png', format='PNG')

def get_block_colors(file, blocks):
    """
    Determines the color for text based on the average color of the specified blocks in the image.

    Parameters:
    - file_path: File object representing the image file.
    - blocks: List of tuples defining the blocks (x, y, width, height) or output from connected component analysis.

    Returns:
    - A list of colors (0 or 255) where each color corresponds to a block, chosen based on the block's background color to ensure text visibility.
    """
    colors=[]
    # Extract the file name
    file_name = file.name
    name, _ = os.path.splitext(file_name)

    # Load the segmented image
    image = cv2.imread(f'prediction/segmentation/{name}/{name}.png')

    # Iterate through blocks to determine text color
    if isinstance(blocks, tuple): # If text_blocks is a tuple, it's assumed to contain connected component analysis data
        (num_labels, labels, stats, centroids) = blocks
        for i in range(1, num_labels):
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            crop = image[y:y+height,x:x+width]
            if crop.mean(axis=(0,1))[0] < 255/2:
                colors.append(255)
            else:
                colors.append(0)
    else:
        for i in range(0,len(blocks)):
            x = blocks[i][0]
            y = blocks[i][1]
            width = blocks[i][2]
            height = blocks[i][3]
            crop = image[y:y+height,x:x+width]
            if crop.mean(axis=(0,1))[0] < 255/2:
                colors.append(255)
            else:
                colors.append(0)
    return colors

def inject_text(texts, blocks, font, image, font_colors):
    """
    Injects the specified texts into the image at the specified blocks, using the provided font and colors.

    Parameters:
    - texts: List of strings to be injected.
    - blocks: List of tuples (x, y, width, height) defining the blocks where texts are to be injected, or a tuple containing connected component analysis output.
    - font: Font object to be used for text rendering.
    - drawable_image: ImageDraw object associated with the image to draw on.
    - font_colors: List of color values (0 or 255) for each text block.
    """
    if isinstance(blocks, tuple):
        (num_labels, labels, stats, centroids) = blocks
        for i in range(1,num_labels): 
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            result = split_text_to_fit(texts[i-1], font, width)
            place_text(result, x, y, width, height, image, font, font_colors[i-1])
    else:
        for i in range(0,len(blocks)):
            x = blocks[i][0]
            y = blocks[i][1]
            width = blocks[i][2]
            height = blocks[i][3]
            result = split_text_to_fit(texts[i-1], font, width)
            place_text(result, x, y, width, height, image, font, font_colors[i-1])

def split_text_to_fit(text, font, width_block):
    """
    Splits a text into multiple lines to fit within a specified width block.

    Parameters:
    - text (str): Text to split.
    - font: Font object used for text measurement.
    - width_block (int): Maximum width available for the text.

    Returns:
    - list of str: Text split into lines that fit the width block.
    """
    words = text.split(" ")
    sentence=""
    result=[]
    for word in words:
        if words[0] == word:
            sentence = word
        else:
            sentence = f'{sentence} {word}'
        left, top, right, bottom=font.getbbox(sentence)
        width_text = right - left
        if width_text > width_block:
            num = len(sentence.split(" "))
            if num == 1:
                sentence=''
            else:
                sentence = sentence[:sentence.rfind(" ")]
                result.append(sentence)
            sentence = word

    result.append(sentence)

    return result

def place_text(text, x, y, w, h, image, font, color):
    """
    Places text lines within a specified block in an image.

    Parameters:
    - text_lines (list of str): Text lines to place in the block.
    - x, y, w, h (int): Coordinates and dimensions of the block.
    - image_draw (ImageDraw): ImageDraw object to draw on.
    - font: Font object for text rendering.
    - color: Text color.
    """
    # Calculate the vertical start position to center the text block
    left, top, right, bottom=font.getbbox(text[0])
    width_text = right - left
    height_text = bottom - top
    y_start=(y + y + h)/2-height_text*1.2/2-(height_text*1.2/2)*(len(text)-1)

    for i in text:
        left, top, right, bottom=font.getbbox(i)
        width_text = right - left
        height_text = bottom - top
        x_line=(x + x + w)/2-width_text/2
        image.text((x_line, y_start), i, font=font, fill=(color, color, color))
        y_start += height_text * 1.2
    return image