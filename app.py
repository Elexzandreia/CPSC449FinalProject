from flask import Flask, request, jsonify, render_template
from flask_caching import Cache
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Task, Tag, Priority, TaskTag
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
import config

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)
app.config.from_object(config)
cache = Cache(app)

# Initialize the database
db.init_app(app)
jwt = JWTManager(app)

@app.route('/')
def index():
    return render_template('index.html')

# Route for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already taken"}), 400

    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        password_hash=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201


@app.route('/login', methods=['POST'])
def login():
    print("Login endpoint was hit")
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    try:
        access_token = create_access_token(identity=str(user.id))  # Ensure identity is a string
    except Exception as e:
        return jsonify({"error": f"Token creation error: {str(e)}"}), 500

    return jsonify({"access_token": access_token}), 200


# Route for creating a task (JWT protected)
@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    data = request.json

    # Validate title and priority_id
    if not data or not isinstance(data.get('title'), str):
        return jsonify({"error": "Title must be a string"}), 400
    if not isinstance(data.get('priority_id'), int):
        return jsonify({"error": "Priority ID must be an integer"}), 400

    current_user_id = get_jwt_identity()

    # Validate priority_id
    priority = Priority.query.get(data.get('priority_id'))
    if not priority:
        priorities = [p.name for p in Priority.query.all()]
        return jsonify({"error": "Invalid priority_id", "available_priorities": priorities}), 400

    # Create the task
    new_task = Task(
        title=data['title'],
        description=data.get('description'),
        priority_id=data.get('priority_id'),
        user_id=current_user_id
    )
    db.session.add(new_task)

    # Handle tags
    tag_names = data.get('tags', [])
    if not isinstance(tag_names, list) or not all(isinstance(tag, str) for tag in tag_names):
        return jsonify({"error": "Tags must be a list of strings"}), 400

    for tag_name in tag_names:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        new_task.tags.append(tag)

    db.session.commit()
    cache.clear()  # Clear cache to keep data consistent
    return jsonify({"message": "Task successfully created"}), 201


# Route for getting all tasks (JWT protected), cache tasks list for faster access
@app.route('/tasks', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60) # Cache this route for 60 seconds
def get_tasks():
    tasks = Task.query.all()
    return jsonify([{
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority.name if task.priority else None,
        "tags": [tag.name for tag in task.tags]
    } for task in tasks])


# Route for getting all tasks (JWT protected) from a particular user, cache tasks list for faster access
@app.route('/tasks/user', methods=['POST'])
@jwt_required()
def get_tasks_by_user():
    data = request.json
    current_user_id = get_jwt_identity()  # Get the logged-in user's ID

    # Validate request body
    username = data.get('username')  # Get the username from the request body
    if username and not isinstance(username, str):
        return jsonify({"error": "Username must be a string"}), 400

    # Determine the user whose tasks to fetch
    if username:
        cache_key = f"user_tasks_{username}"
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
    else:
        cache_key = f"user_tasks_{current_user_id}"
        user = User.query.get(current_user_id)

    # Check if tasks are cached
    cached_tasks = cache.get(cache_key)
    if cached_tasks:
        return jsonify({"task_count": len(cached_tasks), "tasks": cached_tasks}), 200

    # Fetch tasks from the database
    tasks = Task.query.filter_by(user_id=user.id).all()
    task_list = [{
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority.name if task.priority else None,
        "tags": [tag.name for tag in task.tags],
        "created_by": user.username
    } for task in tasks]

    # Cache the tasks
    cache.set(cache_key, task_list, timeout=60)  # Cache for 60 seconds
    return jsonify({"task_count": len(task_list), "tasks": task_list}), 200

