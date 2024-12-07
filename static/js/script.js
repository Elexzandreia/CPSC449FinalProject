let token = null;
let tags = new Set();
let editTags = new Set();
let currentEditingTask = null;

// Message display function
function showMessage(message, isError = false) {
    const messageArea = document.getElementById('messageArea');
    messageArea.textContent = message;
    messageArea.className = isError ? 'error' : 'success';
    messageArea.style.display = 'block';
    setTimeout(() => {
        messageArea.style.display = 'none';
    }, 3000);
}

// Authentication section
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: document.getElementById('regUsername').value,
                password: document.getElementById('regPassword').value
            })
        });
        const data = await response.json();
        if (response.ok) {
            showMessage('Registration successful! Please login.');
            document.getElementById('registerForm').reset();
        } else {
            showMessage(data.error, true);
        }
    } catch (error) {
        showMessage('Registration failed: ' + error.message, true);
    }
});

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: document.getElementById('loginUsername').value,
                password: document.getElementById('loginPassword').value
            })
        });
        const data = await response.json();
        if (response.ok) {
            token = data.access_token;
            console.log('Token saved:', token);
            document.getElementById('authSection').classList.add('hidden');
            document.getElementById('aiAssistantSection').classList.remove('hidden')
            document.getElementById('taskSection').classList.remove('hidden');
            showMessage('Login successful!');
            fetchTasks();
        } else {
            showMessage(data.error, true);
        }
    } catch (error) {
        showMessage('Login failed: ' + error.message, true);
    }
});

// Task management functions
function addTag() {
    const tagInput = document.getElementById('tagInput');
    const tag = tagInput.value.trim();
    if (tag && !tags.has(tag)) {
        tags.add(tag);
        updateTagsDisplay();
        tagInput.value = '';
    }
}

function updateTagsDisplay() {
    const container = document.getElementById('tagsContainer');
    container.innerHTML = '';
    tags.forEach(tag => {
        const tagElement = document.createElement('span');
        tagElement.className = 'tag';
        tagElement.textContent = tag;
        container.appendChild(tagElement);
    });
}

document.getElementById('createTaskForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const response = await fetch('/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                title: document.getElementById('taskTitle').value,
                description: document.getElementById('taskDescription').value,
                priority_id: parseInt(document.getElementById('taskPriority').value),
                tags: Array.from(tags)
            })
        });
        const data = await response.json();
        if (response.ok) {
            showMessage('Task created successfully!');
            document.getElementById('createTaskForm').reset();
            tags.clear();
            updateTagsDisplay();
            fetchTasks();
        } else {
            showMessage(data.error, true);
        }
    } catch (error) {
        showMessage('Failed to create task: ' + error.message, true);
    }
});

async function fetchTasks() {
    try {
        const response = await fetch('/tasks/user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache'  // Add cache control header
            },
            body: JSON.stringify({
                timestamp: new Date().getTime()  // Add timestamp to bypass cache
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            displayTasks(data.tasks);
        } else {
            throw new Error(data.error || 'Failed to fetch tasks');
        }
    } catch (error) {
        showMessage('Failed to fetch tasks: ' + error.message, true);
    }
}

function displayTasks(tasks) {
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = `task-item priority-${task.priority.toLowerCase()}`;
        taskElement.innerHTML = `
            <h3>${task.title}</h3>
            <p>${task.description || 'No description'}</p>
            <div>Priority: ${task.priority}</div>
            <div class="tags-container">
                ${task.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
            </div>
        `;
        taskList.appendChild(taskElement);
    });
}

// Modal functions
function openEditModal(encodedTask) {
    try {
        // Decode and parse the task data
        const task = JSON.parse(decodeURIComponent(encodedTask));
        
        currentEditingTask = task;
        document.getElementById('editTaskId').value = task.id;
        document.getElementById('editTaskTitle').value = task.title;
        document.getElementById('editTaskDescription').value = task.description || '';
        document.getElementById('editTaskPriority').value = getPriorityId(task.priority);
        
        // Set up tags
        editTags = new Set(task.tags);
        updateEditTagsDisplay();
        
        // Show the modal
        const modal = document.getElementById('editTaskModal');
        modal.classList.remove('hidden');
        modal.classList.add('show');
    } catch (error) {
        console.error('Error opening edit modal:', error);
        showMessage('Error opening edit form. Please try again.', true);
    }
}

function closeEditModal() {
    // Reset the form
    document.getElementById('editTaskForm').reset();
    
    // Clear tags
    editTags.clear();
    updateEditTagsDisplay();
    
    // Reset current editing task
    currentEditingTask = null;
    
    // Hide the modal
    const modal = document.getElementById('editTaskModal');
    modal.classList.remove('show');
    modal.classList.add('hidden');
}

function getPriorityId(priorityName) {
    const priorities = {
        'HIGH': '1',
        'MEDIUM': '2',
        'LOW': '3'
    };
    return priorities[priorityName.toUpperCase()] || '2';
}

