let token = null;
let tags = new Set();
let editTags = new Set();
let currentEditingTask = null;
let currentFilter = 'all';
let filterUsername = '';

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

// // Helper function to determine priority from tags
// function getPriorityFromTags(tags) {
//     if (tags.includes('High')) return 'High';
//     if (tags.includes('Medium')) return 'Medium';
//     if (tags.includes('Low')) return 'Low';
//     return 'Medium'; // Default priority
// }

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
    console.log('Tasks received:', tasks); // Debug log
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = `task-item priority-${task.priority.toLowerCase()}`;
        
        // Store task data
        const taskData = encodeURIComponent(JSON.stringify(task));
        
        // Remove quotes from taskId in onchange event
        taskElement.innerHTML = `
            <div class="task-header">
                <div class="task-status">
                    <input type="checkbox"
                        id="task-${task.id}"  // Changed from task.task_id
                        class="task-checkbox"
                        ${task.tags.includes('Done') ? 'checked' : ''}
                        onchange="toggleTaskCompletion(${task.id}, this.checked)">
                    <h3 class="${task.tags.includes('Done') ? 'completed-task' : ''}">${task.title}</h3>
                </div>
                <div class="task-actions">
                    <button class="button-small edit-button" onclick="openEditModal('${taskData}')">
                        Edit
                    </button>
                    <button class="button-small delete-button" onclick="deleteTask(${task.task_id})">
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
        const updateData = {
            task_id: taskId,  // Add task_id to request body
            title: document.getElementById('editTaskTitle').value,
            description: document.getElementById('editTaskDescription').value,
            priority_id: parseInt(document.getElementById('editTaskPriority').value),
            tags: Array.from(editTags)
        };
        
        console.log('Updating task:', taskId);
        console.log('Update data:', updateData);

        const response = await fetch('/tasks/update', {  // Updated endpoint
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
            await fetchTasks();
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
        const response = await fetch('/tasks/delete', {  // Updated endpoint
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',  // Added Content-Type header
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ id: taskId })  // Add task_id to request body
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

// Update active filter button
function updateFilterButtons(activeFilter) {
    const buttons = document.querySelectorAll('.filter-button');
    buttons.forEach(button => {
        button.classList.remove('active');
        if (button.textContent.toLowerCase().includes(activeFilter)) {
            button.classList.add('active');
        }
    });
}

// Fetch all tasks (existing fetchTasks function)
async function fetchAllTasks() {
    currentFilter = 'all';
    updateFilterButtons('all');
    await fetchTasks();
}

// Fetch completed tasks
async function fetchCompletedTasks() {
    try {
        currentFilter = 'completed';
        updateFilterButtons('completed');
        
        const response = await fetch('/tasks/complete', { 
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();
        
        if (response.ok) {
            displayTasks(data);             // Update task count
            updateTaskStatus(`Showing ${data.length} completed tasks`);
            
            // If you need to filter by username (optional)
            if (filterUsername) {
                const filteredTasks = data.filter(task => task.username === filterUsername);
                displayTasks(filteredTasks);
                updateTaskStatus(`Showing ${filteredTasks.length} completed tasks for user ${filterUsername}`);
            }
        } else {
            throw new Error(data.error || 'Failed to fetch completed tasks');
        }
    } catch (error) {
        showMessage('Failed to fetch completed tasks: ' + error.message, true);
    }
}

// Fetch incomplete tasks
async function fetchIncompleteTasks() {
    try {
        currentFilter = 'incomplete';
        updateFilterButtons('incomplete');
        
        const response = await fetch('/tasks/incomplete', {
            method: 'GET',  // Changed to GET method
            headers: {
                'Authorization': `Bearer ${token}`
            }
            // Removed body since it's a GET request
        });
 
        const data = await response.json();
        
        if (response.ok) {
            displayTasks(data);  // data is already in the correct format
            // Update task count
            updateTaskStatus(`Showing ${data.length} incomplete tasks`);
            
            // If you need to filter by username (optional)
            if (filterUsername) {
                const filteredTasks = data.filter(task => task.username === filterUsername);
                displayTasks(filteredTasks);
                updateTaskStatus(`Showing ${filteredTasks.length} incomplete tasks for user ${filterUsername}`);
            }
        } else {
            throw new Error(data.error || 'Failed to fetch incomplete tasks');
        }
    } catch (error) {
        showMessage('Failed to fetch incomplete tasks: ' + error.message, true);
    }
 }

// Apply user filter
function applyUserFilter() {
    const usernameInput = document.getElementById('filterUsername');
    filterUsername = usernameInput.value.trim();
    
    // Refresh current view with new username filter
    switch(currentFilter) {
        case 'completed':
            fetchCompletedTasks();
            break;
        case 'incomplete':
            fetchIncompleteTasks();
            break;
        default:
            fetchAllTasks();
    }
}

// Update task status display
function updateTaskStatus(message) {
    const taskList = document.getElementById('taskList');

    const statusDiv = document.querySelector('.task-list-status') || document.createElement('div');
    statusDiv.className = 'task-list-status';  
    statusDiv.textContent = message;
    
    // Check for existing status with the correct class
    if (!document.querySelector('.task-list-status')) {
        taskList.parentElement.insertBefore(statusDiv, taskList);
    }
}

async function toggleTaskCompletion(taskId, isCompleted) {
    try {
        console.log('Original taskId:', taskId); // Debug log

        // Ensure taskId is a number (since your backend expects an integer)
        const numericTaskId = parseInt(taskId);

        // Get the current task element
        const taskElement = document.querySelector(`#task-${taskId}`).closest('.task-header').parentElement;
        
        // Get task data
        const title = taskElement.querySelector('h3').textContent;
        const description = taskElement.querySelector('p').textContent === 'No description' ? '' : taskElement.querySelector('p').textContent;
        
        // Extract priority ID from class name
        const priorityClass = taskElement.className.match(/priority-(\w+)/)[1];
        const priorityMap = {
            'high': 1,
            'medium': 2,
            'low': 3
        };
        const priority_id = priorityMap[priorityClass.toLowerCase()];
        
        // Get current tags from tags container
        const currentTags = Array.from(taskElement.querySelectorAll('.tag')).map(tag => tag.textContent);
        
        // Create updated tags array
        let tags = [...currentTags];
        if (isCompleted) {
            if (!tags.includes('Done')) {
                tags.push('Done');
            }
        } else {
            tags = tags.filter(tag => tag !== 'Done');
        }

        const updateData = {
            task_id: numericTaskId,  // Use the parsed numeric ID
            title: title,
            description: description,
            priority_id: priority_id,
            tags: tags
        };

        console.log('Sending update data:', updateData); // Debug log
        
        const response = await fetch('/tasks/update', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(updateData)
        });

        const data = await response.json();
        console.log('Response:', data); // Debug log

        if (!response.ok) {
            throw new Error(data.error || 'Failed to update task status');
        }

        // Refresh current view
        switch(currentFilter) {
            case 'completed':
                await fetchCompletedTasks();
                break;
            case 'incomplete':
                await fetchIncompleteTasks();
                break;
            default:
                await fetchAllTasks();
        }
        
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