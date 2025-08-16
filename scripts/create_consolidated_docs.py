#!/usr/bin/env python3
"""
Script to generate consolidated documentation for the "Copy All Docs for AI" button.
This script finds all .mdx files in the docs-mintlify directory and combines them
into a single markdown file that can be easily copied by developers.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

def clean_mdx_content(content):
    """Remove MDX-specific syntax and convert to clean markdown."""
    # Remove frontmatter
    content = re.sub(r'^---[\s\S]*?---\n?', '', content, flags=re.MULTILINE)
    
    # Remove import/export statements that cause parsing issues
    content = re.sub(r'^import\s+.*?;?\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^export\s+.*?;?\s*$', '', content, flags=re.MULTILINE)
    
    # Remove JSX components and convert to plain text/markdown
    content = re.sub(r'<Card[^>]*>', '', content)
    content = re.sub(r'</Card>', '', content)
    content = re.sub(r'<CardGroup[^>]*>', '', content)
    content = re.sub(r'</CardGroup>', '', content)
    content = re.sub(r'<Accordion[^>]*>', '', content)
    content = re.sub(r'</Accordion>', '', content)
    content = re.sub(r'<AccordionGroup>', '', content)
    content = re.sub(r'</AccordionGroup>', '', content)
    content = re.sub(r'<Tabs>', '', content)
    content = re.sub(r'</Tabs>', '', content)
    content = re.sub(r'<Tab[^>]*>', '', content)
    content = re.sub(r'</Tab>', '', content)
    content = re.sub(r'<Warning>', '**Warning:**', content)
    content = re.sub(r'</Warning>', '', content)
    content = re.sub(r'<Info>', '**Info:**', content)
    content = re.sub(r'</Info>', '', content)
    
    # Remove JSX style attributes and divs
    content = re.sub(r'<div[^>]*>', '', content)
    content = re.sub(r'</div>', '', content)
    
    # Remove script tags
    content = re.sub(r'<script[\s\S]*?</script>', '', content, flags=re.DOTALL)
    
    # Remove button elements (they won't work in plain markdown anyway)
    content = re.sub(r'<button[\s\S]*?</button>', '', content, flags=re.DOTALL)
    
    # Remove iframe elements
    content = re.sub(r'<iframe[\s\S]*?</iframe>', '', content, flags=re.DOTALL)
    
    # Clean up extra whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = content.strip()
    
    return content

def get_page_order():
    """Get the page order from mint.json navigation."""
    script_dir = Path(__file__).parent
    mint_json_path = script_dir.parent / "openmemory" / "ui" / "docs-mintlify" / "mint.json"
    
    try:
        with open(mint_json_path, 'r') as f:
            mint_config = json.load(f)
        
        pages_order = []
        for group in mint_config.get('navigation', []):
            for page in group.get('pages', []):
                pages_order.append(page)
        
        return pages_order
    except Exception as e:
        print(f"Warning: Could not read mint.json: {e}")
        return []

def main():
    script_dir = Path(__file__).parent
    docs_dir = script_dir.parent / "openmemory" / "ui" / "docs-mintlify"
    # CRITICAL: Output the TS module in /generated/ directory so CopyToClipboard.tsx 
    # in /snippets/ can import it. This file structure is required by Mintlify framework.
    # DO NOT CHANGE - CopyToClipboard.tsx MUST be in /snippets/ folder for Mintlify.
    # See COPY_BUTTON_DEBUGGING.md for detailed explanation.
    ts_output_file = docs_dir / "generated" / "docs.ts"
    
    # Ensure the generated directory exists
    ts_output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get page order from mint.json
    page_order = get_page_order()
    
    # Find all .mdx files
    mdx_files = []
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.mdx'):
                file_path = Path(root) / file
                # Get relative path from docs_dir
                rel_path = file_path.relative_to(docs_dir)
                # Convert to page identifier (remove .mdx and use forward slashes)
                page_id = str(rel_path.with_suffix('')).replace('\\', '/')
                mdx_files.append((page_id, file_path))
    
    # Sort files according to mint.json order
    def sort_key(item):
        page_id = item[0]
        try:
            return page_order.index(page_id)
        except ValueError:
            return 999  # Put unordered files at the end
    
    mdx_files.sort(key=sort_key)
    
    # Generate consolidated content
    consolidated_content = []
    
    # Add header
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    consolidated_content.append("# Jean Memory - Complete Documentation for AI Coding Tools")
    consolidated_content.append("")
    consolidated_content.append(f"**Generated on:** {current_time}")
    consolidated_content.append("")
    
    # Add quick overview
    consolidated_content.append("## What is Jean Memory?")
    consolidated_content.append("")
    consolidated_content.append("Jean Memory is the universal memory layer for AI applications. It provides persistent, cross-application memory that allows AI agents to remember user preferences, conversation context, and personal information across different applications and sessions.")
    consolidated_content.append("")
    consolidated_content.append("### Key Capabilities:")
    consolidated_content.append("- **Universal Memory**: Works across any application or platform")
    consolidated_content.append("- **5-Line Integration**: Add persistent memory to any React app in under 5 minutes")
    consolidated_content.append("- **Cross-Application Persistence**: Users' AI agents remember them across different apps")
    consolidated_content.append("- **Context Engineering**: Intelligent context building for personalized AI experiences")
    consolidated_content.append("- **Multiple Integration Methods**: REST API, React SDK, Python SDK, Node.js SDK, and MCP")
    consolidated_content.append("")
    consolidated_content.append("### Quick Integration Examples:")
    consolidated_content.append("")
    consolidated_content.append("#### React (5 lines):")
    consolidated_content.append("```tsx")
    consolidated_content.append("import { useState } from 'react';")
    consolidated_content.append("import { useJean, SignInWithJean, JeanChat } from '@jeanmemory/react';")
    consolidated_content.append("")
    consolidated_content.append("function MyApp() {")
    consolidated_content.append("  const [user, setUser] = useState(null);")
    consolidated_content.append("  const { agent } = useJean({ user });")
    consolidated_content.append("  ")
    consolidated_content.append("  if (!agent) return <SignInWithJean apiKey=\"your-api-key\" onSuccess={setUser} />;")
    consolidated_content.append("  return <JeanChat agent={agent} />;")
    consolidated_content.append("}")
    consolidated_content.append("```")
    consolidated_content.append("")
    consolidated_content.append("#### Python:")
    consolidated_content.append("```python")
    consolidated_content.append("from jeanmemory import JeanAgent")
    consolidated_content.append("agent = JeanAgent(api_key=\"your-api-key\")")
    consolidated_content.append("agent.run()")
    consolidated_content.append("```")
    consolidated_content.append("")
    consolidated_content.append("#### Node.js:")
    consolidated_content.append("```javascript")
    consolidated_content.append("import { JeanAgent } from '@jeanmemory/node';")
    consolidated_content.append("const agent = new JeanAgent({ apiKey: \"your-api-key\" });")
    consolidated_content.append("await agent.run();")
    consolidated_content.append("```")
    consolidated_content.append("")
    consolidated_content.append("### NPM Packages:")
    consolidated_content.append("- React: `npm install @jeanmemory/react`")
    consolidated_content.append("- Node.js: `npm install @jeanmemory/node`")
    consolidated_content.append("- Python: `pip install jeanmemory`")
    consolidated_content.append("")
    consolidated_content.append("---")
    consolidated_content.append("")
    consolidated_content.append("# Complete Documentation")
    consolidated_content.append("")
    
    # Process each file
    for page_id, file_path in mdx_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean the content
            cleaned_content = clean_mdx_content(content)
            
            if cleaned_content.strip():
                # Add section header based on file name
                section_title = page_id.replace('/', ': ').replace('-', ' ').title()
                consolidated_content.append(f"## {section_title}")
                consolidated_content.append("")
                consolidated_content.append(cleaned_content)
                consolidated_content.append("")
                consolidated_content.append("---")
                consolidated_content.append("")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Add footer with additional context for AI
    consolidated_content.append("")
    consolidated_content.append("## Additional Context for AI Development")
    consolidated_content.append("")
    consolidated_content.append("### Common Integration Patterns:")
    consolidated_content.append("- **Chat Applications**: Use JeanChat component for instant AI chat with memory")
    consolidated_content.append("- **Personal Assistants**: Build context with user preferences and history  ")
    consolidated_content.append("- **Customer Support**: Maintain customer context across support sessions")
    consolidated_content.append("- **Learning Platforms**: Track progress and adapt to learning style")
    consolidated_content.append("- **Team Collaboration**: Share context across team members")
    consolidated_content.append("")
    consolidated_content.append("### API Base URL:")
    consolidated_content.append("- Production: `https://jean-memory-api-virginia.onrender.com`")
    consolidated_content.append("")
    consolidated_content.append("### Authentication:")
    consolidated_content.append("- All SDKs handle OAuth 2.1 PKCE flow automatically")
    consolidated_content.append("- Get API keys at: https://jeanmemory.com")
    consolidated_content.append("")
    consolidated_content.append("### Key Features to Highlight in Applications:")
    consolidated_content.append("- Cross-application memory persistence")
    consolidated_content.append("- Personalized AI experiences")
    consolidated_content.append("- Context-aware responses")
    consolidated_content.append("- User preference learning")
    consolidated_content.append("- Conversation continuity")
    consolidated_content.append("")
    consolidated_content.append("This documentation contains everything needed to integrate Jean Memory into any application. Focus on the SDK that matches your technology stack and follow the quickstart examples.")
    
    # Write the consolidated file
    final_content = '\n'.join(consolidated_content)
    
    # Write the consolidated file as a TypeScript module
    # Use triple backticks for a template literal that can span multiple lines
    # CRITICAL: Escape both backticks AND template literal syntax to prevent JS syntax errors
    # The ${} syntax in documentation examples will break the template literal if not escaped
    escaped_content = final_content.replace('`', '\\`').replace('${', '\\${')
    
    # CRITICAL: Do NOT add TypeScript type annotations (: string) as they break JavaScript imports
    # The CopyToClipboard.tsx component imports this as a JavaScript module
    ts_content = f"""// This file is auto-generated by scripts/create_consolidated_docs.py
// Do not edit this file manually.
// See COPY_BUTTON_DEBUGGING.md for debugging guide.

export const consolidatedDocs = `
{escaped_content}
`;
"""
    
    with open(ts_output_file, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    # Also generate a markdown file in the static directory for direct fetching
    static_output_path = docs_dir / "static" / "consolidated-docs.md"
    static_output_path.parent.mkdir(exist_ok=True)
    
    with open(static_output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"✅ Consolidated documentation generated as a TS module: {ts_output_file}")
    print(f"✅ Consolidated documentation generated as markdown: {static_output_path}")
    print(f"📊 Processed {len(mdx_files)} documentation files")
    print(f"📝 Generated {len(final_content.split())} words of documentation")

if __name__ == "__main__":
    main()
