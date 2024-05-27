def test_convert_pdf(client, user_1):
    pdf_file_path = "tests/static/scalability 1.pdf"
    with open(pdf_file_path, "rb") as pdf_file:
        data = {"file": (pdf_file, "scalability 1.pdf")}

        with client:
            login_response = client.post("/login", json={
                "email": "test@example.com",
                "password": "password"
            })

            assert login_response.status_code == 200, f"Login failed: {
                login_response.data}"

            response = client.post(
                "/users/convert-pdf-to-audio", data=data, content_type='multipart/form-data')

            assert response.status_code == 200, f"Conversion failed: {
                response.data}"
            assert "attachment" in response.headers.get(
                "Content-Disposition", ""), "MP3 file not sent"
