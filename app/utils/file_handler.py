import tempfile
from flask import jsonify


class FileHandler:
    def __init__(self):
        self.temp_file_path = None

    def validate_file(self, file):
        if not file:
            return jsonify({"message": "No file part"}), 400

        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        return None

    def upload_file(self, file):
        with tempfile.NamedTemporaryFile(suffix=file.filename, delete=False) as tmp:
            file.save(tmp.name)
            self.temp_file_path = tmp.name
