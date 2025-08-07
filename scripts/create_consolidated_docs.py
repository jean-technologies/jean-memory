
import os

def create_consolidated_docs():
    """
    Combines all API documentation files into a single markdown file.
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

    output_filename = "docs-mintlify/consolidated-api-docs.mdx"

    with open(output_filename, "w") as outfile:
        outfile.write("# Consolidated API Documentation\n\n")
        outfile.write("Don't like reading docs? Paste this into your AI coding tool (Cursor, Claude, etc.), give it instructions for what you'd like to build, and have it build it for you.\n\n")
        
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                with open(doc_file, "r") as infile:
                    outfile.write(f"## {os.path.basename(doc_file)}\n\n")
                    outfile.write(infile.read())
                    outfile.write("\n\n")
            else:
                print(f"Warning: {doc_file} not found.")

if __name__ == "__main__":
    create_consolidated_docs()
    print("Consolidated documentation created successfully.")
