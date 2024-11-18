# Standard library imports
import os
import sys
import time
import shutil
import json

# Third-party library imports
import streamlit as st
import torch
from fastai.vision.all import load_learner #API Update to fastai.vision.all https://forums.fast.ai/t/fastai-v2-upgrade-review-guide-whats-new-in-fastai-version-2/86626
from fastai.vision.all import *
from PIL import Image
import deepl
from dotenv import load_dotenv
from ruamel.yaml import YAML
from streamlit_drawable_canvas import st_canvas
from manga_ocr import MangaOcr

# Custom module imports for various components of the comic translation app
from components.text_detection.text_segmentation import text_segmentation
from components.text_block_detection import block_detection, blocks_to_json, modify_mask
from components.text_recognition import ocr
from components.text_translation import translate_texts
from components.image_inpainting.inpainting import inpainting
from components.text_injection import text_injection
from utils.utils import *

# Set Streamlit page configuration
##############################################################
st.set_page_config(
     page_title="MangaQuick",
     page_icon='components/webpage_assets/page_icon_no_bg.png',
     layout="wide",
)

# Session state
##############################################################
# Initial state
if 'init' not in st.session_state:
    st.session_state['init'] = True

# Segmentation and text block detection
if 'process files' not in st.session_state:
    st.session_state['process files'] = False

# Modify text boxes
if 'modify' not in st.session_state:
    st.session_state['modify'] = False

# Current file index for text box modification
if 'current_file_index' not in st.session_state:
    st.session_state['current_file_index'] = 0

# Download state
if 'download' not in st.session_state:
    st.session_state['download'] = False

# Initialize the list of text blocks, canvas rectangles, texts, and translated texts
if 'blocks' not in st.session_state:
    st.session_state['blocks'] = []

if 'texts' not in st.session_state:
    st.session_state['texts'] = []

if 'text_translated' not in st.session_state:
    st.session_state['text_translated'] = []

# Timer
if 'start_time' not in st.session_state:
    st.session_state['start_time'] = 0

# Sidebar
##############################################################

# Define available languages and their codes
languages={ 
    "Bulgarian" : "BG",
    "Czech" : "CS",
    "Danish" : "DA",
    "German" : "DE",
    "Greek" : "EL",
    "English (British)" : "EN-GB",
    "English (American)" : "EN-US",
    "Spanish" : "ES",
    "Estonian" : "ET",
    "Finnish" : "FI",
    "French" : "FR",
    "Hungarian" : "HU",
    "Italian" : "IT",
    "Japanese" : "JA",
    "Lithuanian" : "LT",
    "Latvian" : "LV",
    "Dutch" : "NL",
    "Polish" : "PL",
    "Portuguese" : "PT-PT", 
    "Portuguese (Brazilian)" : "PT-BR",
    "Romanian" : "RO",
    "Russian" : "RU",
    "Slovak" : "SK",
    "Slovenian" : "SL",
    "Swedish" : "SV",
    "Chinese" : "ZH"
}

# Load fonts from the 'text_fonts' directory
fonts={}
for filename in os.listdir('text_fonts'):
    f = os.path.join('text_fonts',filename)
    if os.path.isfile(f):
        name = os.path.splitext(filename)[0]
        fonts[name]=filename   

model_names = os.listdir('components/text_detection/models')

# Sidebar widgets
with st.sidebar:
    # Device selection for segmentation
    with st.expander("Text segmentation", expanded=True):
        model_name = st.selectbox('Model', model_names, 0)
        segmentation_device = st.selectbox('Segmentation device', ('cuda', 'cpu'), 0)

    # Text block detection settings
    with st.expander("Text block detection", expanded=False):
        dilation_iter = st.slider(
        'Dilation iterations:',
        0,20,3)
        Modify = st.checkbox("Modify text boxes", False)
    
    # Device selection for OCR
    ocr_device = st.selectbox('OCR device', ('cuda', 'cpu'), 0)
    
    # Translation settings
    with st.expander("Translation", expanded=True):
        deepl_key = st.text_input('DeepL_key:',value=os.getenv('DEEPL_KEY'))
        target_language=st.selectbox('target_language',languages.keys(), index=6)

    # Device selection for inpainting
    inpainting_device=st.selectbox('Inpainting device',('cuda','cpu'), 0)

    # Text injection settings
    with st.expander("Text injection", expanded=False):
        fontSize = st.number_input('Font_size',value=15,step=1)
        font_style=st.selectbox('Font',fonts.keys())

