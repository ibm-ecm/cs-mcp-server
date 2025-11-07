#  Licensed Materials - Property of IBM (c) Copyright IBM Corp. 2025 All Rights Reserved.

#  US Government Users Restricted Rights - Use, duplication or disclosure restricted by GSA ADP Schedule Contract with
#  IBM Corp.

#  DISCLAIMER OF WARRANTIES :

#  Permission is granted to copy and modify this Sample code, and to distribute modified versions provided that both the
#  copyright notice, and this permission notice and warranty disclaimer appear in all copies and modified versions.

#  THIS SAMPLE CODE IS LICENSED TO YOU AS-IS. IBM AND ITS SUPPLIERS AND LICENSORS DISCLAIM ALL WARRANTIES, EITHER
#  EXPRESS OR IMPLIED, IN SUCH SAMPLE CODE, INCLUDING THE WARRANTY OF NON-INFRINGEMENT AND THE IMPLIED WARRANTIES OF
#  MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT WILL IBM OR ITS LICENSORS OR SUPPLIERS BE LIABLE FOR
#  ANY DAMAGES ARISING OUT OF THE USE OF OR INABILITY TO USE THE SAMPLE CODE, DISTRIBUTION OF THE SAMPLE CODE, OR
#  COMBINATION OF THE SAMPLE CODE WITH ANY OTHER CODE. IN NO EVENT SHALL IBM OR ITS LICENSORS AND SUPPLIERS BE LIABLE
#  FOR ANY LOST REVENUE, LOST PROFITS OR DATA, OR FOR DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
#  DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF IBM OR ITS LICENSORS OR SUPPLIERS HAVE
#  BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

"""
MCP Server Main Module

This module serves as the main entry point for the Model-Context-Protocol (MCP) server
that integrates with a GraphQL client to provide various content management tools and services.
It handles server initialization, tool registration, and graceful shutdown procedures.
"""

# Standard library imports
import asyncio
import atexit
import logging
import os

# Third-party imports
import truststore
from mcp.server.fastmcp import FastMCP

# Use absolute imports
from cs_mcp_server.cache import MetadataCache
from cs_mcp_server.client import GraphQLClient
from cs_mcp_server.tools.documents import register_document_tools
from cs_mcp_server.tools.classes import register_class_tools
from cs_mcp_server.tools.search import (
    register_search_tools,
)
from cs_mcp_server.tools.mcp_manage_hold import register_legalhold
from cs_mcp_server.tools.vector_search import register_vector_search_tool
from cs_mcp_server.tools.folders import register_folder_tools
from cs_mcp_server.tools.annotations import register_annotation_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global MCP instance
mcp = FastMCP("ecm")


def parse_ssl_flag(value, default="true"):
    """
    Parse SSL flag which can be either a boolean or a path to a certificate.

    Args:
        value: The SSL flag value from environment variable
        default: Default value if not provided

    Returns:
        bool or str: True/False for boolean values, or the path string for certificates
    """
    if value is None:
        value = default

    # If it's a string representation of a boolean
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    # Otherwise it's a path to a certificate or other value
    return value


