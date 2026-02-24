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

import logging
import traceback
from typing import Any, Union

from mcp.server.fastmcp import FastMCP

from cs_mcp_server.cache.metadata import MetadataCache
from cs_mcp_server.client.graphql_client import GraphQLClient
from cs_mcp_server.utils.common import ToolError
from cs_mcp_server.utils.utils import get_class_specific_property_names
from cs_mcp_server.utils.utils import get_document_text_extract_content

# Logger for this module
logger = logging.getLogger(__name__)


def register_property_extraction_tools(
    mcp: FastMCP, graphql_client: GraphQLClient, metadata_cache: MetadataCache
) -> None:
    @mcp.tool(
        name="property_extraction",
    )
    async def property_extraction(identifier: str) -> Union[dict, ToolError]:
        """
        Use this tool for property extraction workflow when you need to extract property values from a document's content/text.

        This tool first determines the document's class, then fetches the class metadata to identify
        all available properties specific to that document class. It filters out system properties and
        hidden properties.

        It also retrieves a document's text extract content.

        :param identifier: The document id or path (required). This can be either the document's ID (GUID)
                          or its path in the repository (e.g., "/Folder1/document.pdf").

        :returns: A dictionary containing:
                 - text_extract: The text content of the document's text extract annotation.
                   If multiple text extracts are found, they will be concatenated.
                 - properties: A list of property metadata dictionaries with symbolicName, displayName,
                   descriptiveText, dataType, and cardinality fields.
        """
        text_extract = await get_document_text_extract_content(
            graphql_client=graphql_client, identifier=identifier
        )

        # First, get the class name of the document
        query = """
        query getDocument($object_store_name: String!, $identifier: String!){
            document(repositoryIdentifier: $object_store_name, identifier: $identifier){
                className
            }
        }
        """

        variables: dict[str, Any] = {
            "identifier": identifier,
            "object_store_name": graphql_client.object_store,
        }

        response = graphql_client.execute(query=query, variables=variables)

        if "errors" in response:
            return response

        class_name = response["data"]["document"]["className"]

        properties = await get_class_specific_property_names(
            graphql_client=graphql_client,
            metadata_cache=metadata_cache,
            class_name=class_name,
        )

        return {"text_extract": text_extract, "properties": properties}
