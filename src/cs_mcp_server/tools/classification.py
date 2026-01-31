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
Classification Tools Module

This module provides tools for document classification workflows, including
listing available classes, determining the best class match, and updating
document classes.
"""

import logging
from typing import Any, List, Union

from mcp.server.fastmcp import FastMCP

from cs_mcp_server.cache.metadata import MetadataCache
from cs_mcp_server.cache.metadata_loader import get_root_class_description_tool
from cs_mcp_server.client.graphql_client import GraphQLClient
from cs_mcp_server.utils.common import (
    CacheClassDescriptionData,
    ClassDescriptionData,
    ToolError,
)

# Logger for this module
logger = logging.getLogger(__name__)


def register_classification_tools(
    mcp: FastMCP, graphql_client: GraphQLClient, metadata_cache: MetadataCache
) -> None:
    """
    Register classification-specific tools with the MCP server.

    These tools support document classification workflows by providing
    access to class metadata and enabling class-based operations.

    Args:
        mcp: The FastMCP instance to register tools with
        graphql_client: The GraphQL client to use for queries
        metadata_cache: The metadata cache to use for class information
    """

    @mcp.tool(
        name="list_all_classes",
    )
    def list_all_classes_tool(
        root_class: str,
    ) -> Union[List[ClassDescriptionData], ToolError]:
        """
        List all available classes for a specific root class type.

        IMPORTANT: Only use this tool when the user explicitly asks to see a list of classes of a specific root class,
        OR when performing document reclassification workflows where you need to match document content
        to the most appropriate class. For reclassification, call with root_class="Document" to get all available
        document classes, then analyze the document content to select the best matching class.

        If a user does not specify a root_class, you **MUST** request the root class from them.
        To get a list of all valid root class names that can be used with this tool, you can call the `list_root_classes_tool` tool.

        :param root_class: The root class to list all classes for (e.g., "Document", "Folder", "Annotation", "CustomObject")

        :returns: A list of all classes for the specified root class, or a ToolError if an error occurs
        """
        # Validate root_class parameter by checking the cache keys
        if root_class not in metadata_cache.get_root_class_keys():
            return ToolError(
                message=f"Invalid root class '{root_class}'. Root class must be one of: {metadata_cache.get_root_class_keys()}",
                suggestions=[
                    "Use list_root_classes tool first to get valid root class names",
                ],
            )

        # First, ensure the root class cache is populated
        root_class_result = get_root_class_description_tool(
            graphql_client=graphql_client,
            root_class_type=root_class,
            metadata_cache=metadata_cache,
        )

        # If there was an error populating the root class cache, return it
        if isinstance(root_class_result, ToolError):
            return root_class_result

        # Get all classes for the specified root class
        all_classes = metadata_cache.get_class_cache(root_class)

        if not all_classes:
            return ToolError(
                message=f"No classes found for root class '{root_class}'",
                suggestions=[
                    "Check if the metadata cache is properly populated",
                    "Try refreshing the class metadata",
                ],
            )

        # Convert all classes to ClassDescriptionData objects
        result = []
        for class_name, class_data in all_classes.items():
            # Skip if class_data is not a CacheClassDescriptionData object
            if not isinstance(class_data, CacheClassDescriptionData):
                continue

            # Use model_validate to convert CacheClassDescriptionData to ClassDescriptionData
            class_desc_data = ClassDescriptionData.model_validate(class_data)
            result.append(class_desc_data)

        # Sort results by symbolic name for consistency
        result.sort(key=lambda x: x.symbolic_name)

        return result
