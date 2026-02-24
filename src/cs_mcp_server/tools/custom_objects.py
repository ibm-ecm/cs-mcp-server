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

from typing import Any, Dict, Union
from cs_mcp_server.utils.constants import (
    TRACEBACK_LIMIT,
)

from mcp.server.fastmcp import FastMCP

from cs_mcp_server.client.graphql_client import GraphQLClient, graphql_client_execute_async_wrapper
from cs_mcp_server.utils import ToolError
from cs_mcp_server.utils.model.core import  CustomObject


# Logger for this module
logger = logging.getLogger(__name__)


def register_custom_object_tools(mcp: FastMCP, graphql_client: GraphQLClient) -> None:
    @mcp.tool(
        name="get_custom_object",
    )
    async def get_custom_object(
        custom_object_id: str,
    ) -> Union[CustomObject, ToolError]:
        """
        Retrieves an CustomObject associated with an customObject id.

        This tool fetches custom object metadata. 

        :param custom_object_id: The customObject ID to retrieve information for.

        :returns: a CustomObject object or
                 ToolError if the custom Object doesn't exist or another error occurs.
        """
        method_name: str = "get_a_custom_object"

        if not custom_object_id or not isinstance(custom_object_id, str):
            return ToolError(
                message="Invalid custom object ID provided",
                suggestions=["Provide a valid custom object ID string"],
            )

        # Extract query to a constant for better maintainability
        A_CUSTOM_OBJECT_QUERY = """
        query getACustomObject ($object_store_name: String!, $custom_object_id: String!){
            customObject(repositoryIdentifier: $object_store_name, identifier: $custom_object_id){
                        className
                        creator
                        dateCreated
                        dateLastModified
                        id
                        name
                        owner
                    }
        }
        """

        variables = {
            "custom_object_id": custom_object_id,
            "object_store_name": graphql_client.object_store,
        }

        try:
            result: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                    logger, method_name, graphql_client, query=A_CUSTOM_OBJECT_QUERY, variables=variables)
            if isinstance   (result, ToolError):
                return result

            # Check for no result returned before checking if there is "errors" key in the result dictionary
            if result is None:
                return ToolError(
                    message="No custom object found or invalid custom object id",
                    suggestions=[
                        "Verify the custom object exists",
                        "Check if you have permission to access this custom object",
                    ],
                )

            # Check for GraphQL errors
            if "errors" in result:
                return ToolError(
                    message=f"GraphQL error: {result['errors'][0]['message']}",
                    suggestions=[
                        "Verify the custom object ID exists",
                        "Check if you have permission to access this custom object",
                    ],
                )

            # Check for empty or invalid response
            if (
                not result
                or "data" not in result
                or not result["data"]
                or "customObject" not in result["data"]
            ):
                return ToolError(
                    message="No custom object found",
                    suggestions=[
                        "Verify the custom object exists",
                    ],
                )


 
            a_custom_object = CustomObject.create_an_instance(
                graphQL_changed_object_dict=result["data"]["customObject"],
                class_name=result["data"]["customObject"]["className"],
            )

            return a_custom_object

        except Exception as e:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {e.__class__.__name__} - {str(e)}\n{error_traceback}"
            )
            return ToolError(
                message=f"Error retrieving custom object: {str(e)}",
                suggestions=[
                    "Check network connectivity",
                    "Verify GraphQL endpoint is accessible",
                    "Ensure custom object ID is valid",
                ],
            )