# Load cached data
##############################################################

@st.cache_resource
def load_enviroment():
    """
    Loads the environment variables from a .env file.
    """
    load_dotenv()

# Load environment variables at the start
load_enviroment()

@st.cache_resource
def modify_sys_path():
    """
    Adds the text detection component directory to the system path if not already present,
    enabling imports from this directory.
    """
    if 'components/text_detection' not in sys.path:
        sys.path.append('./components/text_detection')

# Modify the system path to ensure imports work correctly
modify_sys_path()

@st.cache_resource
def load_segmentation_model(segmentation_device, model_name):
    """
    Loads and returns the text segmentation model based on the specified device (cuda or cpu).

    Parameters:
    - device (str): The device to use for the model ('cuda' or 'cpu').

    Returns:
    - The loaded text segmentation model.
    """
    defaults.device = torch.device(segmentation_device)
    model = load_learner('.', f'components/text_detection/models/{model_name}')

    return model

# Load the text segmentation model using the selected device
text_segmentation_model = load_segmentation_model(segmentation_device, model_name)

@st.cache_resource
def load_ocr(ocr_device):
    """
    Initializes and returns the OCR model, optionally forcing CPU usage.

    Parameters:
    - device (str): The device to use ('cuda' or 'cpu').

    Returns:
    - An instance of the MangaOcr model.
    """
    if ocr_device == "cuda":
        mocr = MangaOcr(force_cpu=False)
    else:
        mocr = MangaOcr(force_cpu=True)

    return mocr

# Load the OCR model using the selected device
ocr_model = load_ocr(ocr_device)

@st.cache_resource
def set_inpainting_device(inpainting_device):
    """
    Configures the device setting for the image inpainting model in its configuration file.

    Parameters:
    - device (str): The device to use for inpainting ('cuda' or 'cpu').
    """
    yaml = YAML()
    mf = pathlib.Path('components/image_inpainting/configs/prediction/default.yaml')
    doc = yaml.load(mf)
    doc['device'] = inpainting_device
    yaml.dump(doc, mf)

# Configure the device for the inpainting model
set_inpainting_device(inpainting_device)

# Main content
##############################################################

# File uploader widget allowing multiple CSV files
uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)

if uploaded_files is not None:
    # Create a list of filenames from the uploaded files
    file_names = [uploaded_file.name for uploaded_file in uploaded_files]

     # Use a select box for the user to choose an image
    selected_file_name = st.selectbox("Select an image to display", file_names)

    # Find the selected file
    selected_file = next((uploaded_file for uploaded_file in uploaded_files if uploaded_file.name == selected_file_name), None)

    if selected_file is not None:
        # Display the selected image
        image = Image.open(selected_file)
        st.image(image, caption=selected_file_name)


