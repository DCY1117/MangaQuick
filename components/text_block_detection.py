import os
import cv2
import numpy as np
from PIL import Image, ImageDraw

# Base rectangle template for JSON output
base_rect = {
    "type": "rect",
    "version": "4.4.0",
    "originX": "left",
    "originY": "top",
    "left": 28,
    "top": 41,
    "width": 213,
    "height": 264,
    "fill": "",
    "stroke": "#8fce00",
    "strokeWidth": 4,
    "strokeDashArray": None,
    "strokeLineCap": "butt",
    "strokeDashOffset": 0,
    "strokeLineJoin": "miter",
    "strokeUniform": True,
    "strokeMiterLimit": 4,
    "scaleX": 1,
    "scaleY": 1,
    "angle": 0,
    "flipX": False,
    "flipY": False,
    "opacity": 1,
    "shadow": None,
    "visible": True,
    "backgroundColor": "",
    "fillRule": "nonzero",
    "paintFirst": "fill",
    "globalCompositeOperation": "source-over",
    "skewX": 0,
    "skewY": 0,
    "rx": 0,
    "ry": 0
}

def block_detection(file, dilation_iterations):
    """
    Detect text blocks in an uploaded image using dilation and connected components analysis.

    Parameters:
    - file: The uploaded file (UploadedFile object) to be processed.
    - dilation_iterations: The number of iterations for the dilation process.

    Returns:
    - output: The result of connected components analysis on the dilated image.
    """
    
    # Extract the file name without extension
    file_name, _ = os.path.splitext(file.name)

    # Construct the path for the mask file
    mask_path = f'prediction/segmentation/{file_name}/{file_name}_mask.png'

    # Read the mask image in grayscale
    img = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    # Define the kernel size for dilation
    kernel = np.ones((5, 5), np.uint8)

    # Dilate the image
    dilated_img = cv2.dilate(img, kernel, iterations=dilation_iterations)

    # Perform connected components analysis on the dilated image
    output = cv2.connectedComponentsWithStats(dilated_img, 8, cv2.CV_32S)

    # Save the dilated mask image
    cv2.imwrite(mask_path, dilated_img)

    return output

def blocks_to_json(blocks):
    """
    Converts block data to a JSON-compatible format using a base rectangle template.

    Parameters:
    - blocks: A tuple containing the output from connected components analysis or a list of block coordinates.

    Returns:
    - A list of dictionaries, each representing a block's properties in JSON-compatible format.
    """
    rects = []

    if isinstance(blocks, tuple): # If text_blocks is a tuple, it's assumed to contain connected component analysis data
        num_labels, _, stats, _ = blocks
        for i in range(1, num_labels):
            rect = base_rect.copy()
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            rect['left']=int(x)
            rect['top']=int(y)
            rect['width']=int(width)
            rect['height']=int(height)
            rects.append(rect)
    else:
        for i in range(0,len(blocks)):
            rect = base_rect.copy()
            x = blocks[i][0]
            y = blocks[i][1]
            width = blocks[i][2]
            height = blocks[i][3]
            rect['left']=int(x)
            rect['top']=int(y)
            rect['width']=int(width)
            rect['height']=int(height)
            rects.append(rect)

    return rects

def modify_mask(file, blocks_json, canvas_json):
    """
    Modifies the mask image based on the provided canvas and blocks JSON data.

    Parameters:
    - file: The uploaded file whose mask needs modification.
    - blocks_json: JSON data representing detected blocks.
    - canvas_json: JSON data representing user-modified blocks on the canvas.

    Returns:
    - A list of blocks that were kept after modification.
    """
    # Extract the file name without extension
    file_name, _ = os.path.splitext(file.name)

    # Construct the path for the mask file
    mask_path = f'prediction/segmentation/{file_name}/{file_name}_mask.png'

    # Read the mask image in grayscale mode
    image = Image.open(mask_path)
    image_copy = image.copy()
    image_draw = ImageDraw.Draw(image_copy)

    # Remove blocks that are almost identical to the ones on the canvas
    for canvas_block in canvas_json['objects']:
        for i in range(0,len(blocks_json['objects'])):
            if rectangles_almost_identical(blocks_json, canvas_block, i):
                del blocks_json['objects'][i]
                break
    
    # Fill the remaining blocks in the mask with black
    for block in blocks_json['objects']:
        x = int(block['left'])
        y = int(block['top'])
        w = int(block['width'])
        h = int(block['height'])   
        image_draw.rectangle([(x, y), (x + w, y + h)], fill ="#000000")

    image_copy.save(mask_path, format='PNG')

def rectangles_almost_identical(blocks_json, canvas_json, i, tolerance=5):
    """
    Checks if two rectangles are almost identical within a specified tolerance.

    Parameters:
    - block_json: The block data in JSON format.
    - canvas_block: The block data from the canvas.
    - tolerance: The allowed difference in position and size.

    Returns:
    - True if the rectangles are almost identical; otherwise, False.
    """
    # Coordinates and dimensions of the first rectangle (from blocks_json)
    left1 = int(blocks_json['objects'][i]['left'])
    top1 = int(blocks_json['objects'][i]['top'])
    width1 = int(blocks_json['objects'][i]['width'])
    height1 = int(blocks_json['objects'][i]['height'])

    # Coordinates and dimensions of the second rectangle (from canvas_json)
    left2 = canvas_json['left']
    top2 = canvas_json['top']
    width2 = canvas_json['width'] * canvas_json['scaleX']
    height2 = canvas_json['height'] * canvas_json['scaleY']

    # Check if the dimensions and positions are within the tolerance
    left_diff = abs(left1 - left2) <= tolerance 
    top_diff = abs(top1 - top2) <= tolerance 
    width_diff = abs(width1 - width2) <= tolerance
    height_diff = abs(height1 - height2) <= tolerance

    # Return True if all dimensions and positions are within the tolerance
    return left_diff and top_diff and width_diff and height_diff