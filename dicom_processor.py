import os
import pydicom
import zlib
from pydicom.encaps import encapsulate, defragment_data
from pydicom.pixel_data_handlers.util import convert_color_space
from pydicom.uid import ExplicitVRLittleEndian

def process_dicom(input_file, output_file, operation):
    ds = pydicom.dcmread(input_file)

    if operation == 'compress':
        compress_dicom(ds, output_file)
    elif operation == 'decompress':
        decompress_dicom(ds, output_file)
    else:
        raise ValueError("Invalid operation. Choose 'compress' or 'decompress'.")

def compress_dicom(ds, output_file):
    if not hasattr(ds, 'PixelData'):
        print("This DICOM file does not contain pixel data.")
        return

    compressed_data = zlib.compress(ds.PixelData)
    encapsulated_data = encapsulate([compressed_data])

    ds.PixelData = encapsulated_data
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds.add_new([0x0011, 0x0011], 'LO', 'CUSTOM_ZLIB_COMPRESSED')

    ds.save_as(output_file, write_like_original=False)

    print(f"Compressed DICOM saved as {output_file}")

def decompress_dicom(ds, output_file):
    if not hasattr(ds, 'PixelData'):
        print("This DICOM file does not contain pixel data.")
        return

    try:
        if ds.get([0x0011, 0x0011]) is not None and ds[0x0011, 0x0011].value == 'CUSTOM_ZLIB_COMPRESSED':
            fragments = defragment_data(ds.PixelData)
            decompressed_data = zlib.decompress(fragments[0])
        else:
            if ds.file_meta.TransferSyntaxUID.is_compressed:
                ds.decompress()

            if hasattr(ds, 'pixel_array'):
                decompressed_data = ds.pixel_array.tobytes()
            else:
                decompressed_data = ds.PixelData
    except Exception as e:
        print(f"Failed to decompress: {str(e)}")
        return

    if isinstance(decompressed_data, int):
        print("Warning: PixelData is an integer. This might indicate an issue with the DICOM file.")
        decompressed_data = decompressed_data.to_bytes((decompressed_data.bit_length() + 7) // 8, byteorder='little')

    ds.PixelData = decompressed_data
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    for attr in ['NumberOfFrames', 'PlanarConfiguration']:
        if attr in ds:
            delattr(ds, attr)

    if ds.get([0x0011, 0x0011]) is not None:
        del ds[0x0011, 0x0011]

    if 'PhotometricInterpretation' in ds:
        if ds.PhotometricInterpretation == 'YBR_FULL_422':
            ds.PhotometricInterpretation = 'RGB'
            ds.PixelData = convert_color_space(ds.pixel_array, 'YBR_FULL_422', 'RGB').tobytes()

    ds.save_as(output_file, write_like_original=False)

    print(f"Decompressed DICOM saved as {output_file}")