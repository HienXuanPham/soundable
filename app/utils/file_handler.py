import tempfile


class FileHandler:
    def __init__(self):
        self.temp_file_path = None

    def upload_file(self, file):
        with tempfile.NamedTemporaryFile(suffix=file.filename, delete=False) as tmp:
            file.save(tmp.name)
            self.temp_file_path = tmp.name
