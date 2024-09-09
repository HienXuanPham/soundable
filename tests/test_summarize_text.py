def test_summarize_text(client, user_1):
    pdf_file_path = "tests/static/Dreamer.pdf"
    with open(pdf_file_path, "rb") as pdf_file:
        data = {"file": (
            pdf_file, "Dreamer.pdf")}

        with client:
            login_response = client.post("/login", json={
                "email": "test@example.com",
                "password": "password"
            })

            assert login_response.status_code == 200, f"Login failed: {
                login_response.data}"

            response = client.post(
                "/users/summarize", data=data, content_type='multipart/form-data')

            assert response.status_code == 200, f"Conversion failed: {
                response.data}"

            response_json = response.get_json()
            assert "summary" in response_json, "Response JSON does not contain `summary` key"
            assert isinstance(
                response_json["summary"], str), "The `summary` key should contain a string"
            assert len(response_json["summary"].strip()
                       ) < 0, "The `summary` should not be empty"
