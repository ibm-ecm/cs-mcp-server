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

from typing import Union

# Use absolute imports instead of relative imports
from cs_mcp_server.utils.common import (
    CacheClassDescriptionData,
    CachePropertyDescription,
    ToolError,
)


def get_root_class_description_tool(
    graphql_client,
    root_class_type: str,
    metadata_cache,
) -> Union[bool, ToolError]:
    """
    Retrieves all classes of a specific root class type (e.g., "Document", "Folder", "Annotation", "CustomObject).

    Args:
        graphql_client: The GraphQL client to use for queries
        root_class_type: The type of root class to retrieve (e.g., "Document", "Folder", "Annotation", "CustomObject")
        metadata_cache: The metadata cache instance to use

    Returns:
        True if the cache exists or was successfully filled, False otherwise, or a ToolError if an error occurs
    """
    # Ensure the root class exists in the cache
    metadata_cache.ensure_root_class_exists(root_class_type)

    # Check if we have any cached classes for this root class type
    class_cache = metadata_cache.get_class_cache(root_class_type)
    if class_cache:
        # Cache exists, return True
        return True

    # If no cached classes, fetch all classes of this type
    query = """
    query getClassAndSubclasses($object_store_name: String!, $root_class_name: String!, $page_size: Int!) {
        classDescription(
            repositoryIdentifier: $object_store_name
            identifier: $root_class_name
        ) {
            symbolicName
            displayName
            descriptiveText
        }
        subClassDescriptions(
            repositoryIdentifier: $object_store_name
            identifier: $root_class_name
            pageSize: $page_size
        ) {
            classDescriptions {
                symbolicName
                displayName
                descriptiveText
            }
        }
    }
    """

    variables = {
        "object_store_name": graphql_client.object_store,
        "root_class_name": root_class_type,
        "page_size": 500,
    }

    try:
        response = graphql_client.execute(query=query, variables=variables)

        # Check for errors in the response
        if "error" in response and response["error"]:
            return ToolError(
                message=f"Failed to retrieve classes for {root_class_type}: {response.get('message', 'Unknown error')}",
                suggestions=[
                    "Verify the root class type is correct",
                    "Check your connection to the repository",
                ],
            )

        # Process the response
        data = response.get("data", {})
        root_class_info = data.get("classDescription", {})
        subclasses = data.get("subClassDescriptions", {}).get("classDescriptions", [])

        if not root_class_info and not subclasses:
            return ToolError(
                message=f"No classes found for root class type '{root_class_type}'",
                suggestions=[
                    "Check if the root class type is correct",
                    "Verify that classes of this type exist in the repository",
                ],
            )

        # Cache the root class with basic information
        if root_class_info:
            root_class_data = CacheClassDescriptionData(
                display_name=root_class_info.get("displayName", ""),
                symbolic_name=root_class_info.get("symbolicName", ""),
                descriptive_text=root_class_info.get("descriptiveText", ""),
                property_descriptions=[],  # Empty list for now
                name_property_symbolic_name=None,  # To be filled in when property descriptions loaded
            )

            # Cache the root class under its own key (e.g., "Document" -> "Document")
            # This ensures the root class itself is included in the cache
            metadata_cache.set_class_data(
                root_class_type, root_class_type, root_class_data
            )

        # Cache the subclasses with basic information
        for subclass in subclasses:
            symbolic_name = subclass.get("symbolicName", "")

            # Create a ContentClassData object with empty properties list
            class_data = CacheClassDescriptionData(
                display_name=subclass.get("displayName", ""),
                symbolic_name=symbolic_name,
                descriptive_text=subclass.get("descriptiveText", ""),
                property_descriptions=[],  # Empty list for now
                name_property_symbolic_name=None,  # To be filled in when property descriptions loaded
            )

            metadata_cache.set_class_data(root_class_type, symbolic_name, class_data)

        # Successfully filled the cache
        return True

    except Exception as e:
        return ToolError(
            message=f"Failed to retrieve classes for {root_class_type}: {str(e)}",
            suggestions=[
                "Verify the root class type is correct",
                "Check your connection to the repository",
            ],
        )


