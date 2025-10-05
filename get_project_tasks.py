#!/usr/bin/env python3
"""
GitHub Project Tasks Retriever
A script to retrieve all tasks from a GitHub project with filtering and tree view capabilities.

This script uses GitHub's GraphQL API to fetch project data and can:
- Filter tasks by type (issue, pull request, draft issue)
- Display results in tree format
- Export to various formats (JSON, table)

Dependencies:
- requests>=2.28.0
- tabulate>=0.9.0 (optional, only required for table output format)

Usage:
    python get_project_tasks.py --token <github_token> --org <organization> --project-id <project_id>
    python get_project_tasks.py --token <github_token> --org 4d --project-id 745 --type issue
    python get_project_tasks.py --token <github_token> --org 4d --project-id 745 --tree
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Any
import requests

# Make tabulate optional - only required for table output format
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    tabulate = None


class GitHubProjectManager:
    def __init__(self, token: str):
        """Initialize with GitHub Personal Access Token."""
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v4+json',  # GraphQL API
            'Content-Type': 'application/json'
        })
        self.graphql_url = 'https://api.github.com/graphql'
    
    def execute_graphql_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute a GraphQL query against GitHub's API."""
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        response = self.session.post(self.graphql_url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data.get('data', {})
    
    def get_project_by_number(self, org: str, project_number: int) -> Dict:
        """Get project information by organization and project number."""
        query = """
        query GetProject($org: String!, $projectNumber: Int!) {
            organization(login: $org) {
                projectV2(number: $projectNumber) {
                    id
                    title
                    shortDescription
                    public
                    closed
                    createdAt
                    updatedAt
                    url
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                                dataType
                            }
                            ... on ProjectV2IterationField {
                                id
                                name
                                dataType
                                configuration {
                                    iterations {
                                        startDate
                                        id
                                        title
                                    }
                                }
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                dataType
                                options {
                                    id
                                    name
                                    color
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'org': org,
            'projectNumber': project_number
        }
        
        result = self.execute_graphql_query(query, variables)
        project = result.get('organization', {}).get('projectV2')
        
        if not project:
            raise Exception(f"Project {project_number} not found in organization {org}")
        
        return project
    
    def get_project_items(self, project_id: str, first: int = 100, after: str = None) -> Dict:
        """Get items from a project with pagination."""
        query = """
        query GetProjectItems($projectId: ID!, $first: Int!, $after: String) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    items(first: $first, after: $after) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        nodes {
                            id
                            type
                            createdAt
                            updatedAt
                            isArchived
                            content {
                                ... on Issue {
                                    id
                                    number
                                    title
                                    body
                                    state
                                    closed
                                    createdAt
                                    updatedAt
                                    url
                                    author {
                                        login
                                    }
                                    assignees(first: 10) {
                                        nodes {
                                            login
                                        }
                                    }
                                    labels(first: 10) {
                                        nodes {
                                            name
                                            color
                                        }
                                    }
                                    repository {
                                        name
                                        owner {
                                            login
                                        }
                                    }
                                    parent {
                                        id
                                        title
                                        number
                                    }
                                    subIssues(first: 50) {
                                        nodes {
                                            id
                                            title
                                            number
                                        }
                                    }
                                    subIssuesSummary {
                                        total
                                        completed
                                        percentCompleted
                                    }
                                }
                                ... on PullRequest {
                                    id
                                    number
                                    title
                                    body
                                    state
                                    closed
                                    merged
                                    createdAt
                                    updatedAt
                                    url
                                    author {
                                        login
                                    }
                                    assignees(first: 10) {
                                        nodes {
                                            login
                                        }
                                    }
                                    labels(first: 10) {
                                        nodes {
                                            name
                                            color
                                        }
                                    }
                                    repository {
                                        name
                                        owner {
                                            login
                                        }
                                    }
                                }
                                ... on DraftIssue {
                                    id
                                    title
                                    body
                                    createdAt
                                    updatedAt
                                    creator {
                                        login
                                    }
                                    assignees(first: 10) {
                                        nodes {
                                            login
                                        }
                                    }
                                }
                            }
                            fieldValues(first: 20) {
                                nodes {
                                    ... on ProjectV2ItemFieldTextValue {
                                        text
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                    }
                                    ... on ProjectV2ItemFieldNumberValue {
                                        number
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                    }
                                    ... on ProjectV2ItemFieldSingleSelectValue {
                                        name
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                    }
                                    ... on ProjectV2ItemFieldDateValue {
                                        date
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                    }
                                    ... on ProjectV2ItemFieldIterationValue {
                                        title
                                        startDate
                                        duration
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'projectId': project_id,
            'first': first
        }
        
        if after:
            variables['after'] = after
        
        return self.execute_graphql_query(query, variables)
    
    def get_all_project_items(self, project_id: str) -> List[Dict]:
        """Get all items from a project, handling pagination."""
        all_items = []
        has_next_page = True
        after = None
        
        while has_next_page:
            result = self.get_project_items(project_id, first=100, after=after)
            project_data = result.get('node', {})
            items_data = project_data.get('items', {})
            
            items = items_data.get('nodes', [])
            all_items.extend(items)
            
            page_info = items_data.get('pageInfo', {})
            has_next_page = page_info.get('hasNextPage', False)
            after = page_info.get('endCursor')
        
        return all_items
    
    def filter_items(self, items: List[Dict], filters: Dict) -> List[Dict]:
        """Filter items based on provided criteria."""
        filtered_items = []
        
        for item in items:
            content = item.get('content')
            if content is None:
                # Skip items with no content (archived or null items)
                continue
            
            # Filter by type
            if filters.get('type'):
                item_type = None
                if 'number' in content and 'repository' in content:
                    if content.get('merged') is not None:  # PullRequest has merged field
                        item_type = 'pull_request'
                    else:
                        item_type = 'issue'
                elif 'title' in content and 'creator' in content:
                    item_type = 'draft_issue'
                
                if filters['type'] != item_type:
                    continue
            
            # Filter by status (from field values)
            if filters.get('status'):
                status_found = False
                for field_value in item.get('fieldValues', {}).get('nodes', []):
                    field = field_value.get('field', {})
                    if field.get('name', '').lower() == 'status':
                        if field_value.get('name', '').lower() == filters['status'].lower():
                            status_found = True
                            break
                
                if filters['status'] and not status_found:
                    continue
            
            # Filter by assignee
            if filters.get('assignee'):
                assignees = []
                if 'assignees' in content:
                    assignees = [a['login'] for a in content['assignees'].get('nodes', [])]
                
                if filters['assignee'] not in assignees:
                    continue
            
            # Filter by label
            if filters.get('label'):
                labels = []
                if 'labels' in content:
                    labels = [l['name'].lower() for l in content['labels'].get('nodes', [])]
                
                # Case-insensitive label matching
                if filters['label'].lower() not in labels:
                    continue
            
            filtered_items.append(item)
        
        return filtered_items
    
    def parse_item_data(self, item: Dict) -> Dict:
        """Parse item data into a standardized format."""
        content = item.get('content')
        if content is None:
            content = {}
        
        parsed = {
            'id': item.get('id'),
            'type': 'unknown',
            'title': '',
            'body': '',
            'url': '',
            'state': '',
            'author': '',
            'assignees': [],
            'labels': [],
            'repository': '',
            'number': None,  # GitHub issue/PR number
            'parent': None,  # Parent issue information
            'sub_issues': [],  # List of sub-issues
            'sub_issues_summary': None,  # Summary of sub-issues
            'created_at': content.get('createdAt', '') if content else '',
            'updated_at': content.get('updatedAt', '') if content else '',
            'project_fields': {}
        }
        
        # Determine type and parse content
        if content and 'number' in content and 'repository' in content:
            if content.get('merged') is not None:
                parsed['type'] = 'pull_request'
                parsed['state'] = 'merged' if content.get('merged') else content.get('state', '')
            else:
                parsed['type'] = 'issue'
                parsed['state'] = content.get('state', '')
            
            parsed['title'] = content.get('title', '')
            parsed['body'] = content.get('body', '') or ''
            parsed['url'] = content.get('url', '')
            parsed['number'] = content.get('number')
            parsed['author'] = content.get('author', {}).get('login', '')
            parsed['assignees'] = [a['login'] for a in content.get('assignees', {}).get('nodes', [])]
            parsed['labels'] = [{'name': l['name'], 'color': l['color']} for l in content.get('labels', {}).get('nodes', [])]
            
            # Capture parent-child relationships
            if content.get('parent'):
                parsed['parent'] = {
                    'id': content['parent']['id'],
                    'title': content['parent'].get('title', ''),
                    'number': content['parent'].get('number')
                }
            
            if content.get('subIssues', {}).get('nodes'):
                parsed['sub_issues'] = [
                    {
                        'id': sub['id'],
                        'title': sub.get('title', ''),
                        'number': sub.get('number')
                    }
                    for sub in content['subIssues']['nodes']
                ]
            
            if content.get('subIssuesSummary'):
                parsed['sub_issues_summary'] = content['subIssuesSummary']
            
            repo = content.get('repository', {})
            owner = repo.get('owner', {}).get('login', '')
            repo_name = repo.get('name', '')
            parsed['repository'] = f"{owner}/{repo_name}" if owner and repo_name else ''
            
        elif content and 'title' in content and 'creator' in content:
            parsed['type'] = 'draft_issue'
            parsed['title'] = content.get('title', '')
            parsed['body'] = content.get('body', '') or ''
            parsed['author'] = content.get('creator', {}).get('login', '')
            parsed['assignees'] = [a['login'] for a in content.get('assignees', {}).get('nodes', [])]
        
        # Parse project fields
        for field_value in item.get('fieldValues', {}).get('nodes', []):
            field = field_value.get('field', {})
            field_name = field.get('name', '')
            
            if 'text' in field_value:
                parsed['project_fields'][field_name] = field_value['text']
            elif 'number' in field_value:
                parsed['project_fields'][field_name] = field_value['number']
            elif 'name' in field_value:
                parsed['project_fields'][field_name] = field_value['name']
            elif 'date' in field_value:
                parsed['project_fields'][field_name] = field_value['date']
            elif 'title' in field_value:  # Iteration field
                parsed['project_fields'][field_name] = field_value['title']
        
        return parsed
    
    def get_repository_id(self, owner: str, repo: str) -> str:
        """Get the GitHub repository ID."""
        query = """
        query GetRepositoryId($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                id
            }
        }
        """
        variables = {'owner': owner, 'repo': repo}
        result = self.execute_graphql_query(query, variables)
        return result['repository']['id']
    
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = None,
        assignee_ids: List[str] = None,
        label_ids: List[str] = None,
        parent_issue_id: str = None
    ) -> Dict:
        """
        Create a new issue in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body/description
            assignee_ids: List of user node IDs to assign
            label_ids: List of label node IDs to apply
            parent_issue_id: Parent issue node ID (to create sub-issue relationship)
        
        Returns:
            Created issue data
        """
        repo_id = self.get_repository_id(owner, repo)
        
        mutation = """
        mutation CreateIssue($input: CreateIssueInput!) {
            createIssue(input: $input) {
                issue {
                    id
                    number
                    title
                    url
                    body
                    state
                    author {
                        login
                    }
                    assignees(first: 10) {
                        nodes {
                            login
                        }
                    }
                    labels(first: 10) {
                        nodes {
                            name
                        }
                    }
                }
            }
        }
        """
        
        input_data = {
            'repositoryId': repo_id,
            'title': title
        }
        
        if body:
            input_data['body'] = body
        if assignee_ids:
            input_data['assigneeIds'] = assignee_ids
        if label_ids:
            input_data['labelIds'] = label_ids
        
        variables = {'input': input_data}
        result = self.execute_graphql_query(mutation, variables)
        issue = result['createIssue']['issue']
        
        # If parent issue is specified, create sub-issue relationship
        if parent_issue_id:
            self.link_as_sub_issue(parent_issue_id, issue['id'])
        
        return issue
    
    def link_as_sub_issue(self, parent_issue_id: str, child_issue_id: str):
        """Link an issue as a sub-issue of a parent issue."""
        mutation = """
        mutation LinkSubIssue($input: AddSubIssueInput!) {
            addSubIssue(input: $input) {
                subIssue {
                    id
                }
            }
        }
        """
        
        variables = {
            'input': {
                'issueId': parent_issue_id,
                'subIssueId': child_issue_id
            }
        }
        
        return self.execute_graphql_query(mutation, variables)
    
    def add_issue_to_project(self, project_id: str, issue_id: str) -> Dict:
        """Add an issue to a project."""
        mutation = """
        mutation AddProjectV2Item($input: AddProjectV2ItemByIdInput!) {
            addProjectV2ItemById(input: $input) {
                item {
                    id
                }
            }
        }
        """
        
        variables = {
            'input': {
                'projectId': project_id,
                'contentId': issue_id
            }
        }
        
        result = self.execute_graphql_query(mutation, variables)
        return result['addProjectV2ItemById']['item']
    
    def update_project_field(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        value: Any
    ):
        """Update a project field value."""
        mutation = """
        mutation UpdateProjectV2ItemFieldValue($input: UpdateProjectV2ItemFieldValueInput!) {
            updateProjectV2ItemFieldValue(input: $input) {
                projectV2Item {
                    id
                }
            }
        }
        """
        
        variables = {
            'input': {
                'projectId': project_id,
                'itemId': item_id,
                'fieldId': field_id,
                'value': value
            }
        }
        
        return self.execute_graphql_query(mutation, variables)
    
    def get_field_id_by_name(self, project_id: str, field_name: str) -> Optional[str]:
        """Get project field ID by field name."""
        query = """
        query GetProjectFields($projectId: ID!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    fields(first: 50) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {'projectId': project_id}
        result = self.execute_graphql_query(query, variables)
        
        fields = result.get('node', {}).get('fields', {}).get('nodes', [])
        for field in fields:
            if field.get('name') == field_name:
                return field['id']
        
        return None
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get GitHub user node ID by username."""
        query = """
        query GetUserId($username: String!) {
            user(login: $username) {
                id
            }
        }
        """
        
        variables = {'username': username}
        result = self.execute_graphql_query(query, variables)
        return result.get('user', {}).get('id')
    
    def get_label_ids(self, owner: str, repo: str, label_names: List[str]) -> List[str]:
        """Get label node IDs by names."""
        query = """
        query GetLabels($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                labels(first: 100) {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        
        variables = {'owner': owner, 'repo': repo}
        result = self.execute_graphql_query(query, variables)
        
        labels = result.get('repository', {}).get('labels', {}).get('nodes', [])
        label_ids = []
        
        for label_name in label_names:
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    label_ids.append(label['id'])
                    break
        
        return label_ids


def display_as_relationship_tree(items: List[Dict], project_info: Dict, show_description: bool = False):
    """Display items as a tree structure showing task relationships/dependencies."""
    print(f"\n🌲 Project Relationship Tree: {project_info['title']}")
    print(f"📄 Description: {project_info.get('shortDescription', 'N/A')}")
    print(f"🔗 URL: {project_info['url']}")
    if show_description:
        print("📝 Task descriptions will be shown")
    print("=" * 80)
    
    if not items:
        print("No items found matching the criteria.")
        return
    
    # Try to identify relationships between tasks
    relationships = build_task_relationships(items)
    
    if not relationships['roots'] and not relationships['orphans']:
        print("\n📋 No clear task relationships found. Displaying flat list:")
        display_flat_task_list(items, show_description)
        return
    
    # Display root tasks and their children
    if relationships['roots']:
        for root_id in relationships['roots']:
            root_task = next((item for item in items if item['id'] == root_id), None)
            if root_task:
                display_task_subtree(root_task, relationships['children'], items, level=0, show_description=show_description)
    
    # Display orphaned tasks (no clear parent/child relationship)
    if relationships['orphans']:
        print(f"\n📄 Independent Tasks ({len(relationships['orphans'])} items):")
        for orphan_id in relationships['orphans']:
            orphan_task = next((item for item in items if item['id'] == orphan_id), None)
            if orphan_task:
                display_single_task(orphan_task, prefix="├── ", show_description=show_description)
def display_as_table(items: List[Dict], project_info: Dict, show_description: bool = False):
    """Display items as a formatted table."""
    if not TABULATE_AVAILABLE:
        raise ImportError(
            "The 'tabulate' package is required for table output format.\n"
            "Install it with: pip install tabulate>=0.9.0\n"
            "Or use a different output format: --output json, --output tree, or --output status-groups"
        )
    
    print(f"\n🎯 Project: {project_info['title']}")
    print(f"📄 Description: {project_info.get('shortDescription', 'N/A')}")
    print(f"🔗 URL: {project_info['url']}")
    print(f"📊 Total items: {len(items)}")
    if show_description:
        print("📝 Task descriptions will be shown")
    print("=" * 80)
    
    if not items:
        print("No items found matching the criteria.")
        return
    
    # Prepare table data
    table_data = []
    headers = ['Type', 'Title', 'Repository', 'State', 'Author', 'Assignees', 'Status']
    if show_description:
        headers.append('Description')
    
    for item in items:
        assignees_str = ', '.join(item['assignees'][:3])  # Limit to first 3
        if len(item['assignees']) > 3:
            assignees_str += f" (+{len(item['assignees']) - 3})"
        
        status = item['project_fields'].get('Status', 'N/A')
        
        row = [
            item['type'].replace('_', ' ').title(),
            item['title'][:50] + ('...' if len(item['title']) > 50 else ''),
            item['repository'][:30] + ('...' if len(item['repository']) > 30 else ''),
            item['state'].title(),
            item['author'],
            assignees_str,
            status
        ]
        
        if show_description:
            description = item.get('body', '') or ''
            # Truncate long descriptions and replace newlines
            description = description.replace('\n', ' ').replace('\r', ' ')
            if len(description) > 100:
                description = description[:97] + '...'
            row.append(description or 'N/A')
        
        table_data.append(row)
    
    print(tabulate(table_data, headers=headers, tablefmt='grid'))


def display_as_status_groups(items: List[Dict], project_info: Dict, show_description: bool = False):
    """Display items grouped by status."""
    print(f"\n📊 Project Status Groups: {project_info['title']}")
    print(f"📄 Description: {project_info.get('shortDescription', 'N/A')}")
    print(f"🔗 URL: {project_info['url']}")
    if show_description:
        print("📝 Task descriptions will be shown")
    print("=" * 80)
    
    if not items:
        print("No items found matching the criteria.")
        return
    
    # Group items by status
    status_groups = {}
    for item in items:
        status = item['project_fields'].get('Status', 'No Status')
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(item)
    
    # Display tree
    for status, status_items in status_groups.items():
        print(f"\n📁 {status} ({len(status_items)} items)")
        
        for i, item in enumerate(status_items):
            is_last = i == len(status_items) - 1
            prefix = "└── " if is_last else "├── "
            
            display_single_task(item, prefix=prefix, show_description=show_description)


def build_task_relationships(items: List[Dict]) -> Dict:
    """Build task relationships using project-specific patterns and field matching."""
    relationships = {
        'children': {},  # parent_id -> [child_ids]
        'parents': {},   # child_id -> parent_id
        'roots': [],     # tasks that are parents but not children (root issues)
        'orphans': []    # tasks with no clear relationships
    }
    
    # Create lookup maps for items by their ID and by issue number  
    id_to_item = {item['id']: item for item in items}
    # Map issue numbers to project item IDs (for matching parent/child relationships)
    number_to_id = {item['number']: item['id'] for item in items if item.get('number')}
    
    # First, try GitHub's native parent-child relationships (for real issues)
    for item in items:
        item_id = item['id']
        
        # If this item has a parent, establish the relationship by matching issue numbers
        if item.get('parent') and item['parent'].get('number'):
            parent_number = item['parent']['number']
            parent_id = number_to_id.get(parent_number)
            
            # Only add relationship if the parent is also in our project items
            if parent_id:
                if parent_id not in relationships['children']:
                    relationships['children'][parent_id] = []
                if item_id not in relationships['children'][parent_id]:
                    relationships['children'][parent_id].append(item_id)
                relationships['parents'][item_id] = parent_id
        
        # If this item has sub-issues, establish those relationships
        if item.get('sub_issues'):
            for sub_issue in item['sub_issues']:
                sub_number = sub_issue.get('number')
                sub_id = number_to_id.get(sub_number) if sub_number else None
                
                # Only add relationship if the sub-issue is also in our project items
                if sub_id:
                    if item_id not in relationships['children']:
                        relationships['children'][item_id] = []
                    if sub_id not in relationships['children'][item_id]:
                        relationships['children'][item_id].append(sub_id)
                    # Only set parent if not already set (prefer explicit parent relationship)
                    if sub_id not in relationships['parents']:
                        relationships['parents'][sub_id] = item_id
    
    # For projects without native GitHub relationships, use project-specific patterns
    if not relationships['children'] and not relationships['parents']:
        # Separate requirements and test cases
        requirements = []  # Items with 'Acceptance' field
        test_cases = []    # Items with 'Test type' field
        others = []        # Other items
        
        for item in items:
            fields = item.get('project_fields', {})
            if 'Acceptance' in fields:
                requirements.append(item)
            elif 'Test type' in fields:
                test_cases.append(item)
            else:
                others.append(item)
        
        # Build relationships: Requirements as parents, Test cases as children
        for req in requirements:
            req_id = req['id']
            req_title = req['title'].lower()
            
            # Find related test cases by semantic matching
            related_tests = []
            for test in test_cases:
                test_title = test['title'].lower()
                
                # Try to match based on common keywords
                if test_title and req_title:
                    # Extract key terms from requirement title
                    req_terms = set(req_title.split())
                    test_terms = set(test_title.split())
                    
                    # Calculate overlap
                    common_terms = req_terms.intersection(test_terms)
                    significant_terms = [term for term in common_terms if len(term) > 3]
                    
                    # If there are significant matching terms, consider them related
                    if len(significant_terms) >= 1:
                        related_tests.append(test['id'])
            
            # Also group test cases by Test ID field
            test_id_groups = {}
            for test in test_cases:
                test_id = test.get('project_fields', {}).get('Test ID', '')
                if test_id:
                    if test_id not in test_id_groups:
                        test_id_groups[test_id] = []
                    test_id_groups[test_id].append(test['id'])
            
            # If we found related tests, establish relationships
            if related_tests:
                relationships['children'][req_id] = related_tests
                for test_id in related_tests:
                    relationships['parents'][test_id] = req_id
        
        # Group test cases by Test ID if no semantic relationships were found
        if not relationships['children'] and test_cases:
            test_id_groups = {}
            for test in test_cases:
                test_id = test.get('project_fields', {}).get('Test ID', '')
                if test_id:
                    if test_id not in test_id_groups:
                        test_id_groups[test_id] = []
                    test_id_groups[test_id].append(test)
            
            # Create virtual parent nodes for each test group
            for test_id, tests in test_id_groups.items():
                if len(tests) > 1:  # Only group if there are multiple tests
                    # Use the first test as the "parent" of the group
                    parent_test = tests[0]
                    parent_id = parent_test['id']
                    child_ids = [t['id'] for t in tests[1:]]
                    
                    if child_ids:
                        relationships['children'][parent_id] = child_ids
                        for child_id in child_ids:
                            relationships['parents'][child_id] = parent_id
    
    # Identify root tasks (items that have children but no parents within the project)
    # A task is a "root" if it has children AND no parent in the project
    for item in items:
        item_id = item['id']
        has_children_in_project = item_id in relationships['children']
        has_parent_in_project = item_id in relationships['parents']
        
        # Task is a root if it has actual children relationships established
        if has_children_in_project and not has_parent_in_project:
            relationships['roots'].append(item_id)
    
    # Identify orphans (items with no parent-child relationships in the project)
    for item in items:
        item_id = item['id']
        has_children_in_project = item_id in relationships['children']
        has_parent_in_project = item_id in relationships['parents']
        
        # Task is an orphan only if it has no relationships at all
        if not has_children_in_project and not has_parent_in_project:
            relationships['orphans'].append(item_id)
    
    return relationships


def find_task_by_title_match(items: List[Dict], search_text: str) -> Optional[Dict]:
    """Find a task by matching title text."""
    search_text_lower = search_text.lower().strip()
    for item in items:
        if search_text_lower in item['title'].lower() or item['title'].lower() in search_text_lower:
            return item
    return None


def find_potential_children(parent_task: Dict, items: List[Dict]) -> List[str]:
    """Find potential child tasks based on title similarity and patterns."""
    children = []
    parent_title = parent_task['title'].lower()
    parent_id = parent_task['id']
    
    # Extract key terms from parent title (remove common words)
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'shall', 'have', 'means'}
    parent_terms = [word for word in parent_title.split() if word not in common_words and len(word) > 2]
    
    for item in items:
        if item['id'] == parent_id:
            continue
            
        item_title = item['title'].lower()
        
        # Check if item title contains key terms from parent
        matching_terms = sum(1 for term in parent_terms if term in item_title)
        
        # If significant overlap in terms, consider it a potential child
        if matching_terms >= min(2, len(parent_terms) // 2):
            children.append(item['id'])
    
    return children


def display_task_subtree(task: Dict, children_map: Dict, all_items: List[Dict], level: int = 0, show_description: bool = False):
    """Display a task and its subtree recursively."""
    indent = "    " * level
    prefix = "└── " if level > 0 else "│ "
    
    display_single_task(task, prefix=indent + prefix, show_description=show_description, in_tree_view=True)
    
    # Display children
    task_children = children_map.get(task['id'], [])
    for i, child_id in enumerate(task_children):
        child_task = next((item for item in all_items if item['id'] == child_id), None)
        if child_task:
            display_task_subtree(child_task, children_map, all_items, level + 1, show_description=show_description)


def display_single_task(task: Dict, prefix: str = "├── ", show_description: bool = False, in_tree_view: bool = False):
    """Display a single task with its details."""
    # Determine icon based on labels first, then fall back to item type
    icon = None
    if task.get('labels'):
        # Check labels for specific types (case-insensitive)
        label_names = [label['name'].lower() for label in task['labels']]
        
        # Priority order: more specific labels first
        if any('bug' in name for name in label_names):
            icon = '🐛'
        elif any('test case' in name or 'test' in name for name in label_names):
            icon = '🧪'
        elif any('requirement' in name for name in label_names):
            icon = '📋'
        elif any('feature' in name for name in label_names):
            icon = '✨'
        elif any('dev' in name or 'development' in name for name in label_names):
            icon = '⚙️'
    
    # Fall back to item type icon if no label-based icon was found
    if not icon:
        icon = {
            'issue': '�',
            'pull_request': '🔀',
            'draft_issue': '📝'
        }.get(task['type'], '📄')
    
    # Build task line with issue number if available
    task_line = f"{prefix}{icon} {task['title']}"
    if task.get('number'):
        task_line += f" #{task['number']}"
    if task['repository']:
        task_line += f" ({task['repository']})"
    
    print(task_line)
    
    # Show description if requested or if it's a test case (always show for test cases)
    is_test_case = 'verify that' in task['title'].lower() or 'test case' in task['title'].lower()
    should_show_desc = show_description or is_test_case
    
    if should_show_desc and task.get('body'):
        detail_prefix = "    " + prefix.replace("├── ", "│   ").replace("└── ", "    ")
        body_lines = task['body'].strip().split('\n')
        if body_lines:
            print(f"{detail_prefix}📝 Description:")
            
            for line in body_lines:
                if line.strip():
                    line_text = line.strip()
                    print(f"{detail_prefix}   {line_text}")
                else:
                    # Show empty lines within the content
                    print(f"{detail_prefix}   ")
    
    # Add details with proper indentation
    detail_prefix = "    " + prefix.replace("├── ", "│   ").replace("└── ", "    ")
    
    if task['author']:
        print(f"{detail_prefix}👤 Author: {task['author']}")
    
    if task['assignees']:
        assignees_str = ', '.join(task['assignees'])
        print(f"{detail_prefix}👥 Assignees: {assignees_str}")
    
    if task['state']:
        print(f"{detail_prefix}🏷️  State: {task['state'].title()}")
    
    # Show labels if available
    if task.get('labels'):
        labels_str = ', '.join([f"{label['name']}" for label in task['labels']])
        print(f"{detail_prefix}🏷  Labels: {labels_str}")
    
    # Show sub-issues summary if available
    if task.get('sub_issues_summary'):
        summary = task['sub_issues_summary']
        total = summary.get('total', 0)
        completed = summary.get('completed', 0)
        percent = summary.get('percentCompleted', 0)
        print(f"{detail_prefix}📊 Sub-issues: {completed}/{total} completed ({percent}%)")
    
    # Show parent issue if available (but not in tree view where structure shows it)
    if task.get('parent') and not in_tree_view:
        parent_title = task['parent'].get('title', 'Unknown')
        parent_number = task['parent'].get('number', '')
        parent_ref = f"#{parent_number}" if parent_number else ""
        print(f"{detail_prefix}⬆️  Parent: {parent_title} {parent_ref}")
    
    status = task['project_fields'].get('Status')
    if status:
        print(f"{detail_prefix}📌 Status: {status}")
    
    # Show other important project fields (excluding Title which is already shown)
    for field_name, field_value in task['project_fields'].items():
        if field_name not in ['Status', 'Title'] and field_value and len(str(field_value)) < 100:
            print(f"{detail_prefix}📌 {field_name}: {field_value}")
    
    if task['url']:
        print(f"{detail_prefix}🔗 {task['url']}")


def display_flat_task_list(items: List[Dict], show_description: bool = False):
    """Display tasks as a flat list when no relationships are found."""
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        prefix = "└── " if is_last else "├── "
        display_single_task(item, prefix=prefix, show_description=show_description)


def main():
    parser = argparse.ArgumentParser(
        description='Retrieve tasks from a GitHub project with filtering and tree view capabilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --token ghp_xxxx --org 4d --project-id 745
  %(prog)s --token ghp_xxxx --org 4d --project-id 745 --type issue
  %(prog)s --token ghp_xxxx --org 4d --project-id 745 --tree  # Show task relationships
  %(prog)s --token ghp_xxxx --org 4d --project-id 745 --group-by-status  # Group by status
  %(prog)s --token ghp_xxxx --org 4d --project-id 745 --status "In Progress" --assignee username
  %(prog)s --token ghp_xxxx --org 4d --project-id 745 --label bug  # Filter by label
  %(prog)s --org 4d --project-id 745 --output json > project_tasks.json

Environment variables:
  GITHUB_TOKEN    GitHub Personal Access Token (alternative to --token)
  GITHUB_ORG      GitHub organization name (alternative to --org)
        """
    )
    
    parser.add_argument(
        '--token',
        help='GitHub Personal Access Token with repo and project permissions (can also use GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--org',
        help='GitHub organization name (e.g., "4d") (can also use GITHUB_ORG env var)'
    )
    
    parser.add_argument(
        '--project-id',
        type=int,
        required=True,
        help='GitHub project number (e.g., 745 from the URL)'
    )
    
    parser.add_argument(
        '--type',
        choices=['issue', 'pull_request', 'draft_issue'],
        help='Filter by item type'
    )
    
    parser.add_argument(
        '--status',
        help='Filter by status field value (case-insensitive)'
    )
    
    parser.add_argument(
        '--assignee',
        help='Filter by assignee username'
    )
    
    parser.add_argument(
        '--label',
        help='Filter by label name (case-insensitive)'
    )
    
    parser.add_argument(
        '--show-description',
        action='store_true',
        help='Show task description/body content in the output'
    )
    
    parser.add_argument(
        '--tree',
        action='store_true',
        help='Display results as a tree structure showing task relationships/dependencies'
    )
    
    parser.add_argument(
        '--group-by-status',
        action='store_true',
        help='Group results by status (the old tree view)'
    )
    
    parser.add_argument(
        '--output',
        choices=['table', 'tree', 'json', 'status-groups'],
        default='table',
        help='Output format (default: table)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    # Get token from argument or environment variable
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token:
        print("Error: GitHub token is required. Provide it via --token argument or GITHUB_TOKEN environment variable.")
        print("The token needs 'repo' and 'project' permissions.")
        sys.exit(1)
    
    # Get organization from argument or environment variable
    org = args.org or os.getenv('GITHUB_ORG')
    if not org:
        print("Error: GitHub organization is required. Provide it via --org argument or GITHUB_ORG environment variable.")
        sys.exit(1)
    
    try:
        # Initialize manager
        manager = GitHubProjectManager(token)
        
        if not args.quiet:
            print(f"🔍 Fetching project {args.project_id} from organization {org}...")
        
        # Get project information
        project_info = manager.get_project_by_number(org, args.project_id)
        
        if not args.quiet:
            print(f"📋 Found project: {project_info['title']}")
            print(f"🔄 Fetching all project items...")
        
        # Get all project items
        items = manager.get_all_project_items(project_info['id'])
        
        if not args.quiet:
            print(f"✅ Retrieved {len(items)} items")
        
        # Apply filters
        filters = {}
        if args.type:
            filters['type'] = args.type
        if args.status:
            filters['status'] = args.status
        if args.assignee:
            filters['assignee'] = args.assignee
        if args.label:
            filters['label'] = args.label
        
        if filters:
            if not args.quiet:
                print(f"🔍 Applying filters: {filters}")
            items = manager.filter_items(items, filters)
            if not args.quiet:
                print(f"✅ {len(items)} items after filtering")
        
        # Parse items
        parsed_items = [manager.parse_item_data(item) for item in items]
        
        # Output results
        show_description = getattr(args, 'show_description', False)
        if args.output == 'json':
            output_data = {
                'project': project_info,
                'items': parsed_items,
                'total_count': len(parsed_items),
                'filters_applied': filters
            }
            print(json.dumps(output_data, indent=2, default=str))
        elif args.output == 'tree' or args.tree:
            display_as_relationship_tree(parsed_items, project_info, show_description)
        elif args.output == 'status-groups' or args.group_by_status:
            display_as_status_groups(parsed_items, project_info, show_description)
        else:
            display_as_table(parsed_items, project_info, show_description)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()