def initialize_graphql_client():
    """
    Initialize the GraphQL client for the MCP server.
    Supports both basic authentication and OAuth authentication methods.

    Returns:
        GraphQLClient: The initialized GraphQL client instance
    """
    # Get connection details from environment variables
    graphql_url = os.environ.get("SERVER_URL", "")
    username = os.environ.get("USERNAME", "")
    password = os.environ.get("PASSWORD", "")
    ssl_enabled = parse_ssl_flag(os.environ.get("SSL_ENABLED"), "true")
    token_ssl_enabled = parse_ssl_flag(os.environ.get("TOKEN_SSL_ENABLED"), "true")
    object_store = os.environ.get("OBJECT_STORE", "")
    token_refresh = int(
        os.environ.get("TOKEN_REFRESH", "1800")
    )  # 30 minutes in seconds

    # OAuth specific parameters
    token_url = os.environ.get("TOKEN_URL", "")
    grant_type = os.environ.get("GRANT_TYPE", "")
    scope = os.environ.get("SCOPE", "")
    client_id = os.environ.get("CLIENT_ID", "")
    client_secret = os.environ.get("CLIENT_SECRET", "")

    # ZenIAM specific parameters
    zeniam_zen_url = os.environ.get("ZENIAM_ZEN_URL", "")
    zeniam_iam_url = os.environ.get("ZENIAM_IAM_URL", "")
    zeniam_iam_ssl_enabled = parse_ssl_flag(
        os.environ.get("ZENIAM_IAM_SSL_ENABLED"), "true"
    )
    zeniam_iam_grant_type = os.environ.get("ZENIAM_IAM_GRANT_TYPE", "")
    zeniam_iam_scope = os.environ.get("ZENIAM_IAM_SCOPE", "")
    zeniam_iam_client_id = os.environ.get("ZENIAM_IAM_CLIENT_ID", "")
    zeniam_iam_cient_secret = os.environ.get("ZENIAM_IAM_CLIENT_SECRET", "")
    zeniam_iam_user_name = os.environ.get("ZENIAM_IAM_USER", "")
    zeniam_iam_user_password = os.environ.get("ZENIAM_IAM_PASSWORD", "")
    zeniam_zen_exchange_ssl = parse_ssl_flag(
        os.environ.get("ZENIAM_ZEN_SSL_ENABLED"), "true"
    )

    # Connection settings
    timeout = float(os.environ.get("REQUEST_TIMEOUT", "30.0"))
    pool_connections = int(os.environ.get("POOL_CONNECTIONS", "100"))
    pool_maxsize = int(os.environ.get("POOL_MAXSIZE", "100"))

    # Validate required parameters
    if not graphql_url:
        raise ValueError("SERVER_URL environment variable is required")
    if not username and not zeniam_zen_url:
        raise ValueError("USERNAME environment variable is required")
    if not password and not zeniam_zen_url:
        raise ValueError("PASSWORD environment variable is required")
    if not object_store:
        raise ValueError("OBJECT_STORE environment variable is required")

    # Create and return the GraphQL client
    # Pass all parameters to the constructor and let it handle them appropriately
    return GraphQLClient(
        url=graphql_url,
        username=username,
        password=password,
        ssl_enabled=ssl_enabled,
        object_store=object_store,
        token_url=token_url,
        token_ssl_enabled=token_ssl_enabled,
        grant_type=grant_type,
        scope=scope,
        client_id=client_id,
        client_secret=client_secret,
        timeout=timeout,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        token_refresh=token_refresh,
        ZenIAM_iam_url=zeniam_iam_url,
        ZenIAM_iam_ssl_enabled=zeniam_iam_ssl_enabled,
        ZenIAM_iam_grant_type=zeniam_iam_grant_type,
        ZenIAM_iam_scope=zeniam_iam_scope,
        ZenIAM_iam_client_id=zeniam_iam_client_id,
        ZenIAM_iam_client_secret=zeniam_iam_cient_secret,
        ZenIAM_iam_user_name=zeniam_iam_user_name,
        ZenIAM_iam_user_password=zeniam_iam_user_password,
        ZenIAM_zen_url=zeniam_zen_url,
        ZenIAM_zen_exchange_ssl=zeniam_zen_exchange_ssl,
    )


def register_tools(graphql_client: GraphQLClient, metadata_cache: MetadataCache):
    """
    Register all tools with the MCP server instance.

    Args:
        graphql_client: The initialized GraphQL client to use with tools
        metadata_cache: Optional metadata cache instance
    """
    # Register all tools with the GraphQL client

    register_document_tools(mcp, graphql_client, metadata_cache)
    # Planned for future releases
    # register_legalhold(mcp, graphql_client)
    # register_vector_search_tool(mcp, graphql_client)
    register_search_tools(mcp, graphql_client, metadata_cache)
    register_class_tools(mcp, graphql_client, metadata_cache)
    register_folder_tools(mcp, graphql_client)
    register_annotation_tools(mcp, graphql_client)


async def shutdown_client(graphql_client):
    """
    Properly close the GraphQL client's aiohttp session.

    Args:
        graphql_client: The GraphQL client to close
    """
    await graphql_client.close()
    logger.info("GraphQL client session closed.")


def main():
    """
    Main entry point for the MCP server.
    Initializes the GraphQL client and runs the MCP server.
    """
    logger.info("Initializing GraphQL MCP Server...")
    # Initialize the GraphQL client
    graphql_client = initialize_graphql_client()
    logger.info("GraphQL client initialized successfully.")

    # Create the metadata cache
    metadata_cache = MetadataCache()
    logger.info("Metadata cache created successfully.")

    # Register tools with the MCP server
    register_tools(graphql_client, metadata_cache)
    logger.info("Tools registered with MCP server.")

    # Run the MCP server
    logger.info("Starting MCP server... Press Ctrl+C to exit.")
    try:

        def exit_handler():
            # Run the async close in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(shutdown_client(graphql_client))
            loop.close()

        atexit.register(exit_handler)

        # Start the MCP server
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        # Ensure client is closed on keyboard interrupt
        loop = asyncio.get_event_loop()
        loop.run_until_complete(shutdown_client(graphql_client))
        logger.info("Server shut down gracefully.")


if __name__ == "__main__":
    # Calling main
    main()