# Check if the session is initialized
if st.session_state['init']:
    # Create a button in the Streamlit UI to process files
    if st.button('Process Files'):
        # Record the start time of the process
        st.session_state['start_time'] = time.time()
        
        # Create a containers for progress updates
        progress_container = st.empty()
        progress_container.write("Text segmentation in progress...")
        progress_bar = st.progress(0)

        # Count the total number of uploaded files
        total_files = len(uploaded_files)

        # Process each uploaded file for text segmentation
        for i, uploaded_file in enumerate(uploaded_files):
            text_segmentation(
                file = uploaded_file, 
                learner = text_segmentation_model
            )

            update_progress(total_files, progress_bar, i)
            torch.cuda.empty_cache()

        # Update the progress
        progress_bar.progress(100)
        progress_bar.empty() # Hide the progress bar
        progress_container.write("Text block detection in progress...")
        progress_bar = st.progress(0)

        # Detect text blocks in each segmented text
        for i, uploaded_file in enumerate(uploaded_files):
            st.session_state['blocks'].append(block_detection(
                file=uploaded_file, 
                dilation_iterations=dilation_iter
            ))

            update_progress(total_files, progress_bar, i)
            torch.cuda.empty_cache()

        # Update the progress
        progress_bar.progress(100)
        progress_bar.empty()
        progress_container.empty()

        # Update session state
        st.session_state['process files'] = True
        st.session_state['download'] = False
        st.session_state['init'] = False

# Check if modification is enabled and files have been processed
if Modify and st.session_state['process files']:
    # Ensure the current file index is within the range of uploaded files
    if st.session_state['current_file_index'] < len(uploaded_files):
        current_file = uploaded_files[st.session_state['current_file_index']]
        file_name = current_file.name
        name, _ = os.path.splitext(file_name)

        # Load the background image for the current file
        bg_image = Image.open(f'prediction/segmentation/{name}/{name}.png')
        width, height = bg_image.size

        # Convert blocks to a format suitable for the canvas
        blocks = blocks_to_json(st.session_state['blocks'][st.session_state['current_file_index']])
        blocks = {"version": "4.4.0", "objects": blocks}
        blocks_json = json.dumps(blocks)
        blocks_json = json.loads(blocks_json)

        #  Set up the canvas for annotation modification
        canvas_result = st_canvas(
            initial_drawing=blocks_json,
            background_image=bg_image,
            drawing_mode='transform',
            height=height,
            width=width,
            fill_color='',
            stroke_width= 4,
            stroke_color = "#8fce00",
            update_streamlit=True,
            key="rectangles",
        )

        # Create a row with 3 columns
        col1, col2, col3 = st.columns([1,2,1])

        # Button to move to the previous file
        with col2:
            # Use columns inside the middle column for "Previous File" button
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.session_state['current_file_index'] > 0:
                    if st.button('Previous File'):
                        # Save modifications and decrement the file index
                        canvas_json = json.dumps(canvas_result.json_data)
                        canvas_json = json.loads(canvas_json)
                        modify_mask(current_file, blocks_json, canvas_json)
                        st.session_state['current_file_index'] -= 1
                        st.rerun()

        # Button to move to the next file or finish modification
        with col3:
            if st.session_state['current_file_index'] + 1 < len(uploaded_files):
                if st.button('Next File'):
                    # Save modifications and increment the file index
                    canvas_json = json.dumps(canvas_result.json_data)
                    canvas_json = json.loads(canvas_json)
                    modify_mask(current_file, blocks_json, canvas_json)
                    st.session_state['current_file_index'] += 1
                    st.rerun()

            else:
                if st.button('Finish'):
                    # Save modifications and finalize the modification process
                    canvas_json = json.dumps(canvas_result.json_data)
                    canvas_json = json.loads(canvas_json)
                    modify_mask(current_file, blocks_json, canvas_json)

                    # Create a containers for progress updates
                    progress_container = st.empty()
                    progress_container.write("Text block detection in progress...")
                    progress_bar = st.progress(0)

                    # Count the total number of uploaded files
                    total_files = len(uploaded_files)

                    # Detect text blocks in each segmented text with the modified mask
                    st.session_state['blocks'] = []

                    # Detect text blocks in each segmented text
                    for i, uploaded_file in enumerate(uploaded_files):
                        st.session_state['blocks'].append(block_detection(
                            file=uploaded_file, 
                            dilation_iterations=0
                        ))

                        update_progress(total_files, progress_bar, i)
                        torch.cuda.empty_cache()

                    # Update the progress
                    progress_bar.progress(100)
                    progress_bar.empty() # Hide the progress bar

                    # Update session state
                    st.session_state['current_file_index'] = 0
                    st.session_state['modify'] = True
                    st.session_state['process files'] = False
                    st.rerun()

