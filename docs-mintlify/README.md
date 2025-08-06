# Jean Memory Documentation (Mintlify)

This is the official documentation for Jean Memory, built with Mintlify.

## Local Development

```bash
# Install Mintlify CLI (if not already installed)
npm install -g mintlify

# Run development server
mintlify dev

# Your docs will be available at http://localhost:3000
```

## Structure

- `mint.json` - Configuration file with navigation, colors, and settings
- `introduction.mdx` - Home page
- `quickstart.mdx` - Getting started guide
- `api-reference/` - API documentation
- `sdk/` - SDK documentation
- `mcp/` - MCP protocol documentation
- `essentials/` - Core concepts (auth, metadata, etc.)

## Deployment

Mintlify automatically deploys from this folder when pushed to the main branch.

## Adding New Pages

1. Create a new `.mdx` file
2. Add frontmatter with `title` and `description`
3. Add to navigation in `mint.json`

## Components

Mintlify provides built-in components:
- `<Card>` - Feature cards
- `<CodeGroup>` - Multiple code examples
- `<Tabs>` - Tabbed content
- `<Steps>` - Step-by-step guides
- `<AccordionGroup>` - Collapsible sections
- `<Info>`, `<Warning>`, `<Note>` - Callout boxes

## Learn More

- [Mintlify Documentation](https://mintlify.com/docs)
- [Component Library](https://mintlify.com/docs/components)