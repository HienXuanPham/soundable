import tempfile
from flask import jsonify


class DocumentHandler:
    def __init__(self):
        self.temp_doc_path = None

    def validate_doc(self, doc):
        if not doc:
            return jsonify({"message": "No file part"}), 400

        if doc.filename == "":
            return jsonify({"message": "No selected file"}), 400

        if not doc.filename.endswith(".pdf"):
            return jsonify({"message": "Not a PDF file"}), 400

        return None

    def upload_document(self, doc):
        with tempfile.NamedTemporaryFile(suffix=doc.filename, delete=False) as tmp:
            doc.save(tmp.name)
            self.temp_doc_path = tmp.name
