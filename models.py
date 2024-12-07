from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tasks = db.relationship('Task', back_populates='user')

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    priority_id = db.Column(db.Integer, db.ForeignKey('priorities.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to User
    is_completed = db.Column(db.Boolean, default=False)

    priority = db.relationship('Priority', back_populates='tasks')
    tags = db.relationship('Tag', secondary='task_tags', back_populates='tasks')
    user = db.relationship('User', back_populates='tasks')  # Establish relationship to User

# Priority model
class Priority(db.Model):
    __tablename__ = 'priorities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    tasks = db.relationship('Task', back_populates='priority')

# Tag model
class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    tasks = db.relationship('Task', secondary='task_tags', back_populates='tags')

# TaskTags model (Many-to-Many relationship)
class TaskTag(db.Model):
    __tablename__ = 'task_tags'
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)
