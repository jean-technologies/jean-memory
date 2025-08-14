"""
Jean Memory Python SDK CLI
Command-line interface for Jean Memory operations
"""

import os
import json
import sys
from typing import Optional
import click
from .client import JeanMemoryClient, JeanMemoryError
from .auth import JeanMemoryAuth

# Configuration file location
CONFIG_FILE = os.path.expanduser('~/.jean-memory/config.json')

def load_config() -> dict:
    """Load configuration from file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config: dict):
    """Save configuration to file"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_api_key() -> Optional[str]:
    """Get API key from environment or config"""
    # Try environment variable first
    api_key = os.getenv('JEAN_API_KEY')
    if api_key:
        return api_key
    
    # Try config file
    config = load_config()
    return config.get('api_key')

def get_client() -> JeanMemoryClient:
    """Get configured Jean Memory client"""
    api_key = get_api_key()
    if not api_key:
        click.echo("❌ No API key found. Set JEAN_API_KEY environment variable or run 'jean login'")
        sys.exit(1)
    
    return JeanMemoryClient(api_key)

@click.group()
@click.version_option(version='1.0.1', prog_name='Jean Memory CLI')
def cli():
    """
    Jean Memory CLI - Manage your AI memory from the command line
    
    Add memories, search your context, and manage your personal AI assistant.
    """
    pass

@cli.command()
@click.option('--api-key', help='Your Jean Memory API key')
def login(api_key: Optional[str]):
    """
    Authenticate with Jean Memory
    
    You can provide an API key directly or use OAuth flow.
    """
    if api_key:
        # Direct API key login
        if not api_key.startswith('jean_sk_'):
            click.echo("❌ Invalid API key format. Must start with 'jean_sk_'")
            sys.exit(1)
        
        # Test the API key
        try:
            client = JeanMemoryClient(api_key)
            client.health_check()
            
            # Save to config
            config = load_config()
            config['api_key'] = api_key
            save_config(config)
            
            click.echo("✅ Successfully authenticated with Jean Memory!")
            
        except JeanMemoryError as e:
            click.echo(f"❌ Authentication failed: {e}")
            sys.exit(1)
    else:
        # OAuth flow
        try:
            click.echo("🔐 Starting OAuth authentication...")
            auth = JeanMemoryAuth(api_key="default_client")
            user_info = auth.authenticate()
            
            # Save to config
            config = load_config()
            config['api_key'] = user_info['access_token']
            config['user'] = {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'user_id': user_info.get('user_id')
            }
            save_config(config)
            
            click.echo(f"✅ Successfully authenticated as {user_info.get('email')}!")
            
        except Exception as e:
            click.echo(f"❌ Authentication failed: {e}")
            sys.exit(1)

@cli.command()
def logout():
    """Sign out and remove stored credentials"""
    try:
        os.remove(CONFIG_FILE)
        click.echo("✅ Successfully signed out")
    except FileNotFoundError:
        click.echo("ℹ️ Already signed out")

@cli.command()
@click.argument('content')
@click.option('--context', help='Additional context metadata (JSON format)')
def store(content: str, context: Optional[str]):
    """
    Store a new memory
    
    Example:
        jean store "I prefer meetings in the morning"
        jean store "Project X deadline is next Friday" --context '{"project": "X"}'
    """
    try:
        client = get_client()
        
        context_data = {}
        if context:
            try:
                context_data = json.loads(context)
            except json.JSONDecodeError:
                click.echo("❌ Invalid context JSON format")
                sys.exit(1)
        
        result = client.store_memory(content, context_data)
        click.echo(f"✅ Memory stored: {result.get('id', 'success')}")
        
    except JeanMemoryError as e:
        click.echo(f"❌ Failed to store memory: {e}")
        sys.exit(1)

@cli.command()
@click.argument('query')
@click.option('--limit', default=10, help='Maximum number of memories to return')
@click.option('--format', 'output_format', default='list', type=click.Choice(['list', 'json']), 
              help='Output format')