def get_class_metadata_tool(
    graphql_client,
    class_symbolic_name: str,
    metadata_cache,
) -> Union[CacheClassDescriptionData, ToolError]:
    """
    Retrieves detailed metadata about a repository class including its properties.

    Args:
        graphql_client: The GraphQL client to use for queries
        class_symbolic_name: The symbolic name of the class
        metadata_cache: The metadata cache instance to use

    Returns:
        A ContentClassData object containing class metadata or a ToolError if an error occurs
    """
    # First, determine which root class this belongs to
    root_class = metadata_cache.find_root_class_for_class(class_symbolic_name)

    if root_class is None:
        existing_class_data = None
    else:
        existing_class_data = metadata_cache.get_class_data(
            root_class, class_symbolic_name
        )
        if existing_class_data and len(existing_class_data.property_descriptions) > 0:
            return existing_class_data

    query = """
    query getClassMetadata($object_store_name: String!, $class_symbolic_name: String!) {
    classDescription(
        repositoryIdentifier: $object_store_name
        identifier: $class_symbolic_name
    ) {
        namePropertyIndex
        propertyDescriptions {
            symbolicName
            displayName
            descriptiveText
            dataType
            cardinality
            isSearchable
            isSystemOwned
            isHidden
        }
    }
    }
    """

    variables = {
        "object_store_name": graphql_client.object_store,
        "class_symbolic_name": class_symbolic_name,
    }

    try:
        response = graphql_client.execute(query=query, variables=variables)

        # Check for errors in the response
        if "error" in response and response["error"]:
            return ToolError(
                message=f"Failed to retrieve metadata for class {class_symbolic_name}: {response.get('message', 'Unknown error')}",
                suggestions=[
                    "Verify the class name is correct",
                    "Check your connection to the repository",
                ],
            )

        # Process the response to make it more useful
        class_data = response.get("data", {}).get("classDescription", {})

        if not class_data:
            return ToolError(
                message=f"Class '{class_symbolic_name}' not found",
                suggestions=[
                    "Check the class name",
                    "Use get_root_class_description to see available classes",
                ],
            )

        # Convert the GraphQL response to our model objects
        property_descriptions = []
        name_prop_idx: int | None = class_data.get("namePropertyIndex", None)
        name_prop_sym_name: str | None = None
        for idx, prop in enumerate(class_data.get("propertyDescriptions", [])):
            prop_sym_name: str = prop.get("symbolicName")
            if name_prop_idx and idx == name_prop_idx:
                name_prop_sym_name = prop_sym_name
            property_descriptions.append(
                CachePropertyDescription(
                    symbolic_name=prop_sym_name,
                    display_name=prop.get("displayName"),
                    descriptive_text=prop.get("descriptiveText", ""),
                    data_type=prop.get("dataType"),
                    cardinality=prop.get("cardinality"),
                    is_searchable=prop.get("isSearchable", False),
                    is_system_owned=prop.get("isSystemOwned", False),
                    is_hidden=prop.get("isHidden", False),
                    valid_search_operators=[],  # This would need to be populated based on data type
                )
            )

        # If we already have class data, just update the properties
        if existing_class_data:
            existing_class_data.property_descriptions = property_descriptions
            existing_class_data.name_property_symbolic_name = name_prop_sym_name
            content_class_data = existing_class_data
        else:
            # Otherwise create a new ContentClassData with the class name as placeholder
            content_class_data = CacheClassDescriptionData(
                display_name=class_symbolic_name,
                symbolic_name=class_symbolic_name,
                descriptive_text="",
                property_descriptions=property_descriptions,
                name_property_symbolic_name=name_prop_sym_name,
            )

        # Cache the full class description only if we know the root class
        if root_class is not None:
            metadata_cache.set_class_data(
                root_class, class_symbolic_name, content_class_data
            )

        # Return the ContentClassData object directly
        return content_class_data

    except Exception as e:
        return ToolError(
            message=f"Failed to retrieve metadata for class {class_symbolic_name}: {str(e)}",
            suggestions=[
                "Verify the class name is correct",
                "Check your connection to the repository",
            ],
        )