@app.route('/api/export/tasks', methods=['GET'])
@jwt_required()
def export_tasks():
    try:
        print('/api/export/tasks RUNNING')

        current_user_id = get_jwt_identity()
        
        # Get all tasks for the current user
        tasks = Task.query.filter_by(user_id=current_user_id).all()
        
        # Format timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create optimized JSON structure
        export_data = {
            "metadata": {
                "export_timestamp": timestamp,
                "user_id": current_user_id,
                "total_tasks": len(tasks)
            },
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description or "",  # Handle None values
                    "p": task.priority.name if task.priority else "NONE",  # Shortened key for priority
                    "t": [tag.name for tag in task.tags]  # Shortened key for tags
                }
                for task in tasks
            ]
        }
        
        # Create filename with timestamp
        filename = f"tasks_export_{timestamp}.json"
        
        # Set response headers for file download
        response = jsonify(export_data)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = 'application/json'
        
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/tasks/analyze', methods=['POST'])
@jwt_required()
def analyze_tasks():
    try:
        # Get and verify user identity
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({"error": "Invalid user token"}), 401
            
        # Get and verify request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_prompt = data.get('prompt')
        if not user_prompt:
            return jsonify({"error": "Prompt is required"}), 400
            
        # Get tasks for the current user
        tasks = Task.query.filter_by(user_id=current_user_id).all()
        if not tasks:
            return jsonify({"response": "You don't have any tasks yet. Create some tasks first!"}), 200
        
        # Format tasks data
        tasks_data = {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description or "",
                    "priority": task.priority.name if task.priority else "NONE",
                    "tags": [tag.name for tag in task.tags]
                }
                for task in tasks
            ]
        }
        
        context = f"""
        You are a task management assistant. You have access to the user's tasks in the following format:
        {json.dumps(tasks_data, indent=2)}
        
        Please analyze these tasks and respond to the user's question. Focus on providing clear, concise answers.
        Be specific and reference actual task titles when relevant.
        
        User's question: {user_prompt}
        """
        
        try:
            # Configure safety settings
            # safety_settings = {
            #     HarmCategory.HARASSMENT: HarmBlockThreshold.MEDIUM_AND_ABOVE,
            #     HarmCategory.HATE_SPEECH: HarmBlockThreshold.MEDIUM_AND_ABOVE,
            #     HarmCategory.SEXUALLY_EXPLICIT: HarmBlockThreshold.MEDIUM_AND_ABOVE,
            #     HarmCategory.DANGEROUS_CONTENT: HarmBlockThreshold.MEDIUM_AND_ABOVE,
            # }
            
            # Generate response
            # response = model.generate_content(
            #     context,
            #     safety_settings=safety_settings,
            #     generation_config={"temperature": 0.7}
            # )

            response = model.generate_content(context)
            
            return jsonify({"response": response.text})
            
        except Exception as gemini_error:
            app.logger.error(f"Gemini API error: {str(gemini_error)}")
            return jsonify({"error": "Error generating AI response. Please try again."}), 500
            
    except Exception as e:
        app.logger.error(f"General error in analyze_tasks: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Route for editing/updating a task (JWT protected)
@app.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    try:
        # Get the current logged-in user's ID
        current_user_id = get_jwt_identity()

        # Get the task by its ID
        task = Task.query.get(task_id)

        if not task:
            return jsonify({"error": "Task not found"}), 404

        # Check if the logged-in user is the owner of the task
        if task.user_id != int(current_user_id):
            return jsonify({"error": "You do not have permission to update this task"}), 403

        # Update the task details
        data = request.json
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.priority_id = data.get('priority_id', task.priority_id)

        # Update tags (optional)
        tag_names = data.get('tags', [])
        if not isinstance(tag_names, list) or not all(isinstance(tag, str) for tag in tag_names):
            return jsonify({"error": "Tags must be a list of strings"}), 400

        task.tags = []  # Clear the existing tags
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            task.tags.append(tag)

        # Commit the changes
        db.session.commit()
        return jsonify({"message": "Task updated successfully"}), 200

    except Exception as e:
        # Log the exception and return a 500 error
        app.logger.error(f"Error occurred while updating the task: {str(e)}")
        return jsonify({"error": "An error occurred while updating the task. Please try again."}), 500

# Route for deleting a task (JWT protected)
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    try:
        current_user_id = get_jwt_identity()  # Get the logged-in user's ID

        # Find the task to be deleted
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        # DEBUG: Log the current user ID and task's user ID
        app.logger.info(f"Current user ID: {current_user_id}, Task owner ID: {task.user_id}")


        # Check if the logged-in user owns the task
        if task.user_id != int(current_user_id):
            return jsonify({"error": "You do not have permission to delete this task"}), 403

        # Delete the task
        db.session.delete(task)
        db.session.commit()
        
        cache.clear()  # Clear cache to keep data consistent
        
        return jsonify({"message": "Task deleted successfully"}), 200

    except Exception as e:
        app.logger.error(f"Error deleting task: {str(e)}")
        return jsonify({"error": "An error occurred while trying to delete the task"}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures all tables are created
    app.run(debug=True)