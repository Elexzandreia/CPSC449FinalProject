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
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 0  # Disable default caching

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
    
    # Get timestamp from request to handle cache busting
    request_timestamp = data.get('timestamp')
    if request_timestamp:
        cache_key = f"{cache_key}_{request_timestamp}"
    
    # Check if tasks are cached
    cached_tasks = cache.get(cache_key)
    if cached_tasks and not request_timestamp:  # Only use cache if no timestamp provided
        return jsonify({"task_count": len(cached_tasks), "tasks": cached_tasks}), 200
        
    # Fetch tasks from the database
    tasks = Task.query.filter_by(user_id=user.id).all()
    task_list = [{
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority.name if task.priority else None,
        "tags": [tag.name for tag in task.tags],
        "created_by": user.username,
        "is_completed": task.is_completed
} for task in tasks]
    
    # Only cache if no timestamp was provided (not a force refresh)
    if not request_timestamp:
        cache.set(cache_key, task_list, timeout=60)  # Cache for 60 seconds
        
    return jsonify({"task_count": len(task_list), "tasks": task_list}), 200

@app.route('/api/export/tasks', methods=['GET'])
@jwt_required()
def export_tasks():
    try:
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
                    "t": [tag.name for tag in task.tags],  # Shortened key for tags
                    "i": task.is_completed
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
                    "tags": [tag.name for tag in task.tags],
                    "is_completed": task.is_completed
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
        current_user_id = get_jwt_identity()
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        if task.user_id != int(current_user_id):
            return jsonify({"error": "You do not have permission to update this task"}), 403
            
        data = request.json
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.priority_id = data.get('priority_id', task.priority_id)
        
        tag_names = data.get('tags', [])
        if not isinstance(tag_names, list) or not all(isinstance(tag, str) for tag in tag_names):
            return jsonify({"error": "Tags must be a list of strings"}), 400
            
        task.tags = []
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            task.tags.append(tag)
            
        db.session.commit()
        cache.delete_memoized(get_tasks_by_user)  # Clear the specific user's cache
        cache.delete_memoized(get_tasks)          # Clear the general tasks cache
        return jsonify({"message": "Task updated successfully"}), 200
    except Exception as e:
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

@app.route('/tasks/<int:task_id>/toggle-completion', methods=['PATCH'])
@jwt_required()
def toggle_task_completion(task_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.json
        is_completed = data.get('is_completed', False)
        manage_tag = data.get('manage_tag', True)  # Default to True for tag management
        
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
        if task.user_id != int(current_user_id):
            return jsonify({"error": "You do not have permission to modify this task"}), 403
            
        # Update completion status
        task.is_completed = is_completed
        
        if manage_tag:
            completed_tag = Tag.query.filter_by(name='Completed').first()
            if not completed_tag:
                completed_tag = Tag(name='Completed')
                db.session.add(completed_tag)
            
            if is_completed:
                # Add 'Completed' tag if not present
                if completed_tag not in task.tags:
                    task.tags.append(completed_tag)
            else:
                # Remove 'Completed' tag if present
                if completed_tag in task.tags:
                    task.tags.remove(completed_tag)
        
        db.session.commit()
        cache.delete_memoized(get_tasks_by_user)
        
        return jsonify({
            "message": "Task status updated successfully",
            "task_id": task.id,
            "is_completed": task.is_completed,
            "tags": [tag.name for tag in task.tags]
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error toggling task completion: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "An error occurred while updating the task"}), 500


@app.route('/tasks/completion-status', methods=['GET'])
@jwt_required()
def get_tasks_completion_status():
    try:
        current_user_id = get_jwt_identity()
        
        # Get all tasks for the current user
        tasks = Task.query.filter_by(user_id=current_user_id).all()
        
        # Create status summary
        status_summary = {
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t.is_completed]),
            "incomplete_tasks": len([t for t in tasks if not t.is_completed]),
            "tasks": [{
                "id": task.id,
                "title": task.title,
                "is_completed": task.is_completed
            } for task in tasks]
        }
        
        return jsonify(status_summary), 200
        
    except Exception as e:
        app.logger.error(f"Error getting completion status: {str(e)}")
        return jsonify({"error": "An error occurred while fetching task status"}), 500

# Endpoint: Get all tasks with the tag "Done" along with the user information
@app.route('/tasks/complete', methods=['GET'])
def getCompletedTasks():
    # Query tasks with the "Done" tag and include the associated user
    tasks = (
        db.session.query(Task, User)
        .join(Task.tags)  # Join with the Tag model
        .join(User, Task.user_id == User.id)  # Join with the User model
        .filter(Tag.name == "Done")  # Filter for the "Done" tag
        .all()
    )

    # Format the result
    result = [
        {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "user_id": user.id,
            "username": user.username,
            "tags": [tag.name for tag in task.tags]
        }
        for task, user in tasks
    ]

    return jsonify(result), 200


# Endpoint: Get all tasks with the tag as not "Done" along with the user information
@app.route('/tasks/incomplete', methods=['GET'])
def getIncompletedTasks():
    # Query tasks with the "Done" tag and include the associated user
    tasks = (
        db.session.query(Task, User)
        .join(Task.tags)  # Join with the Tag model
        .join(User, Task.user_id == User.id)  # Join with the User model
        .filter(~Task.tags.any(Tag.name == "Done"))  # Exclude tasks with the "Done" tag
        .all(
)
    )

    # Format the result
    result = [
        {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "user_id": user.id,
            "username": user.username,
            "tags": [tag.name for tag in task.tags]
        }
        for task, user in tasks
    ]

    return jsonify(result), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures all tables are created
    app.run(debug=True)