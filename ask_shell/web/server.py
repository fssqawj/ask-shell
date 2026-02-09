"""Web Server for Ask-Shell UI - Enhanced Version"""

import asyncio
import json
import threading
import re
import os
from datetime import datetime
from typing import Dict, List, Any
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from dataclasses import dataclass, asdict

from ..agent import AskShell
from ..ui.console import ConsoleUI
from rich.panel import Panel
from rich.syntax import Syntax


@dataclass
class TaskRecord:
    """Data class for storing task execution records"""
    id: str
    task: str
    status: str
    start_time: str
    end_time: str
    duration: float
    iterations: int
    success_count: int
    failure_count: int
    execution_log: List[Dict[str, Any]]
    summary: Dict[str, Any]
    created_at: str = None


class WebUI:
    """Enhanced Web-based UI for Ask-Shell with history tracking"""
    
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.active_sessions: Dict[str, AskShell] = {}
        self.session_outputs: Dict[str, List[str]] = {}
        self.task_history: List[TaskRecord] = []
        self.task_storage_path = os.path.join(os.path.dirname(__file__), 'task_history.json')
        
        self._load_task_history()
        self._setup_routes()
        self._setup_socket_handlers()
        
    def _load_task_history(self):
        """Load task history from file"""
        try:
            if os.path.exists(self.task_storage_path):
                with open(self.task_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.task_history = [TaskRecord(**record) for record in data]
        except Exception as e:
            print(f"Warning: Could not load task history: {e}")
            self.task_history = []
    
    def _save_task_history(self):
        """Save task history to file"""
        try:
            # Keep only last 100 tasks to prevent file from growing too large
            recent_tasks = self.task_history[-100:]
            with open(self.task_storage_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(task) for task in recent_tasks], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save task history: {e}")
    
    def _save_task_from_context(self, session_id: str, context, start_time=None):
        """Save task to history from context"""
        # Calculate duration
        end_time = datetime.now()
        start_time = start_time or getattr(context, 'start_time', end_time)
        if isinstance(start_time, str):
            # Convert ISO format string back to datetime if needed
            try:
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                # Handle different ISO format variations
                start_time = datetime.fromisoformat(start_time)
        duration = (end_time - start_time).total_seconds()
        
        # Create task record
        task_record = TaskRecord(
            id=session_id,
            task=context.task_description,
            status=context.status.value,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=duration,
            iterations=context.iteration,
            success_count=sum(1 for r in context.history if r.success),
            failure_count=sum(1 for r in context.history if not r.success),
            execution_log=self.session_logs.get(session_id, []),
            summary={
                'iterations': context.iteration,
                'success_count': sum(1 for r in context.history if r.success),
                'failure_count': sum(1 for r in context.history if not r.success)
            }
        )
        
        # Add to history
        self._add_task_record(task_record)
        print(f"DEBUG: Task saved to history: {session_id}")
    
    def _add_task_record(self, task_record: TaskRecord):
        """Add a task record to history"""
        self.task_history.append(task_record)
        self._save_task_history()
        # Broadcast to all connected clients
        self.socketio.emit('task_history_updated', {
            'task_count': len(self.task_history)
        })
    
    def _setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            return render_template('index_refactored.html')
        
        @self.app.route('/test')
        def test():
            return 'Test route working!'
        
        
        @self.app.route('/api/history')
        def get_task_history():
            """Get task history with pagination"""
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            # Sort by start time descending (newest first)
            sorted_history = sorted(self.task_history, 
                                  key=lambda x: x.start_time, 
                                  reverse=True)
            
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_tasks = sorted_history[start_idx:end_idx]
            
            return jsonify({
                'tasks': [asdict(task) for task in paginated_tasks],
                'total': len(self.task_history),
                'page': page,
                'per_page': per_page,
                'total_pages': (len(self.task_history) + per_page - 1) // per_page
            })
        
        @self.app.route('/api/history/<task_id>')
        def get_task_detail(task_id):
            """Get detailed information for a specific task"""
            task_record = next((task for task in self.task_history if task.id == task_id), None)
            if not task_record:
                return jsonify({'error': 'Task not found'}), 404
            
            return jsonify(asdict(task_record))
        
        @self.app.route('/api/history/<task_id>', methods=['DELETE'])
        def delete_task(task_id):
            """Delete a specific task from history"""
            task_index = next((i for i, task in enumerate(self.task_history) if task.id == task_id), None)
            if task_index is None:
                return jsonify({'error': 'Task not found'}), 404
            
            del self.task_history[task_index]
            self._save_task_history()
            
            return jsonify({'message': 'Task deleted successfully'})
        
        @self.app.route('/api/history/clear', methods=['POST'])
        def clear_task_history():
            """Clear all task history"""
            self.task_history.clear()
            self._save_task_history()
            
            return jsonify({'message': 'Task history cleared successfully'})
        
        @self.app.route('/api/run', methods=['POST'])
        def run_task():
            task = request.json.get('task', '')
            if not task:
                return jsonify({'error': 'Task is required'}), 400
            
            # Create a new session for this task
            session_id = request.json.get('session_id', 'default')
            
            # Initialize agent for this session
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = AskShell(auto_execute=True)
                self.session_outputs[session_id] = []
            
            # Initialize execution log for this session
            if not hasattr(self, 'session_logs'):
                self.session_logs = {}
            self.session_logs[session_id] = []
            
            # Record start time
            start_time = datetime.now()
            
            # Run the task in a separate thread to allow async updates
            def run_in_thread():
                agent = self.active_sessions[session_id]
                
                # Override the UI to send updates via WebSocket and capture logs
                original_ui = agent.ui
                web_ui_wrapper = self._create_web_ui_wrapper(agent.ui, session_id)
                agent.ui = web_ui_wrapper
                
                # Also update the UI reference in the skill manager
                original_skill_manager_ui = agent.skill_manager.ui
                agent.skill_manager.ui = web_ui_wrapper
                
                try:
                    context = agent.run(task)
                    
                    # Record end time and create task record
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    # Create task record
                    task_record = TaskRecord(
                        id=session_id,
                        task=task,
                        status=context.status.value,
                        start_time=start_time.isoformat(),
                        end_time=end_time.isoformat(),
                        duration=duration,
                        iterations=context.iteration,
                        success_count=sum(1 for r in context.history if r.success),
                        failure_count=sum(1 for r in context.history if not r.success),
                        execution_log=self.session_logs.get(session_id, []),
                        summary={
                            'iterations': context.iteration,
                            'success_count': sum(1 for r in context.history if r.success),
                            'failure_count': sum(1 for r in context.history if not r.success)
                        },
                        created_at=datetime.now().isoformat()
                    )
                    
                    # Add to history
                    self._add_task_record(task_record)
                    
                    self.socketio.emit('task_complete', {
                        'session_id': session_id,
                        'status': context.status.value,
                        'summary': {
                            'iterations': context.iteration,
                            'success_count': sum(1 for r in context.history if r.success),
                            'failure_count': sum(1 for r in context.history if not r.success)
                        }
                    }, room=session_id)
                except Exception as e:
                    # Record failed task
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    task_record = TaskRecord(
                        id=session_id,
                        task=task,
                        status='error',
                        start_time=start_time.isoformat(),
                        end_time=end_time.isoformat(),
                        duration=duration,
                        iterations=0,
                        success_count=0,
                        failure_count=1,
                        execution_log=self.session_logs.get(session_id, []),
                        summary={'error': str(e)},
                        created_at=datetime.now().isoformat()
                    )
                    
                    self._add_task_record(task_record)
                    
                    self.socketio.emit('error', {
                        'session_id': session_id,
                        'message': str(e)
                    }, room=session_id)
                finally:
                    # Restore original UI
                    agent.ui = original_ui
                    agent.skill_manager.ui = original_skill_manager_ui
            
            thread = threading.Thread(target=run_in_thread)
            thread.daemon = True
            thread.start()
            
            return jsonify({'status': 'started', 'session_id': session_id})
    
    def _setup_socket_handlers(self):
        """Setup Socket.IO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            print(f'Client connected: {request.sid}')
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f'Client disconnected: {request.sid}')
        
        @self.socketio.on('run_task_request')
        def handle_run_task_request(data):
            task = data.get('task', '')
            session_id = data.get('session_id', request.sid)
            
            print(f"DEBUG: Received run_task_request for session {session_id}, data keys: {list(data.keys())}")
            
            if not task:
                emit('error', {'session_id': session_id, 'message': 'Task is required'}, room=session_id)
                return
            
            # Initialize agent for this session if not exists
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = AskShell(auto_execute=True)
                self.session_outputs[session_id] = []
            
            # Initialize execution log for this session
            if not hasattr(self, 'session_logs'):
                self.session_logs = {}
            if session_id not in self.session_logs:
                self.session_logs[session_id] = []
            
            # Record start time for this session
            session_start_time = datetime.now()
            
            # Run the task in a separate thread to allow async updates
            def run_in_thread():
                agent = self.active_sessions[session_id]
                
                # Override the UI to send updates via WebSocket
                original_ui = agent.ui
                web_ui_wrapper = self._create_web_ui_wrapper(agent.ui, session_id)
                agent.ui = web_ui_wrapper
                
                # Also update the UI reference in the skill manager
                original_skill_manager_ui = agent.skill_manager.ui
                agent.skill_manager.ui = web_ui_wrapper
                
                print(f"DEBUG: Starting agent run for session {session_id}")
                try:
                    context = agent.run(task)
                    print(f"DEBUG: Task completed for session {session_id}")
                    
                    # Store context for history saving
                    agent.last_context = context
                    
                    # Emit task completion event to clients
                    self.socketio.emit('task_complete', {
                        'session_id': session_id,
                        'status': context.status.value,
                        'summary': {
                            'iterations': context.iteration,
                            'success_count': sum(1 for r in context.history if r.success),
                            'failure_count': sum(1 for r in context.history if not r.success)
                        }
                    }, room=session_id)
                    
                    # Save task to history
                    self._save_task_from_context(session_id, context, session_start_time)
                except Exception as e:
                    print(f"DEBUG: Error in agent run for session {session_id}: {e}")
                    
                    # Record failed task
                    end_time = datetime.now()
                    duration = (end_time - session_start_time).total_seconds()
                    
                    task_record = TaskRecord(
                        id=session_id,
                        task=task,
                        status='error',
                        start_time=session_start_time.isoformat(),
                        end_time=end_time.isoformat(),
                        duration=duration,
                        iterations=0,
                        success_count=0,
                        failure_count=1,
                        execution_log=self.session_logs.get(session_id, []),
                        summary={'error': str(e)},
                        created_at=datetime.now().isoformat()
                    )
                    
                    self._add_task_record(task_record)
                    
                    self.socketio.emit('error', {
                        'session_id': session_id,
                        'message': str(e)
                    }, room=session_id)
                finally:
                    # Restore original UI
                    agent.ui = original_ui
                    agent.skill_manager.ui = original_skill_manager_ui
            
            thread = threading.Thread(target=run_in_thread)
            thread.daemon = True
            thread.start()
            
            # Store thread reference for potential cancellation
            if not hasattr(self, 'active_threads'):
                self.active_threads = {}
            self.active_threads[session_id] = thread
        
        @self.socketio.on('stop_task_request')
        def handle_stop_task_request(data):
            session_id = data.get('session_id')
            print(f"DEBUG: Received stop_task_request for session {session_id}")
            
            if session_id in self.active_threads:
                thread = self.active_threads[session_id]
                # Note: Python threads can't be forcefully stopped, so we'll notify the client
                # that the request was received and the agent should handle cancellation internally
                del self.active_threads[session_id]
                
                # Emit task cancelled event
                self.socketio.emit('task_cancelled', {
                    'session_id': session_id,
                    'message': 'Task cancellation requested'
                }, room=session_id)
                
                # Attempt to cancel the agent's execution if possible
                if session_id in self.active_sessions:
                    agent = self.active_sessions[session_id]
                    # Set the cancellation flag to stop the agent gracefully
                    agent.cancelled = True
            else:
                self.socketio.emit('info', {
                    'session_id': session_id,
                    'message': 'No active task found to stop'
                }, room=session_id)
    
    def _create_web_ui_wrapper(self, console_ui: ConsoleUI, session_id: str):
        """Create a wrapper around ConsoleUI to emit events to web"""
        class WebUIWrapper:
            def __init__(self, console_ui, session_id, socketio, parent):
                self.console_ui = console_ui
                self.session_id = session_id
                self.socketio = socketio
                self.parent = parent
                # Only capture essential execution events, not streaming updates
                self.essential_events = {
                    'task_received', 'step_started', 'response_generated', 
                    'execution_result', 'task_complete', 'error', 'warning', 
                    'info', 'skill_selected', 'task_cancelled', 'max_iterations'
                }
            
            def _emit_event(self, event_type: str, data: dict):
                """Emit event to the specific session and capture only essential logs"""
                # Add session info to data
                data['session_id'] = self.session_id
                # Add timestamp
                data['timestamp'] = datetime.now().isoformat()
                
                # Only capture essential events for history (exclude streaming updates)
                if (hasattr(self.parent, 'session_logs') and 
                    self.session_id in self.parent.session_logs and 
                    event_type in self.essential_events):
                    log_entry = {
                        'event_type': event_type,
                        'data': data.copy(),
                        'timestamp': data['timestamp']
                    }
                    self.parent.session_logs[self.session_id].append(log_entry)
                
                # Debug logging
                print(f"DEBUG: Emitting event {event_type} to session {self.session_id}")
                # Emit to the default namespace - SocketIO should broadcast to all connected clients
                # The client JS will filter based on session_id if needed
                self.socketio.emit(event_type, data)
            
            def print_welcome(self):
                self.console_ui.print_welcome()
                self._emit_event('welcome', {})
            
            def print_task(self, task: str):
                self.console_ui.print_task(task)
                self._emit_event('task_received', {'task': task})
            
            def print_step(self, step: int):
                self.console_ui.print_step(step)
                self._emit_event('step_started', {'step': step})
            
            def print_response(self, response, skip_all: bool = False):
                self.console_ui.print_response(response, skip_all)
                # Emit response details
                response_data = {
                    'thinking': getattr(response, 'thinking', ''),
                    'command': getattr(response, 'command', ''),
                    'explanation': getattr(response, 'explanation', ''),
                    'next_step': getattr(response, 'next_step', ''),
                    'direct_response': getattr(response, 'direct_response', ''),
                    'is_dangerous': getattr(response, 'is_dangerous', False),
                    'danger_reason': getattr(response, 'danger_reason', ''),
                    'error_analysis': getattr(response, 'error_analysis', ''),
                    'skill_name': getattr(response, 'skill_name', 'unknown'),
                    'select_reason': getattr(response, 'select_reason', '')
                }
                self._emit_event('response_generated', response_data)
            
            def print_skill_response(self, response, skip_all: bool = False):
                self.print_response(response, skip_all)
            
            def print_error_analysis(self, error_analysis: str):
                self.console_ui.print_error_analysis(error_analysis)
                self._emit_event('error_analysis', {'analysis': error_analysis})
            
            def print_direct_response(self, direct_response: str):
                self.console_ui.print_direct_response(direct_response)
                self._emit_event('direct_response', {'response': direct_response})
            
            def print_result(self, result):
                self.console_ui.print_result(result)
                result_data = {
                    'success': result.success,
                    'command': result.command,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'output': result.truncated_output(max_length=500)  # Limit output size
                }
                self._emit_event('execution_result', result_data)
            
            def print_complete(self):
                self.console_ui.print_complete()
                self._emit_event('task_complete', {'status': 'completed'})
            
            def print_cancelled(self):
                self.console_ui.print_cancelled()
                self._emit_event('task_cancelled', {})
            
            def print_max_iterations(self, max_iter: int):
                self.console_ui.print_max_iterations(max_iter)
                self._emit_event('max_iterations', {'max_iter': max_iter})
            
            def print_error(self, message: str):
                self.console_ui.print_error(message)
                self._emit_event('error', {'message': message})
            
            def print_warning(self, message: str):
                self.console_ui.print_warning(message)
                self._emit_event('warning', {'message': message})
            
            def print_info(self, message: str):
                self.console_ui.print_info(message)
                self._emit_event('info', {'message': message})
            
            def print_danger_warning(self, reason: str):
                self.console_ui.print_danger_warning(reason)
                self._emit_event('danger_warning', {'reason': reason})
            
            def prompt_action(self) -> str:
                # For web interface, we'll default to 'y' (execute) to avoid blocking
                # In a more sophisticated implementation, we could wait for user input from the web UI
                self._emit_event('prompt_action_needed', {'message': 'Dangerous operation detected, executing automatically in web mode', 'default': 'y'})
                return 'y'
            
            def prompt_edit_command(self, default: str) -> str:
                # For web interface, return the default command without editing
                # In a more sophisticated implementation, we could allow editing via web UI
                self._emit_event('command_edit_prompt', {'default': default, 'result': default})
                return default
            
            def prompt_task(self) -> str:
                # This shouldn't be called in web mode, but if it is, return empty
                self._emit_event('task_prompt_needed', {'message': 'Task prompt needed in web mode'})
                return ""
            
            def print_summary(self, context):
                self.console_ui.print_summary(context)
                summary_data = {
                    'iteration': context.iteration,
                    'status': context.status.value,
                    'history_count': len(context.history)
                }
                self._emit_event('summary', summary_data)
            
            def print_skill_selected(self, skill_name: str, confidence: float, reasoning: str, capabilities: list):
                self.console_ui.print_skill_selected(skill_name, confidence, reasoning, capabilities)
                skill_data = {
                    'skill_name': skill_name,
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'capabilities': capabilities
                }
                self._emit_event('skill_selected', skill_data)
            
            # Animation methods - forward to console but also emit events
            def thinking_animation(self):
                self._emit_event('thinking_started', {})
                return self.console_ui.thinking_animation()
            
            def streaming_display(self):
                self._emit_event('streaming_started', {})
                
                # Create our own streaming content class that captures and emits updates
                class LocalStreamingContent:
                    def __init__(self, socketio_wrapper):
                        self.buffer = ""
                        self.thinking = ""
                        self.command = ""
                        self.explanation = ""
                        self.next_step = ""
                        self.error_analysis = ""
                        self.direct_response = ""
                        self.code = ""
                        self.title = ""
                        self.outline = ""
                        self.socketio_wrapper = socketio_wrapper
                        
                        # Record each field's currently displayed length
                        self.thinking_displayed = 0
                        self.command_displayed = 0
                        self.explanation_displayed = 0
                        self.next_step_displayed = 0
                        self.error_analysis_displayed = 0
                        self.direct_response_displayed = 0
                        self.code_displayed = 0
                        self.title_displayed = 0
                
                    def add_token(self, token: str):
                        """Add new token and extract field content in real-time"""
                        self.buffer += token
                        self._extract_fields()
                        # Emit the updated content via WebSocket
                        response_data = {
                            'thinking': self.thinking,
                            'command': self.command,
                            'explanation': self.explanation,
                            'next_step': self.next_step,
                            'direct_response': self.direct_response,
                            'code': self.code,
                            'title': self.title,
                            'outline': self.outline,
                            'error_analysis': self.error_analysis
                        }
                        self.socketio_wrapper._emit_event('streaming_update', response_data)
                    
                    def _extract_fields(self):
                        """Extract field content in real-time"""
                        # Extract thinking field
                        thinking_match = re.search(r'"thinking"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if thinking_match:
                            raw_content = thinking_match.group(1)
                            self.thinking = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    
                        # Extract error_analysis field
                        error_match = re.search(r'"error_analysis"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if error_match:
                            raw_content = error_match.group(1)
                            self.error_analysis = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    
                        # Extract command field
                        command_match = re.search(r'"command"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if command_match:
                            raw_content = command_match.group(1)
                            self.command = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    
                        # Extract explanation field
                        explanation_match = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if explanation_match:
                            raw_content = explanation_match.group(1)
                            self.explanation = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    
                        # Extract next_step field
                        next_step_match = re.search(r'"next_step"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if next_step_match:
                            raw_content = next_step_match.group(1)
                            self.next_step = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    
                        # Extract direct_response field
                        direct_response_match = re.search(r'"direct_response"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if direct_response_match:
                            raw_content = direct_response_match.group(1)
                            self.direct_response = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    
                        # Extract code field
                        code_match = re.search(r'"code"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if code_match:
                            raw_content = code_match.group(1)
                            self.code = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    
                        # Extract PPT skill title field
                        title_match = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                        if title_match:
                            raw_content = title_match.group(1)
                            self.title = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    
                        outline_start_pos = self.buffer.find('"outline"')
                        if outline_start_pos != -1:
                            self.outline = self.buffer[outline_start_pos:]

                content = LocalStreamingContent(self)
                
                # Use the original streaming_display context manager but intercept the callback
                from contextlib import contextmanager
                
                @contextmanager
                def streaming_context():
                    # Enter the original streaming_display context manager
                    original_cm = self.console_ui.streaming_display()
                    with original_cm as original_callback:
                        # Create a wrapper callback that sends data to both original and web
                        def wrapped_callback(token: str):
                            # Process token for web interface
                            content.add_token(token)
                            # Pass token to original callback for console display
                            original_callback(token)
                        
                        yield wrapped_callback
                
                return streaming_context()

            def executing_animation(self, command: str):
                self._emit_event('executing_started', {'command': command})
                return self.console_ui.executing_animation(command)
            
            def skill_selection_animation(self):
                self._emit_event('skill_selection_started', {})
                return self.console_ui.skill_selection_animation()
            
            def browser_code_generation_animation(self):
                self._emit_event('browser_code_generation_started', {'message': 'Generating browser automation code...'})
                return self.console_ui.browser_code_generation_animation()
        
        return WebUIWrapper(console_ui, session_id, self.socketio, self)


def create_app():
    """Create Flask app with SocketIO"""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.secret_key = 'ask-shell-web-ui-secret-key'
    
    # Configure SocketIO with async mode
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Initialize WebUI
    web_ui = WebUI(app, socketio)
    
    return app, socketio


def run_web_server(host='localhost', port=5000, debug=False):
    """Run the web server"""
    app, socketio = create_app()
    print(f"Starting Ask-Shell Web UI at http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, use_reloader=False)


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Ask-Shell Web UI')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    run_web_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()