// Tag management for edit modal
function addEditTag() {
    const tagInput = document.getElementById('editTagInput');
    const tag = tagInput.value.trim();
    if (tag && !editTags.has(tag)) {
        editTags.add(tag);
        updateEditTagsDisplay();
        tagInput.value = '';
    }
}

function updateEditTagsDisplay() {
    const container = document.getElementById('editTagsContainer');
    container.innerHTML = '';
    editTags.forEach(tag => {
        const tagElement = document.createElement('span');
        tagElement.className = 'tag';
        tagElement.textContent = tag;
        container.appendChild(tagElement);
    });
}

// Update task display function
function displayTasks(tasks) {
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = `task-item priority-${task.priority.toLowerCase()}`;
        
        // Store task data as a data attribute with proper string escaping
        const taskData = encodeURIComponent(JSON.stringify(task));
        
        taskElement.innerHTML = `
            <div class="task-header">
                <div class="task-status">
                    <input type="checkbox" 
                           id="task-${task.id}" 
                           class="task-checkbox"
                           ${task.is_completed ? 'checked' : ''}
                           onchange="toggleTaskCompletion(${task.id}, this.checked)">
                    <h3 class="${task.is_completed ? 'completed-task' : ''}">${task.title}</h3>
                </div>
                <div class="task-actions">
                    <button class="button-small edit-button" onclick="openEditModal('${taskData}')">
                        Edit
                    </button>
                    <button class="button-small delete-button" onclick="deleteTask(${task.id})">
                        Delete
                    </button>
                </div>
            </div>
            <p>${task.description || 'No description'}</p>
            <div>Priority: ${task.priority}</div>
            <div class="tags-container">
                ${task.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
            </div>
        `;
        taskList.appendChild(taskElement);
    });
}

// Update the edit form submission handler
document.getElementById('editTaskForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const taskId = document.getElementById('editTaskId').value;
    
    try {
        // Add console logs for debugging
        const updateData = {
            title: document.getElementById('editTaskTitle').value,
            description: document.getElementById('editTaskDescription').value,
            priority_id: parseInt(document.getElementById('editTaskPriority').value),
            tags: Array.from(editTags)
        };
        
        console.log('Updating task:', taskId);
        console.log('Update data:', updateData);

        const response = await fetch(`/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(updateData)
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);

        if (response.ok) {
            showMessage('Task updated successfully!');
            closeEditModal();
            await fetchTasks(); // Make sure to await the fetch
        } else {
            throw new Error(data.error || 'Failed to update task');
        }
    } catch (error) {
        console.error('Update error:', error);
        showMessage('Failed to update task: ' + error.message, true);
    }
});

// Handle task deletion
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    try {
        const response = await fetch(`/tasks/${taskId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();
        if (response.ok) {
            showMessage('Task deleted successfully!');
            fetchTasks();
        } else {
            throw new Error(data.error || 'Failed to delete task');
        }
    } catch (error) {
        showMessage('Failed to delete task: ' + error.message, true);
    }
}

async function toggleTaskCompletion(taskId, isCompleted) {
    try {
        const response = await fetch(`/tasks/${taskId}/toggle-completion`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                is_completed: isCompleted,
                manage_tag: true  // Tell backend to manage 'Completed' tag
            })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to update task status');
        }

        // Refresh tasks to show updated state
        await fetchTasks();
        
    } catch (error) {
        console.error('Error updating task status:', error);
        showMessage('Failed to update task status: ' + error.message, true);
        // Revert checkbox state if there was an error
        const checkbox = document.getElementById(`task-${taskId}`);
        if (checkbox) {
            checkbox.checked = !isCompleted;
        }
    }
}

async function askAI() {
    const promptInput = document.getElementById('aiPrompt');
    const responseArea = document.getElementById('aiResponse');
    const prompt = promptInput.value.trim();
    
    if (!prompt) {
        showMessage('Please enter a question about your tasks', true);
        return;
    }
    
    
    // Show loading state
    responseArea.innerHTML = '<div class="ai-loading">Analyzing your tasks...</div>';
    
    try {
        if (!token) {
            throw new Error('No authentication token found. Please log in again.');
        }

        const response = await fetch('/api/tasks/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ prompt: prompt })
        });

        console.log('Response status:', response.status);
        
        const data = await response.json();
        
        // Log the response data for debugging
        console.log('Response data:', data);
        
        if (response.ok) {
            responseArea.textContent = data.response;
        } else {
            throw new Error(data.error || 'Failed to analyze tasks');
        }
    } catch (error) {
        responseArea.innerHTML = `
            <div class="ai-error">
                Sorry, I couldn't analyze your tasks right now: ${error.message}
            </div>
        `;

        // If token is missing, redirect to login
        if (error.message.includes('No authentication token')) {
            document.getElementById('authSection').classList.remove('hidden');
            document.getElementById('taskSection').classList.add('hidden');
        }
    }
}