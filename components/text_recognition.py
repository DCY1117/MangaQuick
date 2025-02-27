import cv2
import os
from PIL import Image

def ocr(file, text_blocks, ocr_model, ocr_type):
    """
    Performs OCR on specified blocks of an image file using the provided OCR model.

    Parameters:
    - file: The uploaded file (UploadedFile object) to be processed.
    - text_blocks: Blocks within the image to perform OCR on, defined as tuples or connected component analysis output.
    - ocr_model: OCR model to use for text extraction.

    Returns:
    - list of str: Extracted texts from each block.
    """
    # Extract the base name of the file without the extension
    name, _ = os.path.splitext(file.name)

    # Read the image file
    image = cv2.imread(f'prediction/segmentation/{name}/{name}.png')
    
    # Get image dimensions
    y_len, x_len, _ = image.shape

    # Extract text from defined blocks using OCR model
    return block_to_text(image, text_blocks, x_len, y_len, ocr_model, ocr_type)

def block_to_text(image, text_blocks, x_len, y_len, ocr_model, ocr_type):
    """
    Extracts text from specified blocks of an image using OCR.

    Parameters:
    - image: Image array.
    - text_blocks: Blocks within the image to perform OCR on, defined as tuples or connected component analysis output.
    - x_len, y_len: Dimensions of the image.
    - ocr_model: OCR model to use for text extraction.

    Returns:
    - list of str: Extracted texts from each block.
    """
    texts=[]
    if isinstance(text_blocks, tuple): # If text_blocks is a tuple, it's assumed to contain connected component analysis data
        (num_labels, labels, stats, centroids) = text_blocks
        for i in range(1,num_labels):
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]

            # Adjust block dimensions with padding if within image boundaries
            if(y-15 > 0 and y+height+15 <= y_len and x-15 > 0 and x+width+15 <= x_len):
                cropped = image[y-15:y+height+15, x-15:x+width+15].copy()
            else:
                cropped = image[y:y+height, x:x+width].copy()

            # Convert cropped array to PIL image for OCR
            pil_image = Image.fromarray(cropped)
            if ocr_type == 'manga_ocr':
                text = ocr_model(pil_image)
            elif ocr_type == 'easyocr':
                result = ocr_model.readtext(cropped)
                #print(result)
                text = ' '.join([res[1] for res in result])
            # elif ocr_type == 'PaddleOCR':
            #     result = ocr_model.ocr(image, det=False)
            #     print(result)
            #     text = ' '.join([res[0][0] for res in result])



            else:
                text = ''
            texts.append(text)
            print(f"'{text}'")
    else:
        for i in range(0,len(text_blocks)):
            x = text_blocks[i][0]
            y = text_blocks[i][1]
            width = text_blocks[i][2]
            height = text_blocks[i][3]

            # Adjust block dimensions with padding if within image boundarie
            if(y-15 > 0 and y+height+15 <= y_len and x-15 > 0 and x+width+15 <= x_len):
                cropped = image[y-15:y+height+15, x-15:x+width+15].copy()
            else:
                cropped = image[y:y+height, x:x+width].copy()

            # Convert cropped array to PIL image for OCR
            pil_image = Image.fromarray(cropped)
            if ocr_type == 'manga_ocr':
                text = ocr_model(pil_image)
            elif ocr_type == 'easyocr':
                result = ocr_model.readtext(cropped)
                text = ' '.join([res[1] for res in result])
            # elif ocr_type == 'PaddleOCR':
            #     result = ocr_model.ocr(cropped, det=False)
            #     print(result)
            #     text = ' '.join([res[0][0] for res in result])
            else:
                text = ''
            texts.append(text)
            print(f"'{text}'")
        
    return texts