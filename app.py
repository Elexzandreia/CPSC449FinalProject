from flask import Flask, request, jsonify
from flask_caching import Cache
from models import db, User, Task, Tag, Priority, TaskTag
import config

app = Flask(__name__)
app.config.from_object(config)
cache = Cache(app)

# Initialize the database
db.init_app(app)

# Route for creating a task, invalidate cache when creating a new task
@app.route('/createTask', methods=['POST'])
def create_task():
    data = request.json

    # Validate priority_id
    priority = Priority.query.get(data.get('priority_id'))
    if not priority:
        return jsonify({"error": "Invalid priority_id"}), 400

    # Create the task
    new_task = Task(
        title=data['title'],
        description=data.get('description'),
        priority_id=data.get('priority_id')
    )
    db.session.add(new_task)

    # Handle tags
    tag_names = data.get('tags', [])
    for tag_name in tag_names:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)  # Create new tag if it doesn't exist
            db.session.add(tag)
        new_task.tags.append(tag)  # Associate tag with the task

    # Commit changes
    db.session.commit()
    cache.clear()  # Clear cache to keep data consistent

    return jsonify(["Task successfully created"]), 201

# Route for getting all tasks, cache tasks list for faster access
@app.route('/getTasks', methods=['GET'])
@cache.cached(timeout=60)  # Cache this route for 60 seconds
def get_tasks():
    tasks = Task.query.all()
    return jsonify([{
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority.name if task.priority else None,
        "tags": [tag.name for tag in task.tags]
    } for task in tasks])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures all tables are created
    app.run(debug=True)
