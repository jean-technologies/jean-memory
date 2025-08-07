import os

def create_consolidated_docs():
    """
    Combines all API documentation files into a single markdown file
    and embeds it into the ai-copilot.mdx page.
    """
    doc_files = [
        "docs-mintlify/mcp/introduction.mdx",
        "docs-mintlify/mcp/authentication.mdx",
        "docs-mintlify/mcp/context-engineering.mdx",
        "docs-mintlify/mcp/setup.mdx",
        "docs-mintlify/sdk/react.mdx",
        "docs-mintlify/sdk/nodejs.mdx",
        "docs-mintlify/sdk/python.mdx",
    ]

    output_filename = "docs-mintlify/ai-copilot.mdx"
    
    consolidated_content = ""
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            with open(doc_file, "r") as infile:
                consolidated_content += f"## {os.path.basename(doc_file)}\\n\\n"
                consolidated_content += infile.read()
                consolidated_content += "\\n\\n"
        else:
            print(f"Warning: {doc_file} not found.")

    with open(output_filename, "w") as outfile:
        outfile.write(f"""---
title: "AI Copilot"
description: "Your AI coding assistant's best friend. A consolidated view of all our documentation for easy copy-pasting."
---

import {{ CodeBlock }} from 'mintlify/components';

## Copy-Paste All Documentation

Don't like reading docs? Paste this into your AI coding tool (Cursor, Claude, etc.), give it instructions for what you'd like to build, and have it build it for you.

<CodeBlock language="markdown" showLineNumbers={{false}}>
{consolidated_content}
</CodeBlock>
""")

if __name__ == "__main__":
    create_consolidated_docs()
    print("Consolidated documentation created successfully.")
