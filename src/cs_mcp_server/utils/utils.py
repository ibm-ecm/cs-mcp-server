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

from typing import List, Union, Optional
from cs_mcp_server.cache.metadata import MetadataCache
from cs_mcp_server.cache.metadata_loader import get_class_metadata_tool
from cs_mcp_server.client.graphql_client import GraphQLClient
from cs_mcp_server.utils import Cardinality, TypeID, ToolError
from cs_mcp_server.utils.constants import EXCLUDED_PROPERTY_NAMES, TRACEBACK_LIMIT
from cs_mcp_server.utils.constants import (
    TEXT_EXTRACT_ANNOTATION_CLASS,
    TEXT_EXTRACT_SEPARATOR,
)
from typing import  Any, Union, Dict
import time
from logging import Logger
import traceback


def get_class_specific_property_names(
    graphql_client: GraphQLClient, metadata_cache: MetadataCache, class_name: str
) -> Union[List[dict], ToolError]:
    """
    Retrieves a list of class-specific property metadata based on class definition.

    Filters out system properties, hidden properties, and properties with unsupported
    data types or cardinality.

    :param graphql_client: GraphQL client instance
    :param metadata_cache: Metadata cache instance
    :param class_name: The symbolic name of the class
    :returns: List of property dictionaries containing symbolicName, displayName,
              descriptiveText, dataType, and cardinality, or ToolError
    """
    # Get class metadata
    class_metadata = get_class_metadata_tool(
        graphql_client=graphql_client,
        class_symbolic_name=class_name,
        metadata_cache=metadata_cache,
    )

    if isinstance(class_metadata, ToolError):
        return class_metadata

    # Define filtering criteria
    not_allowed_cardinality = [Cardinality.ENUM]
    not_allowed_data_type = [TypeID.OBJECT, TypeID.BINARY]
    not_include_property_name = EXCLUDED_PROPERTY_NAMES

    # Filter properties
    property_list = []
    try:
        for prop in class_metadata.property_descriptions:
            if (
                prop.data_type in not_allowed_data_type
                or prop.cardinality in not_allowed_cardinality
                or prop.symbolic_name in not_include_property_name
                or prop.is_system_owned is True
                or prop.is_hidden is True
            ):
                continue

            # Create property info dictionary with requested fields
            property_info = {
                "symbolicName": prop.symbolic_name,
                "displayName": prop.display_name,
                "descriptiveText": prop.descriptive_text,
                "dataType": prop.data_type.value,  # Convert enum to string value
                "cardinality": prop.cardinality.value,  # Convert enum to string value
            }
            property_list.append(property_info)

        return property_list
    except Exception as e:
        return ToolError(
            message=f"Failed to extract property metadata: {str(e)}",
            suggestions=["Check if the class metadata is valid"],
        )


async def get_document_text_extract_content(
    graphql_client: GraphQLClient, identifier: str
) -> str:
    """
    Retrieves a document's text extract content.

    This utility function queries the document's annotations, filters for text extract
    annotations, and downloads the text content from each annotation's content elements.

    :param graphql_client: GraphQL client instance
    :param identifier: The document id or path (GUID or repository path)
    :returns: The concatenated text content from all text extract annotations.
             Returns empty string if no text extract is found.
    """
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

    # Execute query
    result = await graphql_client.execute_async(query=query, variables=variables)

    # Initialize empty string for text content
    all_text_content = ""

    # Check if we have valid result with annotations
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

        # Process each annotation
        for annotation in annotations:
            if (
                "contentElements" in annotation
                and annotation["className"] == TEXT_EXTRACT_ANNOTATION_CLASS
                and annotation["annotatedContentElement"] is not None
            ):
                # Process each content element
                for content_element in annotation["contentElements"]:
                    if (
                        "downloadUrl" in content_element
                        and content_element["downloadUrl"]
                    ):
                        # Download the text content
                        download_url = content_element["downloadUrl"]
                        text_content = await graphql_client.download_text_async(
                            download_url
                        )

                        # Append text content with separator
                        if text_content:
                            if all_text_content:
                                all_text_content += TEXT_EXTRACT_SEPARATOR
                            all_text_content += text_content

    return all_text_content

async def graphql_client_execute_async_wrapper (
    logger: Logger,
    method_name: str,
    graphql_client: GraphQLClient, 
    query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Union [ToolError, Dict[str, Any]]:
    "Wrapper for graphql_client.execute_async to handle errors, timing and logging of GraphQL queries."
    
    start_time = time.perf_counter()
    response = None
    try:
        logger.debug(f"{method_name}, GraphQL query: {query}, GraphQL variables: {variables} ") 
        response = await graphql_client.execute_async(query=query, variables=variables)
        if "errors" in response:
            error_message = response["errors"]
            logger.error(f"{method_name} failed: {error_message}")
            return ToolError(   message=f"{method_name} failed: got err {error_message}. Trace available in server logs.", )    

        if "error" in response:
            error_type = response.get("error_type", "")  # Get error_type if it exists, otherwise empty string               
            error_message = f"error_type = {error_type}, message = {response["message"]}"
            logger.error(f"{method_name} failed: {error_message}")
            return ToolError(   message=f"{method_name} failed: got err {error_message}. Trace available in server logs.", )    

        if "data" not in response or response["data"] is None:
            error_message = f" No 'data' returned from GraphQL query"
            logger.error(f"{method_name} failed: {error_message}")
            return ToolError(   message=f"{method_name} failed: got err {error_message}. Trace available in server logs.", )    

        return response 
    except Exception as ex:
        error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
        logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

        return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )
    finally:
        logger.debug(f"{method_name}, GraphQL response (elapse {time.perf_counter() - start_time:.2f}s): {response}") 