# Handle case where modification is not enabled but files are processed                    
elif not Modify and st.session_state['process files']:
    st.session_state['modify'] = True
    st.session_state['process files'] = False

# Check if modification has been completed
if st.session_state['modify']:
    # Create a container to display progress updates
    progress_container = st.empty()
    progress_container.write("Text recognition in progress...")
    progress_bar = st.progress(0)

    # Count the total number of uploaded files
    total_files = len(uploaded_files)

    # Iterate over uploaded files to perform OCR
    for i, uploaded_file in enumerate(uploaded_files):
        st.session_state['texts'].append(ocr(
            uploaded_file,
            st.session_state['blocks'][i],  # Use the corresponding block for the current file
            ocr_model
        ))
        # Calculate the percentage completion
        percent_complete = int(100 * (i + 1) / len(uploaded_files))
        
        # Update the progress bar with the current percentage
        progress_bar.progress(percent_complete)
    
    torch.cuda.empty_cache()

    # Update the progress
    progress_bar.progress(100)
    progress_bar.empty()
    progress_container.write("Text translation in progress...")
    progress_bar = st.progress(0)

    # Initialize the translator with DeepL API key
    translator = deepl.Translator(deepl_key)

    # Translate the recognized texts for each uploaded file
    for i, uploaded_file in enumerate(uploaded_files):
        st.session_state['text_translated'].append(translate_texts(
            text=st.session_state['texts'][i],
            target_language=languages[target_language],
            translator=translator
        ))

        update_progress(total_files, progress_bar, i)

    # Update the progress
    progress_bar.progress(100)
    progress_bar.empty()
    progress_container.write("Image inpainting in progress...")

    # Display the usage of the DeepL API
    st.write(translator.get_usage())

    # Perform image inpainting on the detected text blocks
    inpainting()


    progress_container.write("Image inpainting in progress...")
    progress_bar = st.progress(0)

    # Update the progress
    progress_container.write("Text injection in progress...")

    # Begin text injection into the inpainted images
    for i, uploaded_file in enumerate(uploaded_files):
        text_injection(
            uploaded_file,
            texts=st.session_state['text_translated'][i],
            blocks=st.session_state['blocks'][i],
            font=fonts[font_style],
            fontSize=fontSize
        )
        # Calculate the percentage completion
        update_progress(total_files, progress_bar, i)
        
    # Update the progress
    progress_bar.progress(100)
    progress_bar.empty()
    progress_container.empty()

    # Record the end time of the process
    end_time = time.time() 
    elapsed_time = end_time - st.session_state['start_time']  
    st.write(f"Elapsed Time: {elapsed_time} seconds")   

    # Update session state
    st.session_state['modify'] = False
    st.session_state['init'] = True
    st.session_state['download'] = True

# Download button after the process is completed
if st.session_state['download']:
    # Retrieve the current working directory
    current_directory = os.getcwd()

    # Create a zip archive of the translated files
    shutil.make_archive('translated', 'zip', f'{current_directory}/prediction/translated')

    # Open and make download button of zip file
    with open('translated.zip', 'rb') as f:
        st.download_button("Download as zip", f, file_name='translated.zip')
    
    # Clean up workspace
    shutil.rmtree(f'{current_directory}/prediction')
    os.remove('translated.zip')
    shutil.rmtree(f'{current_directory}/outputs')

    # Reset various lists and flags in the session state to their initial values
    st.session_state['blocks'] = []
    st.session_state['texts'] = []
    st.session_state['text_translated'] = []
    st.session_state['init'] = True
    st.session_state['download'] = False


