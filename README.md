# GitHub Project Tasks Retriever

A powerful Python script to retrieve, filter, and visualize tasks from GitHub Projects (V2) using GitHub's GraphQL API.

## 🆕 NEW: MCP Server Available!

This project now includes a **Model Context Protocol (MCP) server** that can be used with Claude Desktop and other MCP-compatible clients! 

**→ See [mcp/README.md](mcp/README.md) for complete MCP server documentation.**
## Features

- 📊 **Multiple Output Formats**: Display tasks as tables, trees, JSON, or grouped by status
- 🔍 **Advanced Filtering**: Filter by type, status, assignee, or labels
- 🌲 **Tree View**: Visualize task relationships and dependencies
- 📋 **Task Management**: View issues, pull requests, and draft issues
- 🔄 **Pagination Support**: Automatically handles large projects
- 📝 **Detailed Information**: Access task descriptions, assignees, labels, and custom fields
- 🤖 **MCP Server**: Use with Claude Desktop or other MCP clients for AI-powered project management

## Requirements

- Python 3.7+
- GitHub Personal Access Token with `repo` and `project` permissions

## Installation

1. Clone this repository or download the script:
```bash
git clone <repository-url>
cd get_project_tasks
```

2. Install required dependencies:
```bash
pip install requests tabulate
```

Or using a requirements file:
```bash
pip install -r requirements.txt
```

3. Set up your GitHub token (see [GitHub Token Setup](#github-token-setup) below):
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your GitHub token
# GITHUB_TOKEN=your_github_token_here
```

**⚠️ Security Note**: Never commit your `.env` file or expose your GitHub token in code. The `.gitignore` file is configured to exclude `.env` automatically.

## Usage

### Basic Usage

```bash
python get_project_tasks.py --token <your-github-token> --org <organization> --project-id <project-number>
```

### Using Environment Variable

Set your GitHub token as an environment variable:
```bash
export GITHUB_TOKEN=ghp_your_token_here
python get_project_tasks.py --org 4d --project-id 745
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--token` | GitHub Personal Access Token (or use `GITHUB_TOKEN` env var) |
| `--org` | GitHub organization name (required) |
| `--project-id` | GitHub project number (required) |
| `--type` | Filter by type: `issue`, `pull_request`, or `draft_issue` |
| `--status` | Filter by status field value (case-insensitive) |
| `--assignee` | Filter by assignee username |
| `--label` | Filter by label name (case-insensitive) |
| `--show-description` | Show task description/body content in output |
| `--tree` | Display results as a tree structure showing relationships |
| `--group-by-status` | Group results by status |
| `--output` | Output format: `table`, `tree`, `json`, or `status-groups` |
| `--quiet` | Suppress progress messages |

## Examples

### View all tasks in a table format
```bash
python get_project_tasks.py --org 4d --project-id 745
```

### Filter by issue type
```bash
python get_project_tasks.py --org 4d --project-id 745 --type issue
```

### Show task relationships as a tree
```bash
python get_project_tasks.py --org 4d --project-id 745 --tree
```

### Group tasks by status
```bash
python get_project_tasks.py --org 4d --project-id 745 --group-by-status
```

### Filter by status and assignee
```bash
python get_project_tasks.py --org 4d --project-id 745 --status "In Progress" --assignee username
```

### Filter by label
```bash
python get_project_tasks.py --org 4d --project-id 745 --label bug
```

### Export to JSON
```bash
python get_project_tasks.py --org 4d --project-id 745 --output json > project_tasks.json
```

### Show task descriptions
```bash
python get_project_tasks.py --org 4d --project-id 745 --show-description
```

## Output Formats

### Table Format (Default)
Displays tasks in a clean, readable table with columns for type, title, status, assignees, and more.

### Tree Format
Shows task relationships and hierarchies, visualizing parent-child dependencies between issues.

### Status Groups Format
Groups all tasks by their status field, making it easy to see what's in each stage of your workflow.

### JSON Format
Exports complete project data including all task details and metadata for programmatic processing.

## GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name
4. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `project` (Full control of projects)
5. Click "Generate token" and copy it immediately
6. Use the token with the `--token` flag or set it as `GITHUB_TOKEN` environment variable

## Finding Your Project ID

The project ID is the number in your GitHub project URL:
```
https://github.com/orgs/YOUR-ORG/projects/745
                                              ^^^
                                         This is your project ID
```

## API Details

This script uses GitHub's GraphQL API (V4) to:
- Retrieve project metadata and structure
- Fetch all project items with pagination
- Access custom project fields
- Query issue/PR relationships and sub-issues
- Filter and organize data efficiently

## Error Handling

The script includes comprehensive error handling for:
- Invalid tokens or insufficient permissions
- Non-existent projects or organizations
- API rate limiting
- Network issues
- Invalid filter combinations

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on the GitHub repository.
