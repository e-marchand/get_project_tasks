# GitHub Project Tasks MCP Server

A Model Context Protocol (MCP) server that provides tools for querying GitHub Projects with advanced filtering capabilities.

## Overview

This MCP server exposes three powerful tools for interacting with GitHub Projects:

1. **get_project_tasks_full** - Retrieve all tasks from a project with optional filtering
2. **get_child_tasks** - Get child tasks (sub-issues) of a specific parent task
3. **get_task_info** - Get detailed information about a specific task

All tools support filtering by **label**, **status**, and **assignee**.

## Features

- ✅ Full GitHub Projects V2 API support
- 🔍 Advanced filtering by label, status, assignee, and item type
- 🌲 Parent-child task relationship tracking
- 📊 Complete task metadata including custom project fields
- 🔐 Secure authentication via GitHub Personal Access Token
- 🚀 Fast pagination handling for large projects

## Installation

### Prerequisites

- Python 3.7 or higher
- GitHub Personal Access Token with `repo` and `project` permissions

### Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set your GitHub token:**

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Or create a `.env` file:

```bash
echo "GITHUB_TOKEN=ghp_your_token_here" > .env
```

3. **Make the server executable:**

```bash
chmod +x mcp_server.py
```

## MCP Configuration

### For Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github-project-tasks": {
      "command": "python3",
      "args": [
        "/absolute/path/to/get_project_tasks/mcp_server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

### For Other MCP Clients

The server communicates via JSON-RPC over stdio, following the MCP specification. Point your MCP client to run:

```bash
python3 mcp_server.py
```

## Tools Reference

### 1. get_project_tasks_full

Get all tasks from a GitHub project with optional filtering.

**Parameters:**
- `org` (required): GitHub organization name (e.g., "4d")
- `project_id` (required): GitHub project number (e.g., 745)
- `label` (optional): Filter by label name (case-insensitive)
- `status` (optional): Filter by status field value (e.g., "In Progress", "Done")
- `assignee` (optional): Filter by assignee username
- `item_type` (optional): Filter by type ("issue", "pull_request", or "draft_issue")

**Returns:**
```json
{
  "project": {
    "id": "PVT_...",
    "title": "Project Name",
    "description": "Project description",
    "url": "https://github.com/orgs/org/projects/123",
    "closed": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-10-01T00:00:00Z"
  },
  "total_count": 42,
  "filters_applied": {"status": "In Progress"},
  "tasks": [
    {
      "id": "I_...",
      "type": "issue",
      "title": "Task title",
      "body": "Task description",
      "url": "https://github.com/org/repo/issues/123",
      "state": "open",
      "author": "username",
      "assignees": ["user1", "user2"],
      "labels": [{"name": "bug", "color": "d73a4a"}],
      "repository": "org/repo",
      "number": 123,
      "parent": null,
      "sub_issues": [],
      "sub_issues_summary": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-10-01T00:00:00Z",
      "project_fields": {
        "Status": "In Progress",
        "Priority": "High"
      }
    }
  ]
}
```

**Example Usage:**
```
Get all open issues with label "bug" assigned to "john":
- org: "4d"
- project_id: 745
- label: "bug"
- assignee: "john"
- item_type: "issue"
```

### 2. get_child_tasks

Get all child tasks (sub-issues) of a specific parent task.

**Parameters:**
- `org` (required): GitHub organization name
- `project_id` (required): GitHub project number
- `task_id` (optional): GitHub task ID (either this or task_number required)
- `task_number` (optional): GitHub issue number (either this or task_id required)
- `label` (optional): Filter child tasks by label
- `status` (optional): Filter child tasks by status
- `assignee` (optional): Filter child tasks by assignee

**Returns:**
```json
{
  "parent_task": {
    "id": "I_...",
    "title": "Parent task",
    "number": 123,
    "sub_issues_summary": {
      "total": 5,
      "completed": 3,
      "percentCompleted": 60
    }
  },
  "total_children": 5,
  "filters_applied": {},
  "child_tasks": [
    {
      "id": "I_...",
      "title": "Child task 1",
      "parent": {
        "id": "I_...",
        "title": "Parent task",
        "number": 123
      }
    }
  ]
}
```

**Example Usage:**
```
Get all child tasks of issue #123 that are in "Done" status:
- org: "4d"
- project_id: 745
- task_number: 123
- status: "Done"
```

### 3. get_task_info

Get detailed information about a specific task.

**Parameters:**
- `org` (required): GitHub organization name
- `project_id` (required): GitHub project number
- `task_id` (optional): GitHub task ID (either this or task_number required)
- `task_number` (optional): GitHub issue number (either this or task_id required)

**Returns:**
```json
{
  "project": {
    "id": "PVT_...",
    "title": "Project Name",
    "url": "https://github.com/orgs/org/projects/123"
  },
  "task": {
    "id": "I_...",
    "type": "issue",
    "title": "Task title",
    "body": "Full task description with all details...",
    "url": "https://github.com/org/repo/issues/123",
    "state": "open",
    "author": "username",
    "assignees": ["user1", "user2"],
    "labels": [
      {"name": "bug", "color": "d73a4a"},
      {"name": "priority:high", "color": "ff0000"}
    ],
    "repository": "org/repo",
    "number": 123,
    "parent": {
      "id": "I_...",
      "title": "Parent task",
      "number": 100
    },
    "sub_issues": [
      {"id": "I_...", "title": "Sub-task 1", "number": 124},
      {"id": "I_...", "title": "Sub-task 2", "number": 125}
    ],
    "sub_issues_summary": {
      "total": 2,
      "completed": 1,
      "percentCompleted": 50
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-10-01T00:00:00Z",
    "project_fields": {
      "Status": "In Progress",
      "Priority": "High",
      "Iteration": "Sprint 5",
      "Size": 8
    }
  }
}
```

**Example Usage:**
```
Get complete information about issue #123:
- org: "4d"
- project_id: 745
- task_number: 123
```

## Testing

### Test Mode

Run the server in test mode to see example tool usage:

```bash
python3 mcp_server.py test
```

### Manual Testing

You can test the tools directly in Python:

```python
from mcp_server import GitHubProjectMCPServer
import os

# Initialize server
server = GitHubProjectMCPServer()
server.initialize(token=os.getenv('GITHUB_TOKEN'))

# Get all project tasks
result = server.get_project_tasks_full(
    org="4d",
    project_id=745,
    status="In Progress"
)
print(f"Found {result['total_count']} tasks")

# Get child tasks
children = server.get_child_tasks(
    org="4d",
    project_id=745,
    task_number=123
)
print(f"Task has {children['total_children']} children")

# Get task info
info = server.get_task_info(
    org="4d",
    project_id=745,
    task_number=123
)
print(f"Task: {info['task']['title']}")
```

## Use Cases

### 1. Project Status Overview
Get all tasks filtered by status to see what's in progress:
```
get_project_tasks_full(org="4d", project_id=745, status="In Progress")
```

### 2. Bug Tracking
Find all bugs assigned to a specific developer:
```
get_project_tasks_full(
    org="4d",
    project_id=745,
    label="bug",
    assignee="developer_username"
)
```

### 3. Sprint Planning
Get all tasks in a specific iteration/sprint:
```
get_project_tasks_full(org="4d", project_id=745, status="Sprint 5")
```

### 4. Task Hierarchy Exploration
Explore parent-child relationships:
```
# Get parent task
parent = get_task_info(org="4d", project_id=745, task_number=100)

# Get its children
children = get_child_tasks(org="4d", project_id=745, task_number=100)
```

### 5. Quality Assurance
Find all test-related tasks:
```
get_project_tasks_full(org="4d", project_id=745, label="test")
```

## Troubleshooting

### Authentication Errors

**Error:** "GitHub token is required"
- **Solution:** Set the `GITHUB_TOKEN` environment variable or pass it in the configuration

### Permission Errors

**Error:** "403 Forbidden" or "Resource not accessible"
- **Solution:** Ensure your token has `repo` and `project` (read) permissions
- Go to GitHub Settings → Developer Settings → Personal Access Tokens
- Create a new token with the required scopes

### Project Not Found

**Error:** "Project X not found in organization Y"
- **Solution:** 
  - Verify the project number in the URL: `github.com/orgs/ORG/projects/NUMBER`
  - Ensure your token has access to the organization
  - Check that the project is not private (or that you have access)

### Rate Limiting

**Error:** "API rate limit exceeded"
- **Solution:** 
  - Wait for the rate limit to reset (shown in error message)
  - Use a Personal Access Token (higher rate limits than unauthenticated requests)
  - Consider caching results for frequently accessed projects

## Architecture

The MCP server is built on top of the existing `get_project_tasks.py` script, leveraging:

- **GitHubProjectManager**: Handles GitHub GraphQL API communication
- **Filtering System**: Supports label, status, assignee, and type filters
- **Data Parser**: Converts raw GitHub API responses to structured format
- **Relationship Tracker**: Maintains parent-child task relationships

## Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add caching layer for better performance
- [ ] Support for GitHub Projects Classic (V1)
- [ ] Webhook support for real-time updates
- [ ] Additional filters (date ranges, milestones, etc.)
- [ ] Batch operations for bulk updates
- [ ] Export to different formats (CSV, Excel, etc.)

## License

MIT License - See LICENSE file for details

## Related Projects

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- Original script: `get_project_tasks.py`

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
