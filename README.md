# CPSC449FinalProject

## Group Members
1. Parastoo Toosi CWID 890049349 
2. Elexzandreia Livermore CWID 888823101 
3. Benjamin Nguyen CWID 884523655
4. Chelsea Ogbedeagu CWID 885255463


## Create Container and Install Required Dependencies
1. Create virtual environment with the specific python version 3.10.15 in order to avoid version conflicts with dependencies.
    ```bash
    python3.10 -m venv myenv
    source myenv/bin/activate[in Linux and Mac]
    myenv\Scripts\activate [in Windows]
    
2. Install Dependencies
    ```bash
    pip install -r requirements.txt


## Create your config.py file
1. Create file named 'config.py'.

2. Paste the following in the file:
    ```bash
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/task_manager'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'super-secret'
    CACHE_TYPE = 'SimpleCache'  # Use in-memory caching
    CACHE_DEFAULT_TIMEOUT = 300

3. Change SQLALCHEMY_DATABASE_URI to accurately reflect your username and password for MySQL, and change JWT_SECRET_KEY to your JWT secure key.


## Create and Import MySQL Database
To set up the project's database, follow these steps:

1. Ensure you have MySQL installed and running on your system.

2. Open your terminal or command prompt.

3. Create the database:
   ```bash
   mysql -u root -p -e "CREATE DATABASE task_manager;"

4. Import the database schema and data
    ```bash
    mysql -u root -p task_manager < task_manager.sql

5. When prompted, enter your MySQL root password.

6. Install the packages mentioned in requirements.txt file
    ```bash
    pip install -r requirements.txt

7. Run the following command to list all installed packages and write them to requirements.txt
    ```bash
    pip freeze > requirements.txt

## Add your Gemini API Key
To make AI assistant works, you need to add Gemini API Key.

1. Open app.py in your editor.
2. Locate this line and change YOUR_GEMINI_API_KEY to the your actual Gemini API Key, which is created from [Google AI Studio](https://makersuite.google.com/app/apikey)
   ```bash
   genai.configure(api_key="YOUR_GEMINI_API_KEY")
Note: The default implementing Gemini model is 1.5 Flash. You can change to another Gemini models.

    model = genai.GenerativeModel('model-name')
    
For more information of Gemini models, check out on [this link](https://ai.google.dev/gemini-api/docs/models/gemini)


