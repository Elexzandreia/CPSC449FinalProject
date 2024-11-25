from flask import Flask, request, jsonify
from flask_caching import Cache
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Task, Tag, Priority, TaskTag
from werkzeug.security import generate_password_hash, check_password_hash
import config


app = Flask(__name__)
app.config.from_object(config)
cache = Cache(app)

# Initialize the database
db.init_app(app)
jwt = JWTManager(app)

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures all tables are created
    app.run(debug=True)
