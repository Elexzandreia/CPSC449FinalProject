CREATE DATABASE IF NOT EXISTS task_manager;
USE task_manager;

DROP TABLE IF EXISTS task_tags;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS priorities;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE priorities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL
);

CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(80) NOT NULL,
    description VARCHAR(200),
    priority_id INT,
    user_id INT NOT NULL,  -- Foreign key to users table
    FOREIGN KEY (priority_id) REFERENCES priorities(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE task_tags (
    task_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- Insert default priorities
INSERT INTO priorities (name) VALUES ('High');
INSERT INTO priorities (name) VALUES ('Medium');
INSERT INTO priorities (name) VALUES ('Low');