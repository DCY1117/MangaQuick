# MangaQuick: Automatic Manga Translator

## Description

MangaQuick is a Streamlit-powered web application, designed to facilitate the automatic translation of manga. This tool is part of my Final Degree Project [Diseño y desarrollo de un traductor de comics](https://oa.upm.es/71255/) (UPM, Spanish). It offers a streamlined solution for translating manga pages, with support for both single-page and batch processing. The application integrates [Manga Text Segmentation](https://github.com/juvian/Manga-Text-Segmentation) for text segmentation and detection and [LaMa](https://github.com/advimman/lama) for image inpainting.

## Installation

### Prerequisites

It's highly recommended to use a virtual environment for managing dependencies and isolating the project. `conda` is a great tool for this purpose:

Create a new conda environment named 'MangaQuick' with Python 3.11
```bash
conda create --name MangaQuick python=3.11
```

Activate the 'MangaQuick' environment
```bash
conda activate MangaQuick
```

### Step-by-Step Installation

1. Clone the MangaQuick repository:
    ```bash
    git clone https://github.com/yourusername/MangaQuick.git
    ```

2. Navigate to the MangaQuick directory:
    ```bash
    cd MangaQuick
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
### GPU Support
To utilize GPU, ensure you install the correct version of PyTorch that matches your system and CUDA setup.
You can find the appropriate installation commands on:

[https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)

This will set up MangaQuick on your system, ready for use with or without GPU support, depending on your setup.

## Usage

To start using MangaQuick, follow these steps:

1. Launch the application:
    ```bash
    python mangaquick.py
    ```

2. Follow the on-screen instructions to upload your manga file.

3. Select the target language for the translation.

4. MangaQuick will process and display the translated manga upon completion.

## License

MangaQuick is made available under the [MIT License](LICENSE). For more details, see the LICENSE file in the repository.

## Acknowledgments
- Manga Text Segmenation: [https://github.com/juvian/Manga-Text-Segmentation](https://github.com/juvian/Manga-Text-Segmentation)
- Manga inpainting: [https://github.com/advimman/lama](https://github.com/advimman/lama)

