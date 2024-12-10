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

## Detailed API Endpoints:
Here are detailed descriptions of each API endpoint in the `app.py` file:
1. **Index Route**:
   - **Endpoint**: `/`
   - **Method**: `GET`
   - **Description**: Serves the `index.html` file, which is the main entry point for the web application.

2. **User Registration**:
   - **Endpoint**: `/register`
   - **Method**: `POST`
   - **Description**: Registers a new user by accepting a JSON payload with `username` and `password`. It hashes the password and stores the user in the database. Returns a success message or an error if the username is already taken or the input is invalid.

3. **User Login**:
   - **Endpoint**: `/login`
   - **Method**: `POST`
   - **Description**: Authenticates a user by accepting a JSON payload with `username` and `password`. It checks the credentials and returns a JWT access token if successful. Returns an error message if the credentials are invalid.

4. **Create Task**:
   - **Endpoint**: `/tasks`
   - **Method**: `POST`
   - **Description**: Creates a new task for the authenticated user. Accepts a JSON payload with `title`, `description`, `priority_id`, and `tags`. Validates the input and creates the task, associating it with the user and any specified tags. Returns a success message or an error if the input is invalid.

5. **Get All Tasks**:
   - **Endpoint**: `/tasks`
   - **Method**: `GET`
   - **Description**: Retrieves all tasks for the authenticated user. The response is cached for 60 seconds to improve performance. Returns a list of tasks with their details.

6. **Get Tasks by User**:
   - **Endpoint**: `/tasks/user`
   - **Method**: `POST`
   - **Description**: Retrieves tasks for a specific user or the authenticated user. Accepts a JSON payload with an optional `username` and `timestamp`. If `username` is provided, it fetches tasks for that user; otherwise, it fetches tasks for the authenticated user. The response is cached for 60 seconds unless a `timestamp` is provided. Returns a list of tasks with their details.

7. **Update Task**:
   - **Endpoint**: `/tasks/update`
   - **Method**: `PUT`
   - **Description**: Updates an existing task for the authenticated user. Accepts a JSON payload with the updated task details. Validates the input and updates the task in the database. Returns a success message or an error if the input is invalid or the task is not found.

8. **Delete Task**:
   - **Endpoint**: `/tasks/delete`
   - **Method**: `DELETE`
   - **Description**: Deletes an existing task for the authenticated user. Accepts a JSON payload containing the task ID to be deleted. Validates the input and removes the task from the database. Returns a success message upon successful deletion or an error if the input is invalid, the task is not found, or the user does not have permission to delete the task.

9. **Export Tasks**:
   - **Endpoint**: `/api/export/tasks`
   - **Method**: `GET`
   - **Description**: Exports tasks to a JSON-format payload for the authenticated user. Returns that JSON or an error if the export fails.

9. **Analyze Tasks**:
   - **Endpoint**: `/api/analyze/tasks`
   - **Method**: `POST`
   - **Description**: Analyzes tasks using an AI model. Accepts a JSON payload with the tasks to be analyzed. Returns the AI-generated analysis or an error if the analysis fails.

10. **Retrieve Completed Tasks**:
   - **Endpoint**: `/tasks/completed`
   - **Method**: `POST`
   - **Description**: Retrieves all completed tasks for a specific user or the authenticated user. Accepts a JSON payload with an optional username and timestamp. If username is provided, it fetches completed tasks for that user; otherwise, it fetches completed tasks for the authenticated user. Returns a list of completed tasks with their details.

11. **Retrieve Incomplete Tasks**:
   - **Endpoint**: `/tasks/incomplete`
   - **Method**: `POST`
   - **Description**: Retrieves all incomplete tasks for a specific user or the authenticated user. Accepts a JSON payload with an optional username and timestamp. If username is provided, it fetches incomplete tasks for that user; otherwise, it fetches incomplete tasks for the authenticated user. Returns a list of incomplete tasks with their details.




