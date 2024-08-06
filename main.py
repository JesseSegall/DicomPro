import os
import pydicom
import zlib
from pydicom.encaps import encapsulate, defragment_data
from pydicom.pixel_data_handlers.util import convert_color_space


# reads the file
def process_dicom(input_file, output_file):
    ds = pydicom.dcmread(input_file)

    if ds.file_meta.TransferSyntaxUID.is_compressed:
        decompress_dicom(ds, output_file)
    else:
        compress_dicom(ds, output_file)


# pixel check
def compress_dicom(ds, output_file):
    if not hasattr(ds, 'PixelData'):
        print("This DICOM file does not contain pixel data.")
        return

    compressed_data = zlib.compress(ds.PixelData)

    encapsulated_data = encapsulate([compressed_data])

    ds.PixelData = encapsulated_data
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    # Adding our private tag
    ds.add_new([0x0011, 0x0011], 'LO', 'CUSTOM_ZLIB_COMPRESSED')

    ds.save_as(output_file, write_like_original=False)

    print(f"Compressed DICOM saved as {output_file}")


def decompress_dicom(ds, output_file):
    if not hasattr(ds, 'PixelData'):
        print("This DICOM file does not contain pixel data.")
        return

    # Decompress the pixel data
    try:
        if ds.get([0x0011, 0x0011]) is not None and ds[0x0011, 0x0011].value == 'CUSTOM_ZLIB_COMPRESSED':

            fragments = defragment_data(ds.PixelData)
            decompressed_data = zlib.decompress(fragments[0])
        else:

            decompressed_data = ds.pixel_array.tobytes()
    except Exception as e:
        print(f"Failed to decompress: {str(e)}")
        return

    # Update the dataset
    ds.PixelData = decompressed_data
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    # Remove compression-related attributes if present
    for attr in ['NumberOfFrames', 'PlanarConfiguration']:
        if attr in ds:
            delattr(ds, attr)

    # Remove our custom compression tag if it exists
    if ds.get([0x0011, 0x0011]) is not None:
        del ds[0x0011, 0x0011]

    # Handle color space conversion if necessary
    if 'PhotometricInterpretation' in ds:
        if ds.PhotometricInterpretation == 'YBR_FULL_422':
            ds.PhotometricInterpretation = 'RGB'
            ds.PixelData = convert_color_space(ds.pixel_array, 'YBR_FULL_422', 'RGB').tobytes()

    # Save the decompressed DICOM
    ds.save_as(output_file, write_like_original=False)

    print(f"Decompressed DICOM saved as {output_file}")


def process_folder(input_folder, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith('.dcm'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)  # Keep the same filename

            if os.path.exists(output_path):
                print(f"Warning: {filename} already exists in the output folder. Skipping.")
                continue

            try:
                process_dicom(input_path, output_path)
                print(f"Processed {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")


# Add paths for where the Dicoms are and where they will go.
input_folder = 'C:\\Users\\jsega\\Desktop\\SER00001'
output_folder = 'C:\\Users\\jsega\\Desktop\\Dicom_Processed'

process_folder(input_folder, output_folder)
