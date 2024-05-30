# SOUNDABLE
- This is the backend for the application that converts PDF file to MP3 file.
- Everyone has different style of learning. In my case, I learn faster by listening than reading the materials. This motivates me to create the application help me convert PDF file to audio file.

## Technologies
- I chose Flask to build this app because it's lightweight and makes it easy to build a web application by using its libraries.
- I used PostgreSQL for the database because it’s scalable and flexable. PostgreSQL is a relational database management system that allows us to create tables, insert data, retrieve data, and delete data. It integrates well with Flask through libraries like SQLAlchemy and Psycopg2, making it easier to manage database operations within the application.

## Features
### 1. User Authentication and Management

- **User Signup**: Users can create a new account by providing their name, email, password, and confirming their password. A verification email is sent to the user upon successful signup.
- **User Login**: Users can log in with their email and password. Authentication is managed using the `flask_login` library.
- **Email Verification**: Users receive an email verification link upon signup, which they must use to verify their account.
- **Password Management**:
  - **Forgot Password**: Users can request a password reset link if they forget their password.
  - **Change Password**: Users can change their password using a link sent to their email.
- **User Logout**: Authenticated users can log out of their account.

### 2. PDF to Audio Conversion

- **Convert PDF to Audio**: Authenticated users can upload a PDF file, which will be converted to an audio file using text-to-speech technology. The resulting audio file is made available for download.

## How to Install and Run the Program Locally
### 1. Fork and Clone this repo
### 2. Set Up a Visual Environment
**MacOs**
``` 
python3 -m venv venv
source venv/bin/activate
```
**Windows**
```
python -m venv venv
venv\Scripts\activate
```
### 3. Install Dependencies
```
pip install -r requirements.txt
```
### 4. Setup Postgres
**MacOs**
- Install Postgres
  - `brew install postgresql`
  - `brew services start postgresql`
- Create the Postgres user
  - `createuser -s postgres`
  - The most common default username and password for Postgres is
    - username: postgres
    - password: postgres

**Windows**
- Download PostgreSQL at https://www.postgresql.org/download/ 
- The most common default username and password for Postgres are `postgres`
- After the PostgreSQL install is finished, you do not need to run StackBuilder for additional plugins.

##### Create a Database in Postgres:
- Enter Postgres terminal: `psql -U postgres`
- If you encounter an issue where psql command is not recognized in your environment, you need to add a path to the system’s PATH environment variable.
- To create a database, enter this command in the terminal: `CREATE DATABASE db_name;`
- Use `\l` to list all the databases
- Switch to another database, use `\c database_name`
- Exit Postgres database, use `\q`

### 5. Setup a `.env` File in a Flask Application
A `.env` file in an application is used to store environment variables in a simple, readable format. These variables can include configuration settings such as database credentials, API keys, and other sensitive information that should not be hard-coded into the source code.

- Create a `.env` file in the root directory of your Flask app
- Add environment variables
```
FLASK_ENV="development"

SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://postgres:postgres@localhost:5432/dbname_development"

SQLALCHEMY_TEST_DATABASE_URI="postgresql+psycopg2://postgres:postgres@localhost:5432/dbname_testing"

MAIL_USERNAME="your email"

MAIL_PASSWORD="your email password"

SECRET_KEY="choose your secret key"
```

I chose Gmail to send emails to the users. You can use a different email provider. If you use Gmail, here is how to set up app password for your email: https://support.google.com/mail/answer/185833?hl=en

### 6. Run the Program and Use Postman to Test
```
flask run
```
or
```
flask run --debug
```
##### Test `signup` route


https://github.com/HienXuanPham/soundable/assets/44250274/4b3e0be0-8fb9-4132-978d-dd2d82ffffb0


##### Test `login` and `logout` route


https://github.com/HienXuanPham/soundable/assets/44250274/befee270-6b60-4264-b87c-4f25435bd44a


##### Test `forgot-password` route


https://github.com/HienXuanPham/soundable/assets/44250274/8816feb8-e2c7-44d6-97b7-8a9eb64c0d72


##### Test `convert-pdf-to-audio` route
For this endpoint, I wrote a test case for it. You can check it out in `test_convert_pdf_to_audio.py` file


https://github.com/HienXuanPham/soundable/assets/44250274/3901025b-2204-45ce-a1f3-ab21429857fd







