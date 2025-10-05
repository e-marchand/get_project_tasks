#!/usr/bin/env python3
"""
GitHub Project Tasks MCP Server
A Model Context Protocol server that provides tools for querying GitHub Projects.

This server exposes the following tools:
1. get_project_tasks_full - Get all tasks from a project with optional filters
2. get_child_tasks - Get child tasks of a specific task
3. get_task_info - Get detailed information about a specific task

All tools support filtering by label, status, and assignee.
"""

import json
import os
from typing import Dict, List, Any
from pathlib import Path

# Try to import dotenv for loading .env files
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Import the GitHub project manager from the existing script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from get_project_tasks import GitHubProjectManager


class GitHubProjectMCPServer:
    """MCP Server for GitHub Project operations."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.manager = None
        self.token = None
        
    def initialize(self, token: str = None):
        """Initialize the GitHub manager with a token."""
        # If no token provided and dotenv is available, try to load .env file
        if not token and DOTENV_AVAILABLE:
            # Look for .env file in the current directory and parent directories
            env_path = Path.cwd() / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=True)
            else:
                # Try script directory
                script_dir = Path(__file__).parent
                env_path = script_dir / '.env'
                if env_path.exists():
                    load_dotenv(env_path, override=True)
                else:
                    # Try parent directory of script (project root)
                    env_path = script_dir.parent / '.env'
                    if env_path.exists():
                        load_dotenv(env_path, override=True)
        
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or pass it explicitly.")
        self.manager = GitHubProjectManager(self.token)
    
    def _filter_items(self, items: List[Dict], label: str = None, status: str = None, assignee: str = None) -> List[Dict]:
        """Apply filters to a list of items."""
        filters = {}
        if label:
            filters['label'] = label
        if status:
            filters['status'] = status
        if assignee:
            filters['assignee'] = assignee
        
        if filters:
            return self.manager.filter_items(items, filters)
        return items
    
    def get_project_tasks_full(
        self,
        org: str = None,
        project_id: int = None,
        label: str = None,
        status: str = None,
        assignee: str = None,
        item_type: str = None
    ) -> Dict[str, Any]:
        """
        Get all tasks from a GitHub project with optional filtering.
        
        Args:
            org: GitHub organization name (uses GITHUB_ORG env var if not provided)
            project_id: GitHub project number
            label: Filter by label name (case-insensitive, optional)
            status: Filter by status field value (case-insensitive, optional)
            assignee: Filter by assignee username (optional)
            item_type: Filter by type: 'issue', 'pull_request', or 'draft_issue' (optional)
        
        Returns:
            Dictionary containing project info and filtered tasks
        """
        if not self.manager:
            self.initialize()
        
        # Get organization from argument or environment variable
        org = org or os.getenv('GITHUB_ORG')
        if not org:
            raise ValueError("GitHub organization is required. Provide 'org' parameter or set GITHUB_ORG environment variable.")
        
        if not project_id:
            raise ValueError("project_id is required.")
        
        # Get project information
        project_info = self.manager.get_project_by_number(org, project_id)
        
        # Get all project items
        items = self.manager.get_all_project_items(project_info['id'])
        
        # Apply type filter if specified
        filters = {}
        if item_type:
            filters['type'] = item_type
        if label:
            filters['label'] = label
        if status:
            filters['status'] = status
        if assignee:
            filters['assignee'] = assignee
        
        if filters:
            items = self.manager.filter_items(items, filters)
        
        # Parse items
        parsed_items = [self.manager.parse_item_data(item) for item in items]
        
        return {
            'project': {
                'id': project_info['id'],
                'title': project_info['title'],
                'description': project_info.get('shortDescription', ''),
                'url': project_info['url'],
                'closed': project_info['closed'],
                'created_at': project_info['createdAt'],
                'updated_at': project_info['updatedAt']
            },
            'total_count': len(parsed_items),
            'filters_applied': filters,
            'tasks': parsed_items
        }
    
    def get_child_tasks(
        self,
        org: str = None,
        project_id: int = None,
        task_id: str = None,
        task_number: int = None,
        label: str = None,
        status: str = None,
        assignee: str = None
    ) -> Dict[str, Any]:
        """
        Get child tasks of a specific parent task.
        
        Args:
            org: GitHub organization name (uses GITHUB_ORG env var if not provided)
            project_id: GitHub project number
            task_id: GitHub issue/task ID (optional, either this or task_number required)
            task_number: GitHub issue number (optional, either this or task_id required)
            label: Filter child tasks by label name (case-insensitive, optional)
            status: Filter child tasks by status field value (case-insensitive, optional)
            assignee: Filter child tasks by assignee username (optional)
        
        Returns:
            Dictionary containing parent task info and its child tasks
        """
        if not self.manager:
            self.initialize()
        
        # Get organization from argument or environment variable
        org = org or os.getenv('GITHUB_ORG')
        if not org:
            raise ValueError("GitHub organization is required. Provide 'org' parameter or set GITHUB_ORG environment variable.")
        
        if not project_id:
            raise ValueError("project_id is required.")
        
        if not task_id and not task_number:
            raise ValueError("Either task_id or task_number must be provided")
        
        # Get project information
        project_info = self.manager.get_project_by_number(org, project_id)
        
        # Get all project items
        items = self.manager.get_all_project_items(project_info['id'])
        
        # Parse all items
        parsed_items = [self.manager.parse_item_data(item) for item in items]
        
        # Find the parent task
        parent_task = None
        if task_number:
            parent_task = next((item for item in parsed_items if item.get('number') == task_number), None)
        elif task_id:
            parent_task = next((item for item in parsed_items if item['id'] == task_id), None)
        
        if not parent_task:
            raise ValueError(f"Task not found in project (task_id={task_id}, task_number={task_number})")
        
        # Get child tasks from sub_issues
        child_tasks = []
        if parent_task.get('sub_issues'):
            # Create a mapping of issue numbers to parsed items
            number_to_item = {item['number']: item for item in parsed_items if item.get('number')}
            
            for sub_issue in parent_task['sub_issues']:
                sub_number = sub_issue.get('number')
                if sub_number and sub_number in number_to_item:
                    child_task = number_to_item[sub_number]
                    child_tasks.append(child_task)
        
        # Apply filters to child tasks
        filters = {}
        if label:
            filters['label'] = label
        if status:
            filters['status'] = status
        if assignee:
            filters['assignee'] = assignee
        
        if filters:
            # We need to convert back to the raw format for filtering, then parse again
            raw_items = [item for item in items if self.manager.parse_item_data(item)['id'] in [ct['id'] for ct in child_tasks]]
            filtered_raw = self.manager.filter_items(raw_items, filters)
            child_tasks = [self.manager.parse_item_data(item) for item in filtered_raw]
        
        return {
            'parent_task': parent_task,
            'total_children': len(child_tasks),
            'filters_applied': filters,
            'child_tasks': child_tasks
        }
    
    def get_task_info(
        self,
        org: str = None,
        project_id: int = None,
        task_id: str = None,
        task_number: int = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific task.
        
        Args:
            org: GitHub organization name (uses GITHUB_ORG env var if not provided)
            project_id: GitHub project number
            task_id: GitHub issue/task ID (optional, either this or task_number required)
            task_number: GitHub issue number (optional, either this or task_id required)
        
        Returns:
            Dictionary containing complete task information
        """
        if not self.manager:
            self.initialize()
        
        # Get organization from argument or environment variable
        org = org or os.getenv('GITHUB_ORG')
        if not org:
            raise ValueError("GitHub organization is required. Provide 'org' parameter or set GITHUB_ORG environment variable.")
        
        if not project_id:
            raise ValueError("project_id is required.")
        
        if not task_id and not task_number:
            raise ValueError("Either task_id or task_number must be provided")
        
        # Get project information
        project_info = self.manager.get_project_by_number(org, project_id)
        
        # Get all project items
        items = self.manager.get_all_project_items(project_info['id'])
        
        # Parse all items
        parsed_items = [self.manager.parse_item_data(item) for item in items]
        
        # Find the task
        task = None
        if task_number:
            task = next((item for item in parsed_items if item.get('number') == task_number), None)
        elif task_id:
            task = next((item for item in parsed_items if item['id'] == task_id), None)
        
        if not task:
            raise ValueError(f"Task not found in project (task_id={task_id}, task_number={task_number})")
        
        return {
            'project': {
                'id': project_info['id'],
                'title': project_info['title'],
                'url': project_info['url']
            },
            'task': task
        }
    
    def create_test_case_task(
        self,
        org: str = None,
        project_id: int = None,
        parent_task_number: int = None,
        parent_task_id: str = None,
        title: str = None,
        description: str = None,
        test_steps: str = None,
        expected_result: str = None,
        assignees: List[str] = None,
        labels: List[str] = None,
        status: str = None,
        test_type: str = None,
        platforms: str = None,
        test_database: str = None,
        test_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a test case task under a parent requirement.
        
        Args:
            org: GitHub organization name (uses GITHUB_ORG env var if not provided)
            project_id: GitHub project number
            parent_task_number: Parent requirement issue number
            parent_task_id: Parent requirement issue ID (alternative to parent_task_number)
            title: Test case title
            description: Test case description
            test_steps: Test steps (will be included in the body)
            expected_result: Expected result (will be included in the body)
            assignees: List of assignee usernames
            labels: List of label names (e.g., ["test case"])
            status: Status field value (e.g., "To do", "In progress")
            test_type: Test type custom field value (e.g., "Unit Test")
            platforms: Platforms of test custom field value
            test_database: Test database custom field value
            test_id: Test ID custom field value
        
        Returns:
            Dictionary containing created test case information
        """
        if not self.manager:
            self.initialize()
        
        # Get organization from argument or environment variable
        org = org or os.getenv('GITHUB_ORG')
        if not org:
            raise ValueError("GitHub organization is required. Provide 'org' parameter or set GITHUB_ORG environment variable.")
        
        if not project_id:
            raise ValueError("project_id is required.")
        
        if not parent_task_number and not parent_task_id:
            raise ValueError("Either parent_task_number or parent_task_id must be provided")
        
        if not title:
            raise ValueError("title is required.")
        
        # Get project information
        project_info = self.manager.get_project_by_number(org, project_id)
        
        # Get all project items to find parent task and repository info
        items = self.manager.get_all_project_items(project_info['id'])
        parsed_items = [self.manager.parse_item_data(item) for item in items]
        
        # Find the parent task
        parent_task = None
        if parent_task_number:
            parent_task = next((item for item in parsed_items if item.get('number') == parent_task_number), None)
        elif parent_task_id:
            parent_task = next((item for item in parsed_items if item['id'] == parent_task_id), None)
        
        if not parent_task:
            raise ValueError(f"Parent task not found in project (task_id={parent_task_id}, task_number={parent_task_number})")
        
        # Extract repository information from parent task
        if not parent_task.get('repository'):
            raise ValueError("Parent task must be an issue in a repository (not a draft issue)")
        
        repo_parts = parent_task['repository'].split('/')
        if len(repo_parts) != 2:
            raise ValueError(f"Invalid repository format: {parent_task['repository']}")
        
        owner, repo = repo_parts
        
        # Build test case body
        body_parts = []
        
        if description:
            body_parts.append(description)
            body_parts.append("")
        
        body_parts.append("### Test case Steps")
        body_parts.append("")
        
        if test_steps:
            body_parts.append("#### Test steps :")
            body_parts.append("")
            body_parts.append(test_steps)
            body_parts.append("")
        
        if expected_result:
            body_parts.append("**Expected result:**")
            body_parts.append("")
            body_parts.append(expected_result)
        
        body = "\n".join(body_parts)
        
        # Get assignee IDs if provided
        assignee_ids = []
        if assignees:
            for username in assignees:
                user_id = self.manager.get_user_id(username)
                if user_id:
                    assignee_ids.append(user_id)
        
        # Get label IDs if provided
        label_ids = []
        if labels:
            label_ids = self.manager.get_label_ids(owner, repo, labels)
        
        # Create the issue
        issue = self.manager.create_issue(
            owner=owner,
            repo=repo,
            title=title,
            body=body,
            assignee_ids=assignee_ids if assignee_ids else None,
            label_ids=label_ids if label_ids else None,
            parent_issue_id=parent_task['id']
        )
        
        # Add issue to project
        project_item = self.manager.add_issue_to_project(project_info['id'], issue['id'])
        
        # Update custom project fields
        custom_fields = {}
        if status:
            custom_fields['Status'] = status
        if test_type:
            custom_fields['Test type'] = test_type
        if platforms:
            custom_fields['Plateforms of Test'] = platforms
        if test_database:
            custom_fields['Test database'] = test_database
        if test_id:
            custom_fields['Test ID'] = test_id
        
        for field_name, field_value in custom_fields.items():
            field_id = self.manager.get_field_id_by_name(project_info['id'], field_name)
            if field_id:
                self.manager.update_project_field(
                    project_id=project_info['id'],
                    item_id=project_item['id'],
                    field_id=field_id,
                    value={'text': field_value}
                )
        
        return {
            'success': True,
            'issue': {
                'id': issue['id'],
                'number': issue['number'],
                'title': issue['title'],
                'url': issue['url'],
                'state': issue['state'],
                'body': issue['body']
            },
            'parent_task': {
                'id': parent_task['id'],
                'number': parent_task['number'],
                'title': parent_task['title']
            },
            'project_item_id': project_item['id'],
            'custom_fields_set': list(custom_fields.keys())
        }


def create_mcp_server():
    """Create and configure the MCP server with tool definitions."""
    
    server = GitHubProjectMCPServer()
    
    # MCP Server metadata
    server_info = {
        "name": "github-project-tasks",
        "version": "1.1.0",
        "description": "MCP server for querying and managing GitHub Projects with filtering capabilities"
    }
    
    # Tool definitions following MCP specification
    tools = [
        {
            "name": "get_project_tasks_full",
            "description": "Get all tasks from a GitHub project. Supports filtering by label, status, assignee, and item type. Returns complete list of tasks with all their metadata including assignees, labels, status, parent/child relationships, and custom project fields.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "org": {
                        "type": "string",
                        "description": "GitHub organization name (e.g., '4d'). If not provided, uses GITHUB_ORG environment variable."
                    },
                    "project_id": {
                        "type": "integer",
                        "description": "GitHub project number (e.g., 745 from the project URL)"
                    },
                    "label": {
                        "type": "string",
                        "description": "Filter tasks by label name (case-insensitive, optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter tasks by status field value like 'In Progress', 'Done', etc. (case-insensitive, optional)"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter tasks by assignee username (optional)"
                    },
                    "item_type": {
                        "type": "string",
                        "enum": ["issue", "pull_request", "draft_issue"],
                        "description": "Filter by item type (optional)"
                    }
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "get_child_tasks",
            "description": "Get all child tasks (sub-issues) of a specific parent task. Supports filtering child tasks by label, status, and assignee. Useful for exploring task hierarchies and dependencies.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "org": {
                        "type": "string",
                        "description": "GitHub organization name (e.g., '4d'). If not provided, uses GITHUB_ORG environment variable."
                    },
                    "project_id": {
                        "type": "integer",
                        "description": "GitHub project number (e.g., 745 from the project URL)"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "GitHub task/issue ID (optional, either this or task_number is required)"
                    },
                    "task_number": {
                        "type": "integer",
                        "description": "GitHub issue number like #123 (optional, either this or task_id is required)"
                    },
                    "label": {
                        "type": "string",
                        "description": "Filter child tasks by label name (case-insensitive, optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter child tasks by status field value (case-insensitive, optional)"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter child tasks by assignee username (optional)"
                    }
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "get_task_info",
            "description": "Get detailed information about a specific task including title, description, state, assignees, labels, parent task, sub-issues, project fields, URLs, and timestamps. Use this to get complete context about a single task.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "org": {
                        "type": "string",
                        "description": "GitHub organization name (e.g., '4d'). If not provided, uses GITHUB_ORG environment variable."
                    },
                    "project_id": {
                        "type": "integer",
                        "description": "GitHub project number (e.g., 745 from the project URL)"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "GitHub task/issue ID (optional, either this or task_number is required)"
                    },
                    "task_number": {
                        "type": "integer",
                        "description": "GitHub issue number like #123 (optional, either this or task_id is required)"
                    }
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "create_test_case_task",
            "description": "Create a test case task under a parent requirement in a GitHub project. This creates a new issue linked as a sub-issue to the parent requirement, adds it to the project, and sets custom fields like test type, platforms, test database, and test ID.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "org": {
                        "type": "string",
                        "description": "GitHub organization name (e.g., '4d'). If not provided, uses GITHUB_ORG environment variable."
                    },
                    "project_id": {
                        "type": "integer",
                        "description": "GitHub project number (e.g., 745 from the project URL)"
                    },
                    "parent_task_number": {
                        "type": "integer",
                        "description": "Parent requirement issue number (optional, either this or parent_task_id is required)"
                    },
                    "parent_task_id": {
                        "type": "string",
                        "description": "Parent requirement issue ID (optional, either this or parent_task_number is required)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Test case title (required)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Test case description (optional)"
                    },
                    "test_steps": {
                        "type": "string",
                        "description": "Test steps to perform (optional, will be formatted in the issue body)"
                    },
                    "expected_result": {
                        "type": "string",
                        "description": "Expected result of the test (optional, will be formatted in the issue body)"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of assignee usernames (optional)"
                    },
                    "labels": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of label names (e.g., ['test case']) (optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Status field value (e.g., 'To do', 'In progress') (optional)"
                    },
                    "test_type": {
                        "type": "string",
                        "description": "Test type custom field value (e.g., 'Unit Test', 'Integration Test') (optional)"
                    },
                    "platforms": {
                        "type": "string",
                        "description": "Platforms of test custom field value (e.g., 'macOS & Win & QodlyServer') (optional)"
                    },
                    "test_database": {
                        "type": "string",
                        "description": "Test database custom field value (e.g., '4DAIKitTest') (optional)"
                    },
                    "test_id": {
                        "type": "string",
                        "description": "Test ID custom field value (e.g., 'test_openai_chat_tools') (optional)"
                    }
                },
                "required": ["project_id", "title"]
            }
        }
    ]
    
    return server, server_info, tools


def handle_tool_call(server: GitHubProjectMCPServer, tool_name: str, arguments: Dict) -> Dict:
    """Handle a tool call and return the result."""
    try:
        if tool_name == "get_project_tasks_full":
            result = server.get_project_tasks_full(**arguments)
        elif tool_name == "get_child_tasks":
            result = server.get_child_tasks(**arguments)
        elif tool_name == "get_task_info":
            result = server.get_task_info(**arguments)
        elif tool_name == "create_test_case_task":
            result = server.create_test_case_task(**arguments)
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "isError": True
            }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, default=str)
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ],
            "isError": True
        }


def main():
    """Main entry point for the MCP server using stdio transport."""
    import sys
    
    # Check for GitHub token before starting the server
    # Try to load .env file if dotenv is available
    env_loaded = False
    env_path = None
    if DOTENV_AVAILABLE:
        # Debug: print search paths
        print(f"🔍 Searching for .env file...", file=sys.stderr)
        print(f"   Current working directory: {Path.cwd()}", file=sys.stderr)
        print(f"   Script directory: {Path(__file__).parent}", file=sys.stderr)
        print(f"   Parent directory: {Path(__file__).parent.parent}", file=sys.stderr)
        
        env_path = Path.cwd() / '.env'
        if env_path.exists():
            print(f"✅ Loading .env from: {env_path}", file=sys.stderr)
            load_dotenv(env_path, override=True)
            env_loaded = True
        else:
            print(f"   ❌ Not found: {env_path}", file=sys.stderr)
            script_dir = Path(__file__).parent
            env_path = script_dir / '.env'
            if env_path.exists():
                print(f"✅ Loading .env from: {env_path}", file=sys.stderr)
                load_dotenv(env_path, override=True)
                env_loaded = True
            else:
                print(f"   ❌ Not found: {env_path}", file=sys.stderr)
                # Try parent directory of script (project root)
                env_path = script_dir.parent / '.env'
                if env_path.exists():
                    print(f"✅ Loading .env from: {env_path}", file=sys.stderr)
                    load_dotenv(env_path, override=True)
                    env_loaded = True
                else:
                    print(f"   ❌ Not found: {env_path}", file=sys.stderr)
    else:
        print(f"⚠️  python-dotenv not available, relying on environment variables", file=sys.stderr)
    
    # Check if token is available
    token = os.getenv('GITHUB_TOKEN')
    
    # Debug output
    print(f"\n🔑 Checking GITHUB_TOKEN environment variable...", file=sys.stderr)
    if token:
        print(f"   ✅ Token found: {token[:10]}... (length: {len(token)})", file=sys.stderr)
    else:
        print(f"   ❌ Token not found in environment", file=sys.stderr)
    
    if env_loaded and not token:
        print(f"⚠️  Warning: .env file was loaded but GITHUB_TOKEN is empty", file=sys.stderr)
        print(f"    .env file location: {env_path}", file=sys.stderr)
        print(f"    File exists: {env_path.exists()}", file=sys.stderr)
        print(f"    File content preview:", file=sys.stderr)
        try:
            with open(env_path, 'r') as f:
                content = f.read()
                print(f"    Length: {len(content)} chars", file=sys.stderr)
                print(f"    Lines: {content.splitlines()}", file=sys.stderr)
        except Exception as e:
            print(f"    Could not read file: {e}", file=sys.stderr)
    
    if not token:
        print("=" * 80, file=sys.stderr)
        print("❌ ERROR: GitHub token not found!", file=sys.stderr)
        print("", file=sys.stderr)
        print("To use this MCP server, you need to provide a GitHub token:", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 1: Create a .env file in the project directory:", file=sys.stderr)
        print("  GITHUB_TOKEN=your_github_token_here", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 2: Set the GITHUB_TOKEN environment variable:", file=sys.stderr)
        print("  export GITHUB_TOKEN=your_github_token_here", file=sys.stderr)
        print("", file=sys.stderr)
        print("To create a token:", file=sys.stderr)
        print("  1. Go to GitHub Settings → Developer settings → Personal access tokens", file=sys.stderr)
        print("  2. Generate a new token with 'repo' and 'project' scopes", file=sys.stderr)
        print("", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        sys.exit(1)
    
    server, server_info, tools = create_mcp_server()
    
    # MCP uses JSON-RPC over stdio
    # Read from stdin, write to stdout
    # This is a simplified implementation - a full MCP server would use the official SDK
    
    print(f"✅ GitHub Project Tasks MCP Server v{server_info['version']}", file=sys.stderr)
    print(f"Description: {server_info['description']}", file=sys.stderr)
    print(f"Available tools: {len(tools)}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Tools:", file=sys.stderr)
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Ready to accept MCP requests via stdio", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    
    # For testing purposes, we can also provide a simple CLI interface
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("\n🧪 Test Mode - Demonstrating tool usage\n", file=sys.stderr)
        
        # Example: Get all tasks
        print("Example 1: Get all project tasks", file=sys.stderr)
        print("Tool: get_project_tasks_full", file=sys.stderr)
        print("Arguments: {'org': '4d', 'project_id': 745}", file=sys.stderr)
        print("", file=sys.stderr)
        
        # Example: Get child tasks
        print("Example 2: Get child tasks of issue #123", file=sys.stderr)
        print("Tool: get_child_tasks", file=sys.stderr)
        print("Arguments: {'org': '4d', 'project_id': 745, 'task_number': 123}", file=sys.stderr)
        print("", file=sys.stderr)
        
        # Example: Get task info
        print("Example 3: Get detailed task information", file=sys.stderr)
        print("Tool: get_task_info", file=sys.stderr)
        print("Arguments: {'org': '4d', 'project_id': 745, 'task_number': 123}", file=sys.stderr)
        print("", file=sys.stderr)
    else:
        # Simple stdin/stdout handler for MCP protocol
        # In production, you would use the official MCP SDK
        try:
            for line in sys.stdin:
                if not line.strip():
                    continue
                
                try:
                    request = json.loads(line)
                    
                    if request.get("method") == "tools/list":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "tools": tools
                            }
                        }
                        print(json.dumps(response), flush=True)
                    
                    elif request.get("method") == "tools/call":
                        params = request.get("params", {})
                        tool_name = params.get("name")
                        arguments = params.get("arguments", {})
                        
                        result = handle_tool_call(server, tool_name, arguments)
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": result
                        }
                        print(json.dumps(response), flush=True)
                    
                    elif request.get("method") == "initialize":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {
                                    "tools": {}
                                },
                                "serverInfo": server_info
                            }
                        }
                        print(json.dumps(response), flush=True)
                    
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {request.get('method')}"
                            }
                        }
                        print(json.dumps(response), flush=True)
                
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"Error processing request: {e}", file=sys.stderr)
        
        except KeyboardInterrupt:
            print("\nShutting down MCP server", file=sys.stderr)
            sys.exit(0)


if __name__ == "__main__":
    main()
