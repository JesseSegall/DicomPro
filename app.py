from flask import Flask, request, jsonify, send_file
import os
import tempfile
from io import BytesIO
import zipfile
from werkzeug.utils import secure_filename
from flask_cors import CORS


from dicom_processor import process_dicom

app = Flask(__name__)
#TODO
#DELETE FOR PRODUCTION. TESTING ONLY
CORS(app, resources={r"/*": {"origins": "*"}})
#CORS(app)

ALLOWED_EXTENSIONS = {'dcm'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    if len(files) == 0:
        return jsonify({'error': "No files selected"}), 400

    operation = request.form.get('operation', 'compress')
    if operation not in ['compress', 'decompress']:
        return jsonify({'error': "Invalid operation"}), 400

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_files = []

            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    input_path = os.path.join(temp_dir, filename)
                    output_path = os.path.join(temp_dir, f"processed_{filename}")
                    file.save(input_path)
                    print(f"Processing file: {input_path}")
                    process_dicom(input_path, output_path, operation)
                    processed_files.append(output_path)

            if not processed_files:
                return jsonify({'error': "No valid DICOM files were processed"}), 400

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in processed_files:
                    zipf.write(file_path, os.path.basename(file_path))
            zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'DICOM_PRO_{operation}ed_files.zip'
        )
    except Exception as e:
        print(f"Error in upload_files: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
