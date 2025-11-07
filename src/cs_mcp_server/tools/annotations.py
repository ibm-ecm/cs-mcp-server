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

import logging
import traceback
from typing import Union

from mcp.server.fastmcp import FastMCP

from cs_mcp_server.client.graphql_client import GraphQLClient
from cs_mcp_server.utils.common import ToolError
from cs_mcp_server.utils.constants import TRACEBACK_LIMIT

# Logger for this module
logger = logging.getLogger(__name__)


def register_annotation_tools(mcp: FastMCP, graphql_client: GraphQLClient) -> None:

    @mcp.tool(
        name="get_document_annotations_tool",
    )
    async def get_document_annotations_tool(
        document_id: str,
    ) -> Union[dict, ToolError]:
        """
        Retrieves all annotations associated with a document.

        This tool fetches annotation metadata including creator, dates, descriptive text,
        and content element information. Use this to analyze document annotations or
        to identify specific annotations for further processing.

        :param document_id: The document ID to retrieve annotations for.

        :returns: A dictionary containing document annotations with the following structure:
                - data.document.annotations.annotations: List of annotation objects, each containing:
                    - className: The class name of the annotation
                    - creator: The creator of the annotation
                    - dateCreated: Creation timestamp
                    - dateLastModified: Last modification timestamp
                    - id: Unique identifier of the annotation
                    - name: Name of the annotation
                    - owner: Owner of the annotation
                    - descriptiveText: Text description of the annotation
                    - contentSize: Size of the annotation content
                    - mimeType: MIME type of the annotation
                    - annotatedContentElement: Content element being annotated
                    - contentElementsPresent: Whether content elements are present
                    - contentElements: List of content elements with className, contentType, and sequence

                Returns ToolError if the document doesn't exist or another error occurs.
        """
        method_name: str = "get_document_annotations"

        if not document_id or not isinstance(document_id, str):
            return ToolError(
                message="Invalid document ID provided",
                suggestions=["Provide a valid document ID string"],
            )

        # Extract query to a constant for better maintainability
        ANNOTATIONS_QUERY = """
        query getDocumentAnnotations($object_store_name: String!, $document_id: String!){
            document(repositoryIdentifier: $object_store_name, identifier: $document_id){
                annotations {
                    annotations {
                        className
                        creator
                        dateCreated
                        dateLastModified
                        id
                        name
                        owner
                        descriptiveText
                        contentSize
                        mimeType
                        annotatedContentElement
                        contentElementsPresent
                        contentElements {
                            className
                            contentType
                            elementSequenceNumber
                        }
                    }
                }
            }
        }
        """

        variables = {
            "document_id": document_id,
            "object_store_name": graphql_client.object_store,
        }

        try:
            result = await graphql_client.execute_async(
                query=ANNOTATIONS_QUERY, variables=variables
            )

            # Check for GraphQL errors
            if "errors" in result:
                return ToolError(
                    message=f"GraphQL error: {result['errors'][0]['message']}",
                    suggestions=[
                        "Verify the document ID exists",
                        "Check if you have permission to access this document",
                    ],
                )

            # Check for empty or invalid response
            if (
                not result
                or "data" not in result
                or not result["data"]
                or "document" not in result["data"]
                or not result["data"]["document"]
                or "annotations" not in result["data"]["document"]
            ):
                return ToolError(
                    message="No annotations found or invalid document",
                    suggestions=[
                        "Verify the document exists",
                        "Check if the document has any annotations",
                    ],
                )

            return result

        except Exception as e:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {e.__class__.__name__} - {str(e)}\n{error_traceback}"
            )
            return ToolError(
                message=f"Error retrieving annotations: {str(e)}",
                suggestions=[
                    "Check network connectivity",
                    "Verify GraphQL endpoint is accessible",
                    "Ensure document ID is valid",
                ],
            )
