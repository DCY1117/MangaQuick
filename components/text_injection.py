import os
import cv2
from PIL import Image, ImageDraw, ImageFont

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
    font_path = f'text_fonts/{font}'
    font_style = ImageFont.truetype(font_path, int(fontSize))
    font_style._font_path = font_path

    name, _ = os.path.splitext(file.name)
    mask_name = f'{name}_mask.png'

    # Load the image to be edited
    image = Image.open(f'prediction/inpainting/{name}/{mask_name}')

    # Determine the color for text based on background
    block_colors = get_block_colors(file, blocks)

    # Create a drawable image
    image_copy = image.copy()
    image_draw = ImageDraw.Draw(image_copy)

    # Inject text into the image
    inject_text(texts, blocks, font_style, image_draw, block_colors)

    # Save image
    os.makedirs('prediction/translated/', exist_ok=True)
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
    colors = []
    name, _ = os.path.splitext(file.name)
    image = cv2.imread(f'prediction/segmentation/{name}/{name}.png')
    # Iterate through blocks to determine text color
    if isinstance(blocks, tuple):
        (num_labels, labels, stats, centroids) = blocks
        for i in range(1, num_labels):
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            crop = image[y:y+height, x:x+width]
            colors.append(255 if crop.mean(axis=(0,1))[0] < 127.5 else 0)
    else:
        for block in blocks:
            x, y, width, height = block
            crop = image[y:y+height, x:x+width]
            colors.append(255 if crop.mean(axis=(0,1))[0] < 127.5 else 0)
    return colors

def inject_text(texts, blocks, font, image_draw, font_colors):
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
        for i in range(1, num_labels):
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            adjusted_font, lines = adjust_font_to_fit(texts[i-1], width, height, font)
            place_text(lines, x, y, width, height, image_draw, adjusted_font, font_colors[i-1])
    else:
        for i, block in enumerate(blocks):
            x, y, width, height = block
            adjusted_font, lines = adjust_font_to_fit(texts[i], width, height, font)
            place_text(lines, x, y, width, height, image_draw, adjusted_font, font_colors[i])

def adjust_font_to_fit(text, block_width, block_height, font):
    initial_size = font.size
    font_path = getattr(font, '_font_path', None)
    
    def natural_split_no_break(text, font, width):
        words = text.split()
        if not words:
            return [""]
        if (font.getbbox(words[0])[2] - font.getbbox(words[0])[0]) > width:
            return None
        lines = []
        current_line = words[0]
        for word in words[1:]:
            candidate = current_line + " " + word
            if (font.getbbox(candidate)[2] - font.getbbox(candidate)[0]) <= width:
                current_line = candidate
            else:
                if (font.getbbox(word)[2] - font.getbbox(word)[0]) > width:
                    return None
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines

    def break_word(text, font, width):
        parts = []
        current = ""
        for char in text:
            test = current + char
            if (font.getbbox(test)[2] - font.getbbox(test)[0]) <= width:
                current = test
            else:
                if current:
                    parts.append(f"{current}-")
                current = char
        if current:
            parts.append(current)
        return parts

    def break_text_allowing_breaks(text, font, width):
        words = text.split()
        if not words:
            return [""]
        lines = []
        current_line = ""
        for word in words:
            candidate = word if not current_line else current_line + " " + word
            if (font.getbbox(candidate)[2] - font.getbbox(candidate)[0]) <= width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                if (font.getbbox(word)[2] - font.getbbox(word)[0]) > width:
                    broken = break_word(word, font, width)
                    lines.extend(broken)
                    current_line = ""
                else:
                    current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    best_size = None
    best_lines = None
    min_size = 6
    for size in range(min_size, initial_size + 1):
        test_font = ImageFont.truetype(font_path, size)
        test_font._font_path = font_path
        lines = natural_split_no_break(text, test_font, block_width)
        if lines is None:
            break
        bbox = test_font.getbbox("Ay")
        line_height = bbox[3] - bbox[1]
        spacing = 0.2 * line_height
        total_height = line_height * len(lines) + spacing * (len(lines) - 1)
        if total_height <= block_height:
            best_size = size
            best_lines = lines
        else:
            break

    if best_size is None:
        best_size = min_size
        final_font = ImageFont.truetype(font_path, best_size)
        final_font._font_path = font_path
        final_lines = break_text_allowing_breaks(text, final_font, block_width)
        return final_font, final_lines
    else:
        final_font = ImageFont.truetype(font_path, best_size)
        final_font._font_path = font_path
        return final_font, best_lines


def place_text(text_lines, x, y, w, h, image_draw, font, color):
    """
    Places text lines within a specified block in an image.
    Parameters:
    - text_lines (list of str): Text lines to place in the block.
    - x, y, w, h (int): Coordinates and dimensions of the block.
    - image_draw (ImageDraw): ImageDraw object to draw on.
    - font: Font object for text rendering.
    - color: Text color.
    """
    line_heights = []
    line_widths = []
    for line in text_lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        line_widths.append(line_width)
        line_heights.append(line_height)
    spacing = 0.2 * (line_heights[0] if line_heights else 0)
    total_text_height = sum(line_heights) + spacing * (len(text_lines) - 1) if line_heights else 0
    y_start = y + (h - total_text_height) / 2

    for i, line in enumerate(text_lines):
        x_line = x + (w - line_widths[i]) / 2
        image_draw.text((x_line, y_start), line, font=font, fill=(color, color, color))
        y_start += line_heights[i] + spacing
    return image_draw
