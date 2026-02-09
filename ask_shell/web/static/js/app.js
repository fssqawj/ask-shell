// Ask-Shell Web UI Client-Side JavaScript
// Main application logic and Socket.IO event handlers

class AskShellWebUI {
    constructor() {
        this.socket = io();
        this.sessionId = Date.now().toString();
        this.currentTaskId = null;
        this.currentStreamingElement = null;
        this.skillSelectionElement = null;
        this.syntaxHighlightTimeout = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupSocketHandlers();
        this.loadTaskHistory();
    }
    
    initializeElements() {
        this.outputContainer = document.getElementById('output-container');
        this.taskInput = document.getElementById('task-input');
        this.submitBtn = document.getElementById('submit-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.clearHistoryBtn = document.getElementById('clear-history-btn');
        this.taskHistoryList = document.getElementById('task-history-list');
        this.taskDetailModal = document.getElementById('task-detail-modal');
        this.taskDetailContent = document.getElementById('task-detail-content');
        this.closeModal = document.querySelector('.close-modal');
    }
    
    setupEventListeners() {
        this.submitBtn.addEventListener('click', () => this.executeTask());
        this.stopBtn.addEventListener('click', () => this.stopTask());
        this.clearBtn.addEventListener('click', () => this.clearLog());
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        this.closeModal.addEventListener('click', () => this.taskDetailModal.style.display = 'none');
        
        this.taskInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeTask();
            }
        });
        
        // Modal close when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === this.taskDetailModal) {
                this.taskDetailModal.style.display = 'none';
            }
        });
    }
    
    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('task_history_updated', () => {
            console.log('Task history updated, refreshing display');
            this.loadTaskHistory();
        });
        
        this.socket.on('task_received', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.addLogEntry('Task Received', `<strong>Task:</strong> ${this.escapeHtml(data.task)}`, 'task-received');
        });
        
        this.socket.on('step_started', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.currentStreamingElement = null;
            this.addLogEntry('Step Started', `Starting step <strong>${data.step}</strong>`, 'step-started');
        });
        
        this.socket.on('response_generated', (data) => {
            if (data.session_id !== this.sessionId) return;
            
            if (this.skillSelectionElement) {
                this.skillSelectionElement.remove();
                this.skillSelectionElement = null;
            }
            
            this.currentStreamingElement = null;
            
            let content = '';
            if (data.thinking) {
                content += `<div class="panel"><div class="panel-title">💡 Thinking Process</div>${this.escapeHtml(data.thinking)}</div>`;
            }
            if (data.command) {
                content += `<div class="panel panel-updating"><div class="panel-title">⚙️ Generated Command</div><pre class="shell-command"><code class="language-bash">${this.escapeHtml(data.command)}</code></pre></div>`;
            }
            if (data.explanation) {
                content += `<div class="panel"><div class="panel-title">💬 Explanation</div>${this.escapeHtml(data.explanation)}</div>`;
            }
            if (data.next_step) {
                content += `<div class="panel"><div class="panel-title">📋 Next Step</div>${this.escapeHtml(data.next_step)}</div>`;
            }
            if (data.direct_response) {
                content += `<div class="panel"><div class="panel-title">💡 AI Response</div>${this.escapeHtml(data.direct_response)}</div>`;
            }
            if (data.error_analysis) {
                content += `<div class="panel"><div class="panel-title">🔍 Error Analysis</div>${this.escapeHtml(data.error_analysis)}</div>`;
            }
            if (data.skill_name && data.select_reason) {
                content += `<div class="panel"><div class="panel-title">🎯 Skill Selected</div>Selected <strong>${data.skill_name}</strong>: ${this.escapeHtml(data.select_reason)}</div>`;
            }
            
            if (content) {
                this.addLogEntry('Response Generated', content, 'response-generated');
                this.debounceSyntaxHighlight();
                this.outputContainer.scrollTop = this.outputContainer.scrollHeight;
            }
        });
        
        this.socket.on('execution_result', (data) => {
            if (data.session_id !== this.sessionId) return;
            
            if (!window.lastExecutedCommand || window.lastExecutedCommand !== data.command) {
                window.lastExecutedCommand = data.command;
                let content = `<strong>Command:</strong> <pre class="shell-command"><code class="language-bash">${this.escapeHtml(data.command || '(no command)')}</code></pre><br>`;
                content += `<strong>Status:</strong> ${data.success ? '<span style="color: var(--success);">SUCCESS</span>' : '<span style="color: var(--error);">FAILED</span>'}<br>`;
                
                if (data.output && data.output !== '(无输出)') {
                    content += `<div class="command-output">${this.escapeHtml(data.output)}</div>`;
                }
                
                this.addLogEntry('Execution Result', content, 'execution-result');
                this.debounceSyntaxHighlight();
                this.outputContainer.scrollTop = this.outputContainer.scrollHeight;
            }
        });
        
        this.socket.on('task_complete', (data) => {
            if (data.session_id !== this.sessionId) return;
            
            this.currentStreamingElement = null;
            let content = `Task completed with status: <strong>${data.status}</strong>`;
            if (data.summary) {
                content += `<br>Iterations: ${data.summary.iterations}, Success: ${data.summary.success_count}, Failure: ${data.summary.failure_count}`;
            }
            this.addLogEntry('Task Completed', content, 'status-completed');
            this.submitBtn.disabled = false;
            this.stopBtn.style.display = 'none';
            
            // Refresh history to show completed task
            setTimeout(() => this.loadTaskHistory(), 1000);
        });
        
        this.socket.on('error', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.addLogEntry('Error', this.escapeHtml(data.message), 'error-message');
            this.stopBtn.style.display = 'none';
            this.submitBtn.disabled = false;
        });
        
        // Real-time streaming updates
        this.socket.on('streaming_update', (data) => {
            if (data.session_id !== this.sessionId) return;
            
            let content = '';
            
            if (data.thinking) {
                content += `<div class="panel"><div class="panel-title">💡 Thinking Process</div>${this.escapeHtml(data.thinking)}</div>`;
            }
            
            if (data.command) {
                content += `<div class="panel panel-updating"><div class="panel-title">⚙️ Generated Command</div><pre class="shell-command"><code class="language-bash">${this.escapeHtml(data.command)}</code></pre></div>`;
            }
            
            if (data.explanation) {
                content += `<div class="panel"><div class="panel-title">💬 Explanation</div>${this.escapeHtml(data.explanation)}</div>`;
            }
            
            if (data.next_step) {
                content += `<div class="panel"><div class="panel-title">📋 Next Step</div>${this.escapeHtml(data.next_step)}</div>`;
            }
            
            if (data.direct_response) {
                content += `<div class="panel"><div class="panel-title">💡 AI Response</div>${this.escapeHtml(data.direct_response)}</div>`;
            }
            
            if (data.error_analysis) {
                content += `<div class="panel"><div class="panel-title">🔍 Error Analysis</div>${this.escapeHtml(data.error_analysis)}</div>`;
            }
            
            if (data.code) {
                content += `<div class="panel panel-updating"><div class="panel-title">💻 Generated Code</div><pre class="python-code"><code class="language-python">${this.escapeHtml(data.code)}</code></pre></div>`;
            }
            
            if (content) {
                if (!this.currentStreamingElement) {
                    this.currentStreamingElement = document.createElement('div');
                    this.currentStreamingElement.className = 'log-entry response-generated';
                    const timestamp = new Date().toLocaleTimeString();
                    this.currentStreamingElement.innerHTML = `
                        <div class="log-header">
                            <div class="log-title">Streaming Update</div>
                            <div class="log-timestamp">${timestamp}</div>
                        </div>
                        <div id="streaming-content">${content}</div>
                    `;
                    this.outputContainer.appendChild(this.currentStreamingElement);
                } else {
                    const contentDiv = this.currentStreamingElement.querySelector('#streaming-content');
                    if (contentDiv) {
                        contentDiv.innerHTML = content;
                    }
                }
                
                this.debounceSyntaxHighlight();
                this.outputContainer.scrollTop = this.outputContainer.scrollHeight;
            }
        });
        
        this.socket.on('thinking_started', (data) => {
            if (data.session_id !== this.sessionId) return;
            if (this.skillSelectionElement) {
                this.skillSelectionElement.remove();
                this.skillSelectionElement = null;
            }
            this.addLogEntry('Thinking', '<span class="thinking-indicator"></span> AI is thinking...', 'info-message');
        });
        
        this.socket.on('executing_started', (data) => {
            if (data.session_id !== this.sessionId) return;
            if (this.skillSelectionElement) {
                this.skillSelectionElement.remove();
                this.skillSelectionElement = null;
            }
            this.addLogEntry('Executing Command', `Running: <strong>${this.escapeHtml(data.command)}</strong>`, 'info-message');
        });
        
        this.socket.on('skill_selection_started', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.skillSelectionElement = document.createElement('div');
            this.skillSelectionElement.className = 'log-entry info-message';
            const timestamp = new Date().toLocaleTimeString();
            this.skillSelectionElement.innerHTML = `
                <div class="log-header">
                    <div class="log-title">Skill Selection</div>
                    <div class="log-timestamp">${timestamp}</div>
                </div>
                <div><span class="thinking-indicator"></span> Analyzing task and selecting skill...</div>
            `;
            this.outputContainer.appendChild(this.skillSelectionElement);
            
            const loadingElement = this.outputContainer.querySelector('.loading');
            if (loadingElement) {
                loadingElement.remove();
            }
            
            this.outputContainer.scrollTop = this.outputContainer.scrollHeight;
        });
        
        // Additional socket event handlers
        this.socket.on('warning', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.addLogEntry('Warning', this.escapeHtml(data.message), 'warning-message');
        });
        
        this.socket.on('info', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.addLogEntry('Info', this.escapeHtml(data.message), 'info-message');
        });
        
        this.socket.on('skill_selected', (data) => {
            if (data.session_id !== this.sessionId) return;
            let content = `<strong>Skill:</strong> ${data.skill_name}<br>`;
            content += `<strong>Confidence:</strong> ${(data.confidence * 100).toFixed(0)}%<br>`;
            content += `<strong>Reasoning:</strong> ${this.escapeHtml(data.reasoning)}<br>`;
            content += `<strong>Capabilities:</strong> ${data.capabilities.join(', ')}`;
            this.addLogEntry('Skill Selected', content, 'skill-selected');
        });
        
        this.socket.on('task_cancelled', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.addLogEntry('Task Cancelled', 'Task was cancelled by user', 'status-error');
            this.submitBtn.disabled = false;
            this.stopBtn.style.display = 'none';
        });
        
        this.socket.on('max_iterations', (data) => {
            if (data.session_id !== this.sessionId) return;
            this.addLogEntry('Max Iterations Reached', `Reached maximum iterations limit: ${data.max_iter}`, 'status-error');
            this.submitBtn.disabled = false;
            this.stopBtn.style.display = 'none';
        });
    }
    
    executeTask() {
        const task = this.taskInput.value.trim();
        if (!task) {
            alert('Please enter a task');
            return;
        }
        
        const loadingElement = this.outputContainer.querySelector('.loading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        this.submitBtn.disabled = true;
        this.stopBtn.style.display = 'block';
        this.currentTaskId = this.sessionId;
        
        this.socket.emit('run_task_request', {
            task: task,
            session_id: this.sessionId
        });
        
        this.taskInput.value = '';
    }
    
    stopTask() {
        this.stopBtn.disabled = true;
        this.stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
        
        this.socket.emit('stop_task_request', {
            session_id: this.sessionId
        });
        
        this.addLogEntry('Task Stopping', 'Request sent to stop the current task...', 'info-message');
        
        setTimeout(() => {
            this.stopBtn.disabled = false;
            this.stopBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        }, 2000);
    }
    
    clearLog() {
        this.outputContainer.innerHTML = `
            <div class="loading">
                <div class="loading-icon">
                    <i class="fas fa-circle-notch"></i>
                </div>
                <span>Log cleared. Enter a task to begin.</span>
            </div>
        `;
    }
    
    addLogEntry(title, content, className) {
        const timestamp = new Date().toLocaleTimeString();
        const entryDiv = document.createElement('div');
        entryDiv.className = `log-entry ${className}`;
        entryDiv.innerHTML = `
            <div class="log-header">
                <div class="log-title">${title}</div>
                <div class="log-timestamp">${timestamp}</div>
            </div>
            <div class="log-content">${content}</div>
        `;
        
        const loadingElement = this.outputContainer.querySelector('.loading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        this.outputContainer.appendChild(entryDiv);
        this.outputContainer.scrollTop = this.outputContainer.scrollHeight;
    }
    
    loadTaskHistory() {
        fetch('/api/history')
            .then(response => response.json())
            .then(data => {
                this.renderTaskHistory(data.tasks);
            })
            .catch(error => {
                console.error('Error loading task history:', error);
            });
    }
    
    renderTaskHistory(tasks) {
        this.taskHistoryList.innerHTML = '';
                
        if (tasks.length === 0) {
            this.taskHistoryList.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">No task history yet</div>';
            return;
        }
    
        // Sort tasks by start time (newest first)
        tasks.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
    
        tasks.forEach(task => {
            const taskElement = document.createElement('div');
            taskElement.className = 'task-item';
            if (task.id === this.currentTaskId) {
                taskElement.classList.add('active');
            }
                    
            // Format duration
            const duration = task.duration ? `${task.duration.toFixed(1)}s` : 'N/A';
                    
            taskElement.innerHTML = `
                <div class="task-header">
                    <div class="task-name" title="${this.escapeHtml(task.task)}">${this.truncateText(task.task, 40)}</div>
                    <div class="task-status status-${task.status}">${task.status}</div>
                </div>
                <div class="task-meta">
                    <div class="task-time">${this.formatTime(task.start_time)}</div>
                    <div>${task.iterations} iter • ${duration}</div>
                </div>
                <div style="margin-top: 8px; font-size: 0.8rem; color: var(--text-secondary);">
                    ${task.success_count} success, ${task.failure_count} failed
                </div>
            `;
                    
            taskElement.addEventListener('click', () => this.showTaskDetail(task.id));
            this.taskHistoryList.appendChild(taskElement);
        });
    }
    
    showTaskDetail(taskId) {
        fetch(`/api/history/${taskId}`)
            .then(response => response.json())
            .then(task => {
                this.renderTaskDetail(task);
                this.taskDetailModal.style.display = 'block';
                // Initialize expandable content after a short delay
                setTimeout(() => this.initializeExpandableContent(), 100);
            })
            .catch(error => {
                console.error('Error loading task detail:', error);
            });
    }
    
    renderTaskDetail(task) {
        const duration = task.duration ? `${task.duration.toFixed(2)}s` : 'N/A';
        const successRate = task.iterations > 0 ? ((task.success_count / task.iterations) * 100).toFixed(1) : 0;
        
        this.taskDetailContent.innerHTML = `
            <div class="task-detail-header">
                <h2 class="task-detail-title">${this.escapeHtml(task.task)}</h2>
                <div class="task-status status-${task.status}">${task.status.toUpperCase()}</div>
            </div>
            
            <div class="task-detail-meta">
                <div class="meta-item">
                    <div class="meta-label">Start Time</div>
                    <div class="meta-value">${this.formatDateTime(task.start_time)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">End Time</div>
                    <div class="meta-value">${this.formatDateTime(task.end_time)}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Duration</div>
                    <div class="meta-value">${duration}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Iterations</div>
                    <div class="meta-value">${task.iterations}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Success Rate</div>
                    <div class="meta-value">${successRate}%</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Success/Failure</div>
                    <div class="meta-value">${task.success_count}/${task.failure_count}</div>
                </div>
            </div>
            
            <div class="execution-log">
                <h3 style="margin: 25px 0 15px 0; color: var(--primary);">
                    <i class="fas fa-list-ol"></i> Execution Timeline
                </h3>
                <div class="log-timeline">
                    ${this.renderExecutionTimeline(task.execution_log)}
                </div>
            </div>
            
            <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid var(--dark-border);">
                <h3 style="margin-bottom: 15px; color: var(--primary);">
                    <i class="fas fa-chart-bar"></i> Task Summary
                </h3>
                <div style="background: rgba(42, 42, 74, 0.5); padding: 20px; border-radius: 12px; border: 1px solid var(--dark-border);">
                    ${this.renderTaskSummary(task.summary)}
                </div>
            </div>
        `;
    }
    
    renderExecutionTimeline(logEntries) {
        if (!logEntries || logEntries.length === 0) {
            return '<div style="text-align: center; color: var(--text-secondary); padding: 20px;">No execution log available</div>';
        }
        
        return logEntries.map((entry, index) => {
            const timestamp = new Date(entry.timestamp).toLocaleTimeString();
            let content = '';
            let icon = '';
            let bgColor = 'rgba(42, 42, 74, 0.3)';
            
            switch(entry.event_type) {
                case 'task_received':
                    icon = '<i class="fas fa-receipt" style="color: var(--primary);"></i>';
                    content = `Task received: <div class="expandable-content">${this.escapeHtml(entry.data.task)}</div>`;
                    break;
                case 'step_started':
                    icon = '<i class="fas fa-play-circle" style="color: var(--warning);"></i>';
                    content = `Step ${entry.data.step} started`;
                    break;
                case 'response_generated':
                    icon = '<i class="fas fa-robot" style="color: var(--secondary);"></i>';
                    content = 'AI generated response';
                    if (entry.data.thinking) content += `<br><strong>Thinking:</strong> <div class="expandable-content">${this.escapeHtml(entry.data.thinking)}</div>`;
                    if (entry.data.command) content += `<br><strong>Command:</strong> <code style="background: var(--terminal-bg); padding: 2px 6px; border-radius: 4px;"><div class="expandable-content">${this.escapeHtml(entry.data.command)}</div></code>`;
                    if (entry.data.explanation) content += `<br><strong>Explanation:</strong> <div class="expandable-content">${this.escapeHtml(entry.data.explanation)}</div>`;
                    if (entry.data.next_step) content += `<br><strong>Next Step:</strong> <div class="expandable-content">${this.escapeHtml(entry.data.next_step)}</div>`;
                    if (entry.data.direct_response) content += `<br><strong>Direct Response:</strong> <div class="expandable-content">${this.escapeHtml(entry.data.direct_response)}</div>`;
                    if (entry.data.error_analysis) content += `<br><strong>Error Analysis:</strong> <div class="expandable-content">${this.escapeHtml(entry.data.error_analysis)}</div>`;
                    break;
                case 'execution_result':
                    const status = entry.data.success ? 'SUCCESS' : 'FAILED';
                    icon = entry.data.success ? '<i class="fas fa-check-circle" style="color: var(--success);"></i>' : '<i class="fas fa-times-circle" style="color: var(--error);"></i>';
                    bgColor = entry.data.success ? 'rgba(0, 255, 157, 0.1)' : 'rgba(255, 77, 109, 0.1)';
                    content = `<strong>Command execution ${status}</strong>: <div class="expandable-content">${this.escapeHtml(entry.data.command)}</div>`;
                    if (entry.data.output && entry.data.output !== '(无输出)') {
                        content += `<br><strong>Output:</strong> <div class="command-output expandable-content">${this.escapeHtml(entry.data.output)}</div>`;
                    }
                    break;
                case 'error':
                    icon = '<i class="fas fa-exclamation-triangle" style="color: var(--error);"></i>';
                    bgColor = 'rgba(255, 77, 109, 0.1)';
                    content = `Error: <div class="expandable-content">${this.escapeHtml(entry.data.message)}</div>`;
                    break;
                case 'skill_selected':
                    icon = '<i class="fas fa-brain" style="color: var(--secondary);"></i>';
                    content = `Skill selected: <strong>${this.escapeHtml(entry.data.skill_name)}</strong> (Confidence: ${(entry.data.confidence * 100).toFixed(0)}%)`;
                    if (entry.data.reasoning) content += `<br><strong>Reasoning:</strong> <div class="expandable-content">${this.escapeHtml(entry.data.reasoning)}</div>`;
                    break;
                case 'thinking_started':
                    icon = '<i class="fas fa-spinner fa-spin" style="color: var(--warning);"></i>';
                    content = 'AI is thinking...';
                    break;
                case 'executing_started':
                    icon = '<i class="fas fa-terminal" style="color: var(--primary);"></i>';
                    content = `Executing: <code style="background: var(--terminal-bg); padding: 2px 6px; border-radius: 4px;"><div class="expandable-content">${this.escapeHtml(entry.data.command)}</div></code>`;
                    break;
                default:
                    icon = '<i class="fas fa-info-circle" style="color: var(--text-secondary);"></i>';
                    content = `${entry.event_type}: <div class="expandable-content">${this.escapeHtml(JSON.stringify(entry.data, null, 2))}</div>`;
            }
            
            // Add special class for step boundaries to make them more visually distinct
            const isStepBoundary = entry.event_type === 'step_started';
            const timelineItemClass = isStepBoundary ? 'timeline-item step-boundary' : 'timeline-item';
            const stepDataAttr = isStepBoundary ? `data-step-number="${entry.data.step}"` : '';
            
            return `
                <div class="${timelineItemClass}" style="background: ${bgColor};" data-entry-index="${index}" ${stepDataAttr}>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        ${icon}
                        <div style="font-weight: 600; color: var(--primary);">
                            ${timestamp}
                        </div>
                    </div>
                    <div class="timeline-content">${content}</div>
                </div>
            `;
        }).join('');
    }
    
    initializeExpandableContent() {
        // Add click handlers to expandable content
        document.querySelectorAll('.expandable-content').forEach(element => {
            // Always add truncated class by default for content that could be long
            element.classList.add('truncated');
            
            // Force a reflow to ensure the element has proper dimensions for measurement
            element.style.display = 'block';
            void element.offsetWidth; // Trigger reflow
            
            // Add click handler to toggle expanded/truncated state
            element.addEventListener('click', function(e) {
                e.stopPropagation();
                if (this.classList.contains('truncated')) {
                    this.classList.remove('truncated');
                    this.classList.add('expanded');
                } else {
                    this.classList.remove('expanded');
                    this.classList.add('truncated');
                }
            });
        });
    }
    
    clearHistory() {
        if (confirm('Are you sure you want to clear all task history?')) {
            fetch('/api/history/clear', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                this.loadTaskHistory();
                alert('Task history cleared successfully');
            })
            .catch(error => {
                console.error('Error clearing history:', error);
            });
        }
    }
    
    // Helper functions
    escapeHtml(text) {
        if (typeof text !== 'string') {
            return String(text);
        }
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    renderTaskSummary(summary) {
        if (!summary) return '<div>No summary available</div>';
        
        let summaryHtml = '';
        
        // Handle different summary types
        if (summary.iterations !== undefined) {
            summaryHtml += `
                <div style="margin-bottom: 15px;">
                    <strong>Iterations:</strong> ${summary.iterations}
                </div>
                <div style="margin-bottom: 15px;">
                    <strong>Success Count:</strong> ${summary.success_count}
                </div>
                <div style="margin-bottom: 15px;">
                    <strong>Failure Count:</strong> ${summary.failure_count}
                </div>
            `;
        }
        
        if (summary.error) {
            summaryHtml += `
                <div style="margin-bottom: 15px; color: var(--error);">
                    <strong>Error:</strong> ${this.escapeHtml(summary.error)}
                </div>
            `;
        }
        
        // Add any other summary fields
        Object.keys(summary).forEach(key => {
            if (!['iterations', 'success_count', 'failure_count', 'error'].includes(key)) {
                summaryHtml += `
                    <div style="margin-bottom: 15px;">
                        <strong>${key}:</strong> ${this.escapeHtml(String(summary[key]))}
                    </div>
                `;
            }
        });
        
        return summaryHtml || '<div>No detailed summary available</div>';
    }
    
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    formatTime(isoString) {
        return new Date(isoString).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    formatDateTime(isoString) {
        return new Date(isoString).toLocaleString();
    }
    
    // Debounced syntax highlighter
    debounceSyntaxHighlight() {
        if (this.syntaxHighlightTimeout) {
            clearTimeout(this.syntaxHighlightTimeout);
        }
        this.syntaxHighlightTimeout = setTimeout(() => {
            Prism.highlightAll();
        }, 1000);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.askShellApp = new AskShellWebUI();
});