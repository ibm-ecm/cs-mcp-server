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
legal_hold.py module define all MCP tools that provide legal hold functionality.

"""

import logging
import traceback
from typing import  Any, Union, Dict

from mcp.server.fastmcp import FastMCP

from cs_mcp_server.client.graphql_client import GraphQLClient, graphql_client_execute_async_wrapper
from cs_mcp_server.utils import HoldRelationship, Hold, ToolError
from cs_mcp_server.utils.constants import (
    CM_HOLD_CLASS,
    CM_HOLD_RELATIONSHIP_CLASS,
    ID_PROPERTY,
    TRACEBACK_LIMIT,
)
from cs_mcp_server.utils.model.admin import HeldObject


# Logger for this module
logger = logging.getLogger(__name__) 


def register_hold_tools(mcp: FastMCP, graphql_client: GraphQLClient) -> None:
    """
    Register to MCP server all the legal hold tools.
    """

    async def _find_hold_relationship_object(
        hold_object_id: str, held_object_id: str
    ) -> Union [ToolError, str, None]:
        """
        :returns: the id of the CmHoldRelationship object, or None if no relationship is found.
                 If an error occurs, returns a ToolError object.
        """
        method_name = "_find_hold_relationship_object"

        try:

            query = """
            query getCmRelationshipObject ($object_store_name: String!, 
                $where_clause: String!
                ) {
                    repositoryObjects(
                        repositoryIdentifier: $object_store_name,
                        from: "CmHoldRelationship",
                        where: $where_clause
                    ) {
                    independentObjects {
                        className
                        properties {
                            id
                            value
                        }
                    }
                }
            }
            """

            formatted_hold_value = f"({hold_object_id})"
            formatted_held_value = f"({held_object_id})"
            condition_string = f"[Hold] = Object {formatted_hold_value} and [HeldObject] = Object {formatted_held_value}"

            var = {
                "object_store_name": graphql_client.object_store,
                "where_clause": condition_string,
            }

            response: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                logger, method_name, graphql_client, query=query, variables=var)
            if isinstance   (response, ToolError):
                return response


            if "data" not in response or "repositoryObjects" not in response["data"] or "independentObjects" not in response["data"]["repositoryObjects"]:
                return None

            # return the id of the CmRelationshipObject
            hold_relationships = response["data"]["repositoryObjects"]["independentObjects"]
            # walk thru each relationship object,
            for item in hold_relationships:
                properties = item["properties"]
                for prop in properties:
                    if prop["id"] == ID_PROPERTY:
                        return prop["value"]
            return None
        except Exception as ex:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

            return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )



    @mcp.tool(
        name="delete_object_from_hold",
    )
    async def delete_object_from_hold(
        hold_id: str, held_id: str
    ) -> Union[str, ToolError]:
        """
        Remove a hold on a held object given a hold id and a held id.

        :param hold_id: The hold id.
        :param held_id: The held id.

        :returns: If successful, return a identifier of the Hold Relationship just deleted
                  Else, return a ToolError instance that describes the error.
        """

        #    A CmHoldRelationship is an object that has 2 fields to associate a Hold Id with a Held Id.

        #    To figure out the Hold Id, one can use the tool get_repository_object_main to look for
        #    objects of CmHold class given some criteria to look up a hold, for example a unique displayName.

        #    To figure out the Held Id, one can use the tool get_repository_object_main to look for
        #    objects of CmHoldable class given some criteria to look up a document, annotation, folder that
        #    should be removed from the hold.

        # look for an Object of CmHoldRelationship with the passed in Hold id and Held Id
        method_name = "delete_object_from_hold"
        try:
            hold_relationship_id = await _find_hold_relationship_object(hold_id, held_id)
            if hold_relationship_id is None:
                # Return a toolError 
                return ToolError(
                    message=f"{method_name} no_action_needed: No hold relationship found between the specified hold and held object.",
                )
            if isinstance (hold_relationship_id, ToolError):  # if the function returned a ToolError
                return hold_relationship_id

            mutation = """
            mutation ($object_store_name: String!, 
                $hold_relationship_class_name: String!, 
                $hold_relationship_id: String!
                ) {
                changeObject(
                    repositoryIdentifier: $object_store_name,
                    identifier: $hold_relationship_id,
                    classIdentifier: $hold_relationship_class_name,
                    actions:[
                    {
                        type:DELETE
                    }
                    ]
                ) {
                    className
                    objectReference {
                        repositoryIdentifier
                        classIdentifier
                        identifier
                    }
                    properties {
                        id
                        value
                    }
                }
            }
            """

            var = {
                "object_store_name": graphql_client.object_store,
                "hold_relationship_class_name": CM_HOLD_RELATIONSHIP_CLASS,
                "hold_relationship_id": hold_relationship_id,
            }

            response: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                logger, method_name, graphql_client, query=mutation, variables=var)
            if isinstance   (response, ToolError):
                return response

            # return the identifier of the Hold Relationship object just deleted
            return response["data"]["changeObject"]["objectReference"]["identifier"]
        except Exception as ex:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

            return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )

    @mcp.tool(
        name="delete_hold",
    )
    async def delete_hold(hold_object_id: str) -> Union[str, ToolError]:
        """
        Remove a hold.  This action will release all objects that are held by the hold identified
        by the hold_object_id.

        :param hold_object_id: The hold object id to which all the held objects are identified.

        :returns: If successful, return the Identifier of the hold object has just been deleted.
                  Else, return a ToolError instance that describes the error.
        """

        method_name = "delete_hold"
        try:
            mutation = """
            mutation ($object_store_name: String!, 
            	$hold_identifier: String!
                ) {
                changeObject(
                    classIdentifier: "CmHold",
                    identifier: $hold_identifier,
                    repositoryIdentifier: $object_store_name,
                    actions:[
                    {  
                        type:DELETE
                    }     
                    ]     
                )     
                {       
                    className
                    objectReference {
                        repositoryIdentifier
                        classIdentifier
                        identifier
                    }   
                    properties(includes:["Id"]) {
                        id  
                        label
                        type
                        cardinality
                        value
                    }
                }
            }
            """
            var = {
                "object_store_name": graphql_client.object_store,
                "hold_identifier": hold_object_id,
            }

            response: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                logger, method_name, graphql_client, query=mutation, variables=var)
            if isinstance   (response, ToolError):
                return response
            
            # return the information for all the objects that this hold now has
            return response["data"]["changeObject"]["objectReference"]["identifier"]
        except Exception as ex:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

            return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )

    @mcp.tool(
        name="create_hold",
    )
    async def create_hold(display_name: str, hold_class: str = CM_HOLD_CLASS) -> Union[Hold, ToolError]:
        """
        Create a hold with identifying information


        :param display_name: Value of display name for the newly created hold object.
        :param hold_class (optional): The hold class to instantiate a new object

        :returns: If successful, return a pydantic Hold object that describes the newly created object.
                  Else, return a ToolError instance that describes the error.
        """
        method_name = "create_a_hold"
        try:
            if not hold_class:
                hold_class = CM_HOLD_CLASS


            mutation = """
                    mutation ($object_store_name: String!, $class_name: String!, $display_name: String!) {
                    changeObject(
                        repositoryIdentifier: $object_store_name,
                        properties: [ {
                            displayName: $display_name
                        }
                        ]
                        actions:[
                        {
                            type:CREATE
                            subCreateAction:{
                                classId: $class_name
                            }
                        }
                        ]
                    )
                    {
                        className
                        properties {
                            id
                            value
                        }
                    }
                }
            """
            var = {
                "object_store_name": graphql_client.object_store,
                "class_name": hold_class,
                "display_name": display_name,
            }

            response: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                logger, method_name, graphql_client, query=mutation, variables=var)
            if isinstance   (response, ToolError):
                return response

            return Hold.create_an_instance(response["data"]["changeObject"])

        except Exception as ex:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

            return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )

    @mcp.tool(
        name="add_object_to_hold",
    )
    async def add_object_to_hold(
        hold_id: str, held_class: str, held_id: str
    ) -> Union[HoldRelationship, ToolError]:
        """
        Given an identifier for the hold, a class for the held object,
        an identifier for the held object, this tool will add the held object to the hold.

        If the held object is already in the hold, don't need to add it again.

        One can put multiple types of CmHoldable objects in a CmHold object. A CmHoldRelationship
        object is created to persist this relationship.
        Apply a hold to an object. A hold can be put on multiple objects. This tool allow user to add more objects to an existing hold

        :param hold_id:     The hold object id.
        :param held_class:  The held object class.
        :param held_id:     The held object id that is added to the hold.

        :returns: If successful, return a HoldRelationship instance that describes this relationship.
                  Else, return a ToolError instance that describes the error.
        """

        method_name = "add_object_to_hold"

        try:
            mutation = """
            mutation ($object_store_name: String!, 
                $hold_identifier: String!,
                $held_class_name: String!, $held_identifier: String!
                ) {
                changeObject(
                    repositoryIdentifier: $object_store_name
                    objectProperties:[
                    {
                        identifier:"Hold"
                        objectReferenceValue:{
                            identifier: $hold_identifier
                        }
                    }
                    {
                        identifier:"HeldObject"
                        objectReferenceValue:{
                            classIdentifier: $held_class_name
                            identifier: $held_identifier
                        }
                    }
                    ]
                    actions:[
                    {
                        type:CREATE
                        subCreateAction:{
                            classId:"CmHoldRelationship"
                        }
                    }
                    ]
                ) {
                    className
                    properties {
                        id
                        value
                    }
                }
            }
            """
            var = {
                "object_store_name": graphql_client.object_store,
                "hold_identifier": hold_id,
                "held_class_name": held_class,
                "held_identifier": held_id,
            }

            response: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                logger, method_name, graphql_client, query=mutation, variables=var)
            if isinstance   (response, ToolError):
                return response

            # return the information for the new/updated hold relationship
            # Note: There cam only exist 1 hold relationship between a unique hold and held object
            return HoldRelationship.create_an_instance(response["data"]["changeObject"])
        except Exception as ex:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

            return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )

    @mcp.tool(
        name="get_held_objects_for_hold",
    )
    async def get_held_objects_for_hold(
        hold_object_id: str,
    ) -> Union[list [HeldObject], ToolError]:
        """
        Given a hold object identified by its id, return all the objects that it held

        :param hold_object_id:     The hold object id.

        :returns: If successful, return a list of held objects.
                  Else, return a ToolError instance that describes the error.
        """
        method_name = "get_held_objects_for_hold"

        GET_HELD_OBJECTS_FOR_HOLD_QUERY = """ 
