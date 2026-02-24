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


async def get_class_specific_property_names(
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
    class_metadata = await get_class_metadata_tool(
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


async def process_search_parameters(
    graphql_client: GraphQLClient,
    metadata_cache: MetadataCache,
    search_parameters,
) -> Union[tuple, ToolError]:
    """
    Process search parameters to generate search conditions and return properties.

    This function retrieves class metadata, extracts property information,
    and formats search conditions based on the provided search parameters.

    :param graphql_client: GraphQL client instance for accessing object store info
    :param metadata_cache: Metadata cache instance for retrieving class information
    :param search_parameters: SearchParameters object containing:
        - search_class: The class name to search
        - search_properties: List of property search conditions
    :returns: A tuple of (search_properties_string, return_properties) where:
        - search_properties_string: SQL WHERE clause string
        - return_properties: List of property names to return
        Or ToolError if processing fails
    """
    from cs_mcp_server.utils.constants import (
        DATA_TYPE_STRING,
        DATA_TYPE_INTEGER,
        DATA_TYPE_LONG,
        DATA_TYPE_FLOAT,
        DATA_TYPE_DOUBLE,
        DATA_TYPE_BOOLEAN,
        DATA_TYPE_DATETIME,
        DATA_TYPE_DATE,
        DATA_TYPE_TIME,
        DATA_TYPE_OBJECT,
        CARDINALITY_LIST,
        SQL_LIKE_OPERATOR,
        OPERATOR_CONTAINS,
        OPERATOR_STARTS,
        OPERATOR_ENDS,
    )

    # Helper function to format values by type
    def format_value_by_type(value, data_type):
        """Format a value according to its data type."""
        # Return value directly for numeric, boolean, and date/time types
        if data_type in [
            DATA_TYPE_INTEGER,
            DATA_TYPE_LONG,
            DATA_TYPE_FLOAT,
            DATA_TYPE_DOUBLE,
            DATA_TYPE_BOOLEAN,
            DATA_TYPE_DATETIME,
            DATA_TYPE_DATE,
            DATA_TYPE_TIME,
        ]:
            return value
        # Default to string (quoted) for all other types
        return f"'{value}'"

    # Get the class metadata from the cache
    class_data = await get_class_metadata_tool(
        graphql_client, search_parameters.search_class, metadata_cache
    )

    # Check if we got an error instead of class data
    if isinstance(class_data, ToolError):
        return class_data

    # Extract property information from the class data
    return_properties = []
    property_types = {}

    for prop in class_data.property_descriptions:
        # Skip properties with LIST cardinality or OBJECT data type
        if prop.cardinality == CARDINALITY_LIST or prop.data_type == DATA_TYPE_OBJECT:
            continue

        property_name = prop.symbolic_name
        return_properties.append(property_name)
        # logger.info(f"Adding property {property_name} to return properties")
        property_types[property_name] = prop.data_type

    # logger.info(f"Return properties: {return_properties}")
    # Process search conditions
    query_conditions = []
    for item in search_parameters.search_properties:
        try:
            prop_name = item.property_name
        except AttributeError:
            return ToolError(
                message="search_properties missing 'property_name' key",
                suggestions=["Ensure each search property has a 'property_name' field"],
            )
        try:
            prop_value = item.property_value.replace("*", "")
        except AttributeError:
            return ToolError(
                message="search_properties missing 'property_value' key",
                suggestions=[
                    "Ensure each search property has a 'property_value' field"
                ],
            )
        try:
            operator = item.operator.value
        except AttributeError:
            return ToolError(
                message="search_properties missing 'operator' key",
                suggestions=["Ensure each search property has an 'operator' field"],
            )

        if not all([prop_name, prop_value, operator]):
            print(f"Skipping invalid filter item: {item}")
            continue

        # Get the data type of the property
        data_type = property_types.get(
            prop_name, DATA_TYPE_STRING
        )  # Default to STRING if not found

        # Format the value according to its data type
        formatted_value = format_value_by_type(prop_value, data_type)

        # Handle string operations
        if data_type == DATA_TYPE_STRING:
            if operator.upper() == OPERATOR_CONTAINS:
                operator = SQL_LIKE_OPERATOR
                formatted_value = f"'%{prop_value}%'"
            elif operator.upper() == OPERATOR_STARTS:
                operator = SQL_LIKE_OPERATOR
                formatted_value = f"'{prop_value}%'"
            elif operator.upper() == OPERATOR_ENDS:
                operator = SQL_LIKE_OPERATOR
                formatted_value = f"'%{prop_value}'"

        condition_string = f"{prop_name} {operator} {formatted_value}"
        query_conditions.append(condition_string)

    search_properties_string = " AND ".join(query_conditions)

    return (search_properties_string, return_properties)
