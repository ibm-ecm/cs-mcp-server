## VS Code Copilot Configuration

You can configure VS Code Copilot to use the Core Content Services MCP Server in three ways:

**Option 1: User Settings (Global Configuration)**

To configure an MCP server for all your workspaces:

1. Run the `MCP: Add Server` command from the Command Palette
2. Provide the server information and select **Global** to add the server configuration to your profile

Or:

1. Run the `MCP: Open User Configuration` command, which opens the `mcp.json` file in your user profile
2. Add the following configuration:

```json
{
  "servers": {
    "core-cs-mcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ibm-ecm/cs-mcp-server",
        "core-cs-mcp-server"
      ],
      "env": {
        "SERVER_URL": "https://your-graphql-server/content-services-graphql/graphql",
        "OBJECT_STORE": "your_object_store",
        "USERNAME": "${input:username}",
        "PASSWORD": "${input:password}"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "username",
      "description": "Your FileNet CPE username"
    },
    {
      "type": "promptString",
      "id": "password",
      "description": "Your FileNet CPE password",
      "password": true
    }
  ]
}
```

**Option 2: Workspace Configuration**

To share the MCP server configuration with your project team:

1. Create a `.vscode/mcp.json` file in your workspace.
2. Add the following configuration:

```json
{
  "servers": {
    "core-cs-mcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ibm-ecm/cs-mcp-server",
        "core-cs-mcp-server"
      ],
      "env": {
        "SERVER_URL": "https://your-graphql-server/content-services-graphql/graphql",
        "OBJECT_STORE": "your_object_store",
        "USERNAME": "${input:username}",
        "PASSWORD": "${input:password}"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "username",
      "description": "Your FileNet CPE username"
    },
    {
      "type": "promptString",
      "id": "password",
      "description": "Your FileNet CPE password",
      "password": true
    }
  ]
}
```

**Option 3: Using Local Installation**

If you have a local copy of the repository, you can configure VS Code to use it:

```json
{
  "servers": {
    "core-cs-mcp-server": {
      "type": "stdio",
      "command": "/path/to/your/uvx",
      "args": [
        "--from",
        "/path/to/your/cs-mcp-server",
        "core-cs-mcp-server"
      ],
      "env": {
        "SERVER_URL": "https://your-graphql-server/content-services-graphql/graphql",
        "OBJECT_STORE": "your_object_store",
        "USERNAME": "${input:username}",
        "PASSWORD": "${input:password}"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "username",
      "description": "Your FileNet CPE username"
    },
    {
      "type": "promptString",
      "id": "password",
      "description": "Your FileNet CPE password",
      "password": true
    }
  ]
}
```

> **Important:** Avoid hardcoding sensitive information like passwords by using input variables or environment files as shown in the workspace configuration example.

> **Note:** The JSON configuration examples above show only the minimum required environment variables. For a complete list of all possible configuration options, refer to the Environment Variables tables above.