query getHeldObjectsForAHold ($object_store_name: String!, 
                $identifier: String!)
        {
  object(
    repositoryIdentifier: $object_store_name,
    classIdentifier:"CmHold",
    identifier: $identifier
  ) {
    className
    objectReference {
      repositoryIdentifier
      classIdentifier
      identifier
    }
    properties(includes:["Id", "CmHoldRelationships"]) {
      id
      value
      ... on EnumProperty {
        independentObjectSetValue {
          independentObjects {
            className
            objectReference {
              repositoryIdentifier
              classIdentifier
              identifier
            }
            properties(includes:["Id", "HeldObject"]) {
              id
              value
              ... on ObjectProperty {
                objectValue {
                  className
                  ... on Containable {
                    dateCreated
                    dateLastModified
                    name
                  }
                  ... on CustomObject {
                    customObjectId: id
                  }
                  ... on Document {
                    documentId:id
                  }
                  ... on Annotation {
                    annotationId: id
                    dateCreated
                    dateLastModified
                    name
                  }
                  ... on Folder {
                    folderId: id
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
        """

        try:

            var = {
                "object_store_name": graphql_client.object_store,
                "identifier": hold_object_id,
            }

            response: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                logger, method_name, graphql_client, query=GET_HELD_OBJECTS_FOR_HOLD_QUERY, variables=var)
            if isinstance   (response, ToolError):
                return response

            # extract the list of held objects from the graphQL response
            graphQL_held_objects_list = None    # initialization of the list of graphQL held objects
            # for every CmHoldRelationships property in the hold, get the list of held objects
            for hold_property in response["data"]["object"]["properties"]:
                if hold_property["id"] == "CmHoldRelationships":
                    graphQL_held_objects_list = hold_property["independentObjectSetValue"]["independentObjects"]  


            # walk thru each list of graphQL held objects annd create a list of pydantic HeldObject objects
            held_objects: list[HeldObject] = [] # initialize the list of pydantic HeldObject objects to be returned       
            if graphQL_held_objects_list is not None:
                for held_object in graphQL_held_objects_list:
                    a_held_object = HeldObject.create_an_instance(held_object)
                    held_objects.append(a_held_object)
 
            return held_objects

        except Exception as ex:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

            return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )

    @mcp.tool(
        name="get_holds_by_name", description="List all hold objects given a name"
    )
    async def get_holds_by_name(hold_display_name: str) -> Union[list[Hold], ToolError]:
        """
        Performs a case-insensitive substring search on the displayName field of CmHold objects, 
        returning all objects where the field contains the input hold_display_name string.

        :param hold_display_name: Search term for filtering holds by display name.

        :returns: If successful, returns a list of Hold objects where the objects's display name contains the input string.
                Each hold includes its identifier, displayName, and creator properties.
                If no matches are found, returns an empty result set.
                If an error occurs, returns a ToolError instance with error details.
        """
        method_name = "get_holds_by_name"
        logger.info(f"Enter MCP_LEGAL_HOLD {method_name}")
        try:
            query = """
            query getHoldsGivenAName ($object_store_name: String!, 
                $where_clause: String!, 
                ) {
                repositoryObjects(
                    repositoryIdentifier: $object_store_name,
                    from: "CmHold",
                    where: $where_clause
                ) {
                independentObjects {
                    className
                    properties (includes: ["Id", "DisplayName", "Creator"]) {
                        id
                        value
                    }
                }
                }
            }
            """

            formatted_value: str = f"'%{hold_display_name}%'"
            condition_string: str = (
                f"LOWER([DisplayName]) LIKE LOWER({formatted_value})"
            )

            var = {
                "object_store_name": graphql_client.object_store,
                "where_clause": condition_string,
            }

            response: Union [ToolError, Dict[str, Any]] = await graphql_client_execute_async_wrapper (
                logger, method_name, graphql_client, query=query, variables=var)
            if isinstance   (response, ToolError):
                return response

            # return holds with the display_name
            # convert GraphQL to Pydantic objects
            holds: list[Hold] = [
                Hold.create_an_instance(hold)
                for hold in response["data"]["repositoryObjects"]["independentObjects"]
            ]
            return holds    

        except Exception as ex:
            error_traceback = traceback.format_exc(limit=TRACEBACK_LIMIT)
            logger.error(
                f"{method_name} failed: {ex.__class__.__name__} - {str(ex)}\n{error_traceback}"
            )

            return ToolError(
                message=f"{method_name} failed: got err {ex}. Trace available in server logs.",
            )


