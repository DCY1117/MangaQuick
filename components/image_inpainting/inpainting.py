import os

def inpainting():
    """
    Runs the LaMa inpainting model on the segmentation results to inpaint the missing regions.
    """

    current_directory = os.getcwd()

    os.system(f'python {current_directory}/components/image_inpainting/bin/predict.py model.path={current_directory}/components/image_inpainting/models/big-lama indir={current_directory}/prediction/segmentation outdir={current_directory}/prediction/inpainting/')