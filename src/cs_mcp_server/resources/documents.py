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
Document Resources Module

This module provides resource definitions for accessing document content and metadata.
Resources are read-only and provide context to language models without executing operations.
"""

import logging
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from mcp.types import Annotations

from cs_mcp_server.client.graphql_client import GraphQLClient
from cs_mcp_server.utils.constants import (
    TEXT_EXTRACT_ANNOTATION_CLASS,
    TEXT_EXTRACT_SEPARATOR,
)

# Logger for this module
logger = logging.getLogger(__name__)


async def _fetch_text_extract_by_identifier(
    graphql_client: GraphQLClient, identifier: str
) -> str:
    """Fetch text extract content for a document by ID or path."""

    query = """
    query getDocumentTextExtract($object_store_name: String!, $identifier: String!) {
        document(repositoryIdentifier: $object_store_name, identifier: $identifier) {
            annotations{
                annotations{
                    id
                    name
                    className
                    annotatedContentElement
                    descriptiveText
                    contentElements{
                        ... on ContentTransfer{
                            downloadUrl
                            retrievalName
                            contentSize
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "identifier": identifier,
        "object_store_name": graphql_client.object_store,
    }

    try:
        result = await graphql_client.execute_async(query=query, variables=variables)

        if "errors" in result:
            logger.error("GraphQL errors in text extract query: %s", result["errors"])

        all_text_content = ""

        if (
            result
            and "data" in result
            and result["data"]
            and "document" in result["data"]
            and result["data"]["document"]
            and "annotations" in result["data"]["document"]
            and result["data"]["document"]["annotations"]
            and "annotations" in result["data"]["document"]["annotations"]
        ):
            annotations = result["data"]["document"]["annotations"]["annotations"]

            for annotation in annotations:
                if (
                    "contentElements" in annotation
                    and annotation["className"] == TEXT_EXTRACT_ANNOTATION_CLASS
                    and annotation["annotatedContentElement"] is not None
                ):
                    for content_element in annotation["contentElements"]:
                        if (
                            "downloadUrl" in content_element
                            and content_element["downloadUrl"]
                        ):
                            download_url = content_element["downloadUrl"]
                            text_content = await graphql_client.download_text_async(
                                download_url
                            )

                            if text_content:
                                if all_text_content:
                                    all_text_content += TEXT_EXTRACT_SEPARATOR
                                all_text_content += text_content

        return all_text_content

    except Exception as e:
        logger.error("Error fetching text extract for %s: %s", identifier, str(e))
        return f"Error retrieving text extract: {str(e)}"