def search(query: str, limit: int, output_format: str):
    """
    Search your memories
    
    Example:
        jean search "work preferences"
        jean search "project deadlines" --limit 5
        jean search "meetings" --format json
    """
    try:
        client = get_client()
        memories = client.retrieve_memories(query, limit)
        
        if not memories:
            click.echo("No memories found matching your query.")
            return
        
        if output_format == 'json':
            click.echo(json.dumps(memories, indent=2))
        else:
            click.echo(f"Found {len(memories)} memories:\n")
            for i, memory in enumerate(memories, 1):
                content = memory.get('content', '')
                timestamp = memory.get('created_at', '')
                click.echo(f"{i}. {content}")
                if timestamp:
                    click.echo(f"   📅 {timestamp}")
                click.echo()
        
    except JeanMemoryError as e:
        click.echo(f"❌ Search failed: {e}")
        sys.exit(1)

@cli.command()
@click.argument('query')
def context(query: str):
    """
    Get formatted context for a query
    
    Example:
        jean context "What should I know about the project?"
    """
    try:
        client = get_client()
        context_text = client.get_context(query)
        click.echo(context_text)
        
    except JeanMemoryError as e:
        click.echo(f"❌ Failed to get context: {e}")
        sys.exit(1)

@cli.command()
@click.option('--limit', default=20, help='Number of memories to show')
@click.option('--offset', default=0, help='Number of memories to skip')
@click.option('--format', 'output_format', default='list', type=click.Choice(['list', 'json']),
              help='Output format')
def list(limit: int, offset: int, output_format: str):
    """
    List all your memories with pagination
    
    Example:
        jean list
        jean list --limit 10 --offset 20
        jean list --format json
    """
    try:
        client = get_client()
        result = client.list_memories(limit, offset)
        memories = result.get('memories', [])
        
        if not memories:
            click.echo("No memories found.")
            return
        
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            total = result.get('total', len(memories))
            click.echo(f"Showing {len(memories)} of {total} memories (offset: {offset}):\n")
            
            for i, memory in enumerate(memories, offset + 1):
                memory_id = memory.get('id', '')
                content = memory.get('content', '')
                timestamp = memory.get('created_at', '')
                
                click.echo(f"{i}. {content}")
                click.echo(f"   🆔 {memory_id}")
                if timestamp:
                    click.echo(f"   📅 {timestamp}")
                click.echo()
        
    except JeanMemoryError as e:
        click.echo(f"❌ Failed to list memories: {e}")
        sys.exit(1)

@cli.command()
@click.argument('memory_id')
def delete(memory_id: str):
    """
    Delete a specific memory
    
    Example:
        jean delete mem_abc123
    """
    try:
        client = get_client()
        
        # Confirm deletion
        if not click.confirm(f'Are you sure you want to delete memory "{memory_id}"?'):
            click.echo("Deletion cancelled.")
            return
        
        result = client.delete_memory(memory_id)
        click.echo(f"✅ Memory deleted: {memory_id}")
        
    except JeanMemoryError as e:
        click.echo(f"❌ Failed to delete memory: {e}")
        sys.exit(1)

@cli.command()
def status():
    """Check authentication status and API health"""
    api_key = get_api_key()
    
    if not api_key:
        click.echo("❌ Not authenticated. Run 'jean login' to sign in.")
        return
    
    try:
        client = JeanMemoryClient(api_key)
        health = client.health_check()
        
        config = load_config()
        user = config.get('user', {})
        
        click.echo("✅ Authentication Status: Connected")
        if user.get('email'):
            click.echo(f"👤 User: {user['email']}")
        if user.get('name'):
            click.echo(f"📝 Name: {user['name']}")
        click.echo(f"🔑 API Key: {api_key[:12]}...")
        click.echo(f"🏥 API Health: {health.get('status', 'OK')}")
        
    except JeanMemoryError as e:
        click.echo(f"❌ API Error: {e}")
        sys.exit(1)

@cli.command()
def config():
    """Show current configuration"""
    config_data = load_config()
    
    if not config_data:
        click.echo("No configuration found. Run 'jean login' to get started.")
        return
    
    # Hide sensitive data
    safe_config = config_data.copy()
    if 'api_key' in safe_config:
        safe_config['api_key'] = safe_config['api_key'][:12] + "..."
    
    click.echo("Current configuration:")
    click.echo(json.dumps(safe_config, indent=2))
    click.echo(f"\nConfig file: {CONFIG_FILE}")

if __name__ == '__main__':
    cli()