import os
import re

def create_consolidated_docs():
    """
    Combines all API documentation files into a single, raw markdown file.
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

    output_dir = "docs-mintlify/assets"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_filename = os.path.join(output_dir, "consolidated-docs.md")
    
    with open(output_filename, "w") as outfile:
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                with open(doc_file, "r") as infile:
                    content = infile.read()
                    # Remove YAML frontmatter
                    content = re.sub(r'^---[\\s\\S]*?---', '', content).strip()
                    outfile.write(f"## {os.path.basename(doc_file)}\\n\\n")
                    outfile.write(content)
                    outfile.write("\\n\\n")
            else:
                print(f"Warning: {doc_file} not found.")

if __name__ == "__main__":
    create_consolidated_docs()
    print("Consolidated documentation created successfully.")
