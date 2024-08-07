# DicomPro

DicomPro is a Python-based tool for processing DICOM (Digital Imaging and Communications in Medicine) files. It provides functionality to convert DICOM images to JPEG format and perform various operations on DICOM data.

## Installation

1. Ensure you have Python installed on your system.

2. Clone this repository:

3. Install the required packages:

pip install pydicom

pip install numpy

pip install pillow

pip install pylibjpeg pylibjpeg-openjpeg 
## Configuration

Before running the program, make sure to update the following variables in the main script:

- `input_folder`: Set this to the path of the directory containing your DICOM files.
- `output_folder`: Set this to the path where you want the processed files to be saved.

Example:
```python
input_folder = "C:/Users/YourUsername/DicomFiles"
output_folder = "C:/Users/YourUsername/ProcessedFiles"
