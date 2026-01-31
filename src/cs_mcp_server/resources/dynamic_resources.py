# Copyright contributors to the IBM Core Content Services MCP Server project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Dynamic Resources Module

This module provides functionality to dynamically register resources based on
documents in a configured folder. Resources are created on server start
and can be refreshed via a tool.
"""

import logging
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.types import Annotations

from cs_mcp_server.client.graphql_client import GraphQLClient
from cs_mcp_server.resources.documents import _fetch_text_extract_by_identifier

# Logger for this module
logger = logging.getLogger(__name__)


def _list_dynamic_resources_folder_sync(
    graphql_client: GraphQLClient,
    folder_path: str,
) -> List[Dict[str, str]]:
    """List all documents in the specified folder synchronously."""
    query = """
    query getContainedDocuments($object_store_name: String!, $folder_id_or_path: String!){
        folder(
            repositoryIdentifier: $object_store_name
            identifier: $folder_id_or_path
        ) {
            containedDocuments
                {
                documents
                {
                    id
                    name
                    className
                }
                }
        }
    }
    """

    variables = {
        "folder_id_or_path": folder_path,
        "object_store_name": graphql_client.object_store,
    }

    try:
        result = graphql_client.execute(query=query, variables=variables)

        # Check for errors (e.g., folder not found)
        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown error")
            logger.warning("Folder %s not accessible: %s", folder_path, error_msg)
            return []

        if not result or "data" not in result:
            logger.warning("No data returned for folder %s", folder_path)
            return []

        folder = result["data"].get("folder")
        if not folder:
            logger.info("Folder %s is empty or does not exist", folder_path)
            return []

        contained_docs = folder.get("containedDocuments", {})
        return contained_docs.get("documents", [])

    except Exception as e:
        logger.error("Error listing %s: %s", folder_path, str(e))
        return []


async def _list_dynamic_resources_folder(
    graphql_client: GraphQLClient,
    folder_path: str,
) -> List[Dict[str, str]]:
    """List all documents in the specified folder asynchronously."""
    query = """
    query getContainedDocuments($object_store_name: String!, $folder_id_or_path: String!){
        folder(
            repositoryIdentifier: $object_store_name
            identifier: $folder_id_or_path
        ) {
            containedDocuments
                {
                documents
                {
                    id
                    name
                    className
                }
                }
        }
    }
    """

    variables = {
        "folder_id_or_path": folder_path,
        "object_store_name": graphql_client.object_store,
    }

    try:
        result = await graphql_client.execute_async(query=query, variables=variables)

        # Check for errors (e.g., folder not found)
        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown error")
            logger.warning("Folder %s not accessible: %s", folder_path, error_msg)
            return []

        if not result or "data" not in result:
            logger.warning("No data returned for folder %s", folder_path)
            return []

        folder = result["data"].get("folder")
        if not folder:
            logger.info("Folder %s is empty or does not exist", folder_path)
            return []

        documents = folder["containedDocuments"]["documents"]
        return [
            {
                "id": doc.get("id"),
                "name": doc.get("name"),
                "pathName": f"{folder_path}/{doc.get('name')}",
            }
            for doc in documents
        ]

    except Exception as e:
        logger.error("Error listing %s: %s", folder_path, str(e))
        return []


def _register_resources_from_documents(
    mcp: FastMCP,
    graphql_client: GraphQLClient,
    folder_path: str,
    documents: List[Dict[str, str]],
) -> None:
    """Helper function to register resources from a list of documents."""
    # Common file extensions to remove from resource names
    extensions = [
        ".txt",
        ".md",
        ".pdf",
        ".doc",
        ".docx",
        ".html",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
    ]

    for doc in documents:
        doc_name = doc["name"]
        doc_id = doc["id"]

        # Clean document name for URI
        resource_name = doc_name.lower()

        # Remove file extension if present (check suffix)
        for ext in extensions:
            if resource_name.endswith(ext):
                resource_name = resource_name[: -len(ext)]
                break

        # Replace spaces and underscores with hyphens for consistency
        resource_name = resource_name.replace(" ", "-").replace("_", "-")

        # Clean folder path (remove leading/trailing slashes)
        clean_folder = folder_path.strip("/")

        # Build URI with object store, folder path, and document name
        resource_uri = f"ibm-cs://{graphql_client.object_store}/documents/{clean_folder}/{resource_name}"

        try:

            def make_resource_func(identifier: str, name: str):
                async def get_document_content() -> str:
                    return await _fetch_text_extract_by_identifier(
                        graphql_client, identifier
                    )

                return get_document_content

            resource_func = make_resource_func(doc_id, doc_name)

            mcp.resource(
                uri=resource_uri,
                name=f"[IBM CS] {doc_name}",
                description=f"IBM Content Services document from {graphql_client.object_store}: {folder_path}/{doc_name}",
                mime_type="text/plain",
                annotations=Annotations(audience=["assistant"], priority=0.8),
            )(resource_func)

        except Exception as e:
            logger.error("Error creating resource for %s: %s", doc_name, str(e))


def register_dynamic_resources(
    mcp: FastMCP, graphql_client: GraphQLClient, folder_path: str
) -> None:
    """Register dynamic resources from the specified folder."""
    documents = _list_dynamic_resources_folder_sync(graphql_client, folder_path)

    if documents:
        _register_resources_from_documents(mcp, graphql_client, folder_path, documents)

    # Refresh tool disabled - many MCP clients do not support dynamic resource updates
    # To refresh resources, restart the server
    # @mcp.tool(name="refresh_resources")
    # async def refresh_resources() -> None:
    #     """
    #     Refresh resources from the configured folder.
    #
    #     Scans the folder and re-registers resources for each document found.
    #     Use when resources have been added/updated.
    #     """
    #     documents = await _list_dynamic_resources_folder(graphql_client, folder_path)
    #     if documents:
    #         _register_resources_from_documents(mcp, graphql_client, folder_path, documents)
