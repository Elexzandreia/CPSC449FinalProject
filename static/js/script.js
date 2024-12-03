let token = null;
let tags = new Set();

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
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({})
        });
        const data = await response.json();
        if (response.ok) {
            displayTasks(data.tasks);
        } else {
            showMessage(data.error, true);
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