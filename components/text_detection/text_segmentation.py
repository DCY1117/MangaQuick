import os
from fastai.vision import *
from fastai import *
import torch
from torchvision.utils import save_image

def comp_size(image):
    """Adjust image dimensions to even numbers.

    Args:
        image: An image object with a .size attribute.

    Returns:
        Tuple[int, int]: A tuple containing the adjusted width and height.
    """
    wid, hgt = image.size
    if wid % 2 != 0:
        wid += 1
    if hgt % 2 != 0:
        hgt += 1
    return wid, hgt

def text_segmentation(file, learner):
    """Perform text segmentation on an uploaded file.

    Args:
        uploaded_file: The uploaded file (UploadedFile object) to be processed.
        learner: The model used for prediction.

    Processes the file by resizing its dimensions to even numbers, applies
    the model prediction, and saves the resulting mask.
    """
    # Extract file name
    file_name = file.name
    name, _ = os.path.splitext(file_name)

    # Construct the mask file name
    mask_name = f'{name}_mask.png'

    # Open image
    img = open_image(file)

    # Resize image to even number   
    wid, hgt = img.size
    wid,hgt = comp_size(img)
    img.resize(torch.Size([img.shape[0],wid,hgt])).refresh()

    # Save image
    os.makedirs(f'prediction/segmentation/{name}/', exist_ok=True)
    img.save(f'prediction/segmentation/{name}/{name}.png')

    # Model text segmentation
    with torch.no_grad():
        pred = learner.predict(img)[0]  

    # Save mask as PNG
    save_image(pred.px, f'prediction/segmentation/{name}/{mask_name}')