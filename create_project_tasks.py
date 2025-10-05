#!/usr/bin/env python3
"""
Create Project Tasks Script
Reads a JSON file containing test case definitions and creates them in GitHub Projects
using the create_test_case_task MCP tool.

Usage:
    python create_project_tasks.py tasks.json
    python create_project_tasks.py --file 736.json --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path to import the MCP server
sys.path.insert(0, str(Path(__file__).parent))
from mcp.mcp_server import GitHubProjectMCPServer


def find_tool_calls(data: Any, tool_name: str = "create_test_case_task") -> List[Dict]:
    """
    Recursively search through a data structure to find all tool calls.
    
    Args:
        data: JSON data structure (dict, list, or primitive)
        tool_name: Name of the tool to search for
    
    Returns:
        List of dictionaries containing tool call arguments
    """
    tool_calls = []
    
    if isinstance(data, dict):
        # Check if this dict contains a tool call
        if data.get('tool') == tool_name and 'arguments' in data:
            tool_calls.append(data['arguments'])
        
        # Recursively search all values
        for value in data.values():
            tool_calls.extend(find_tool_calls(value, tool_name))
    
    elif isinstance(data, list):
        # Recursively search all items
        for item in data:
            tool_calls.extend(find_tool_calls(item, tool_name))
    
    return tool_calls


def create_tasks_from_file(
    json_file: str,
    dry_run: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Read a JSON file and create all test case tasks found in it.
    
    Args:
        json_file: Path to JSON file containing task definitions
        dry_run: If True, only show what would be created without actually creating
        verbose: If True, show detailed information
    
    Returns:
        Dictionary with creation results
    """
    # Load JSON file
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {json_file}: {e}")
        sys.exit(1)
    
    if verbose:
        print(f"📖 Loaded JSON from: {json_file}")
    
    # Find all tool calls
    tool_calls = find_tool_calls(data, "create_test_case_task")
    
    if not tool_calls:
        print("⚠️  No create_test_case_task tool calls found in the JSON file")
        return {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
    
    print(f"\n📋 Found {len(tool_calls)} test case(s) to create")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No tasks will be created\n")
        print("=" * 80)
        for i, arguments in enumerate(tool_calls, 1):
            print(f"\n{i}. {arguments.get('title', 'Untitled')}")
            print(f"   Parent: #{arguments.get('parent_task_number', 'N/A')}")
            print(f"   Project: {arguments.get('project_id', 'N/A')}")
            print(f"   Assignees: {', '.join(arguments.get('assignees', []))}")
            print(f"   Test ID: {arguments.get('test_id', 'N/A')}")
        print("\n" + "=" * 80)
        return {
            'total': len(tool_calls),
            'success': 0,
            'failed': 0,
            'skipped': len(tool_calls),
            'results': []
        }
    
    # Initialize MCP server
    print("\n🔧 Initializing GitHub MCP Server...")
    server = GitHubProjectMCPServer()
    
    try:
        server.initialize()
        print("✅ Server initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize server: {e}")
        print("\nMake sure you have:")
        print("  1. Set GITHUB_TOKEN environment variable")
        print("  2. Token has 'repo' and 'project' permissions")
        sys.exit(1)
    
    # Create tasks
    results = {
        'total': len(tool_calls),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'results': []
    }
    
    print("\n" + "=" * 80)
    print("Creating test case tasks...")
    print("=" * 80 + "\n")
    
    for i, arguments in enumerate(tool_calls, 1):
        title = arguments.get('title', 'Untitled')
        parent = arguments.get('parent_task_number', arguments.get('parent_task_id', 'N/A'))
        
        print(f"{i}/{len(tool_calls)}: Creating '{title}'")
        print(f"         Parent: #{parent}")
        
        try:
            result = server.create_test_case_task(**arguments)
            
            if result.get('success'):
                results['success'] += 1
                issue_number = result['issue']['number']
                issue_url = result['issue']['url']
                print(f"         ✅ Created: #{issue_number}")
                print(f"         🔗 {issue_url}")
                
                results['results'].append({
                    'status': 'success',
                    'title': title,
                    'issue_number': issue_number,
                    'issue_url': issue_url,
                    'parent': parent
                })
            else:
                results['failed'] += 1
                print(f"         ❌ Failed: {result.get('error', 'Unknown error')}")
                
                results['results'].append({
                    'status': 'failed',
                    'title': title,
                    'error': result.get('error', 'Unknown error'),
                    'parent': parent
                })
        
        except Exception as e:
            results['failed'] += 1
            error_msg = str(e)
            print(f"         ❌ Error: {error_msg}")
            
            results['results'].append({
                'status': 'error',
                'title': title,
                'error': error_msg,
                'parent': parent
            })
        
        print()  # Empty line between tasks
    
    return results


def print_summary(results: Dict[str, Any]):
    """Print a summary of the task creation results."""
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total tasks:      {results['total']}")
    print(f"✅ Created:       {results['success']}")
    print(f"❌ Failed:        {results['failed']}")
    print(f"⏭️  Skipped:       {results['skipped']}")
    print("=" * 80)
    
    if results['failed'] > 0:
        print("\n⚠️  Failed tasks:")
        for result in results['results']:
            if result['status'] in ['failed', 'error']:
                print(f"  - {result['title']}")
                print(f"    Error: {result.get('error', 'Unknown')}")
    
    if results['success'] > 0:
        print(f"\n✅ Successfully created {results['success']} test case(s)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create GitHub project test case tasks from a JSON file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create all tasks from a JSON file
  python create_project_tasks.py 736.json

  # Dry run to see what would be created
  python create_project_tasks.py --file 736.json --dry-run

  # Verbose output
  python create_project_tasks.py 736.json --verbose

Environment Variables:
  GITHUB_TOKEN  GitHub Personal Access Token (required)
  GITHUB_ORG    Default GitHub organization (optional)
        """
    )
    
    parser.add_argument(
        'json_file',
        nargs='?',
        help='Path to JSON file containing task definitions'
    )
    
    parser.add_argument(
        '--file', '-f',
        dest='json_file_flag',
        help='Path to JSON file (alternative to positional argument)'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Show what would be created without actually creating tasks'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Save results to a JSON file'
    )
    
    args = parser.parse_args()
    
    # Get JSON file path
    json_file = args.json_file or args.json_file_flag
    
    if not json_file:
        parser.print_help()
        print("\n❌ Error: JSON file argument is required")
        sys.exit(1)
    
    # Check if file exists
    if not os.path.isfile(json_file):
        print(f"❌ Error: File not found: {json_file}")
        sys.exit(1)
    
    print("=" * 80)
    print("🚀 GitHub Project Test Case Creator")
    print("=" * 80)
    
    # Create tasks
    results = create_tasks_from_file(
        json_file=json_file,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    # Print summary
    print_summary(results)
    
    # Save results if requested
    if args.output and not args.dry_run:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {args.output}")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not save results: {e}")
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()