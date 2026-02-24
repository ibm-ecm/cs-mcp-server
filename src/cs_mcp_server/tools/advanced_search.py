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

from typing import Any, Union, Dict

from mcp.server.fastmcp import FastMCP

from cs_mcp_server.cache.metadata import MetadataCache
from cs_mcp_server.cache.metadata_loader import get_class_metadata_tool
from cs_mcp_server.client.graphql_client import (
    GraphQLClient,
    graphql_client_execute_async_wrapper,
)
from cs_mcp_server.utils.common import SearchParameters, ToolError
from cs_mcp_server.utils.model.core import Document
from cs_mcp_server.utils.constants import (
    VERSION_STATUS_RELEASED,
)
from cs_mcp_server.utils.utils import (
    process_search_parameters,
)

# Logger for this module
logger: logging.Logger = logging.getLogger(__name__)


def register_advanced_search_tools(
    mcp: FastMCP,
    graphql_client: GraphQLClient,
    metadata_cache: MetadataCache,
) -> None:
    @mcp.tool(name="document_smart_search")
    async def document_smart_search(
        vector_prompt: str,
        search_parameters: SearchParameters,
    ) -> list | ToolError:
        """
        **PREREQUISITES IN ORDER**: To use this tool, you MUST call two other tools first in a specific sequence.
        1. determine_class tool to get the class_name for search_class.
        2. get_searchable_property_descriptions to get a list of valid property_name for search_properties

        Description:
        Performs a hybrid search combining vector (semantic) search and metadata filtering to find documents. Use this to find relevant documents based on meaning rather than just keywords. Returns documents ranked by a GenaiScore.

        :param vector__prompt: The prompt for vector search. This will be used to search for documents based on their content.
        :param search_parameters (SearchParameters): provide parameters search_class and the search conditions.
          Note the search_class is filled in by determine_class tool.
          search_properties inside search_parameters include any property being searched for and any search conditions.


        :returns: the repository object details, including:
            - GenaiScore and each corresponding document (list): a list of dictionary which containing GenaiScore and corresponding document:
                - GenaiScore: the score rank for vector search regarding content query
                - Document: the document object details, including:
                    - id: the document id
                    - name: the document name
                    - properties (list): A list of properties, each containing:
                        - label (str): The name of the property.
                        - value (str): The value of the property.

        Example: find docs with content related to 2023 budget and created by John Doe, the input would be:
        vevtor__prompt: "2023 budget"
        search_parameters:
        {
            "search_class":"Document",
            "search_properties": [
                {
                "property_name": "Creator",
                "property_value": "John Doe",
                "operator": "CONTAINS"
                }
            ]
            }
        """
        # First, get the search condition and return properties

        method_name = "document_smart_search"

        search_properties_string = None
        return_properties = ["GenaiScore"]

        result = await process_search_parameters(
            graphql_client, metadata_cache, search_parameters=search_parameters
        )

        # Check if we got an error
        if isinstance(result, ToolError):
            return result

        # Unpack the result tuple
        search_properties_string, return_properties = result
        if vector_prompt:
            return_properties.append("GenaiScore")
        return_properties_with_brackets = [f"[{prop}]" for prop in return_properties]

        logger.info("search property string:" + (search_properties_string or ""))
        logger.info("return_properties string:" + str(return_properties))
        query = """
        query advanced_doc_search($object_store_name: String!,
             $where_statement: String!){
            repositoryRows(
            repositoryIdentifier: $object_store_name,
            
            sql: $where_statement
            ) 
    				{
              repositoryRows {
                 properties {
                  id
                  type
                  cardinality
                  value
                }
              }
  					}
        }
        """
        prompt = vector_prompt
        escaped_prompt = prompt.replace("'", "''")
        prompt_sql = ""
        if escaped_prompt:
            prompt_sql = (
                f"SELECT "
                + ", ".join(return_properties_with_brackets)
                + f" FROM GenAI::VectorSearch({search_parameters.search_class},'{escaped_prompt}')"
            )
        else:
            prompt_sql = (
                f"SELECT "
                + ", ".join(return_properties_with_brackets)
                + f" FROM {search_parameters.search_class}"
            )

        logger.info("prompt_sql:" + prompt_sql)
        # Add WHERE clause if there are additional search properties
        if search_properties_string:
            sql = f"{prompt_sql} WHERE {search_properties_string} and VersionStatus={VERSION_STATUS_RELEASED}"
        else:
            sql = prompt_sql + f" WHERE VersionStatus={VERSION_STATUS_RELEASED}"

        var = {"object_store_name": graphql_client.object_store, "where_statement": sql}

        try:
            docs: Union[ToolError, Dict[str, Any]] = (
                await graphql_client_execute_async_wrapper(
                    logger, method_name, graphql_client, query=query, variables=var
                )
            )
            if isinstance(docs, ToolError):
                return docs

            docslist = docs["data"]["repositoryRows"]["repositoryRows"]
            if len(docslist) == 0:
                return []
            else:
                contained_docs = []
                for doc in docslist:
                    properties = doc["properties"]
                    id_value = None
                    score = None
                    for prop in properties:
                        if prop["id"] == "Id":
                            id_value = prop["value"]
                            logger.info("doc id is:" + id_value)
                        if prop["id"] == "GenaiScore":
                            score = prop["value"]

                    doc_with_id = {"id": id_value}
                    doc_with_id |= doc
                    onedoc = Document.create_an_instance(
                        graphQL_changed_object_dict=doc_with_id,
                    )
                    onedoc_withscore = {
                        "GenaiScore": score,
                        "document": onedoc,
                    }
                    contained_docs.append(onedoc_withscore)
                return contained_docs

        except Exception as e:
            return ToolError(
                message=f"Error executing advanced document search: {str(e)}",
                suggestions=[
                    "Check that all property names are valid for the class",
                    "Ensure property values match the expected data types",
                    "Verify that the operators are appropriate for the property data types",
                ],
            )

    @mcp.tool(name="document_quick_summary")
    async def document_quick_summary(
        document_ids: list,
    ) -> Union[str, ToolError]:
        """
        Description:
        Generates a concise AI-powered summary for one or more provided document IDs. Use this to give the user a quick overview of content without reading the full text.

        :param document_ids: The ids of the documents to be summarized.

        :returns: the summary string or ToolError.
        """
        method_name = "document_quick_summary"
        query = """
                mutation createGenaiSummary($repo:String!, $identifiers:[String!],
        $className:String!){
                createCmAbstractPersistable(repositoryIdentifier: $repo, 
                
                classIdentifier:$className,
                cmAbstractPersistableProperties:
                {
                    properties:[  
                                               
                                {GenaiMaxSummaryWords:500},
                            {GenaiContextDocuments: 
                                
                                    $identifiers
                                
                            }
                        ],
                })
                {
                    id
                    name
                    properties(includes:["GenaiLLMResponse", "GenaiLLMModelName"])
                    {
                        alias
                        value
                    }
            }
        }"""
        var = {
            "repo": graphql_client.object_store,
            "identifiers": document_ids,
            "className": "GenaiAdhocSummary",
        }

        results: Union[ToolError, Dict[str, Any]] = (
            await graphql_client_execute_async_wrapper(
                logger, method_name, graphql_client, query=query, variables=var
            )
        )
        if isinstance(results, ToolError):
            return results
        return results["data"]["createCmAbstractPersistable"]["properties"][0]["value"]

    @mcp.tool(name="document_compare_insights")
    async def document_compare_insights(
        document_id1: str,
        document_id2: str,
    ) -> Union[str, ToolError]:
        """
        Description:
        Compares exactly two documents to identify similarities, differences, and version changes. Returns an AI-generated analysis.


        :param document_id1: The id of the first document to be compared.
        :param document_id2: The id of the second document to be compared.

        :returns: the comparison result or ToolError.
        """
        method_name = "document_compare_insights"

        query = """
                mutation createGenaiDocCompareWithProps($repo:String!, $className:String!,$props:[PropertyIdentifierAndScalarValue!]
                    ){
                            createCmAbstractPersistable(repositoryIdentifier: $repo, 
                            classIdentifier:$className,
                            cmAbstractPersistableProperties:
                            {
                                properties:$props
                            })
                            {
                                id
                                name
                                properties(includes:["GenaiLLMResponse"])
                                {
                                    alias
                                    value
                                }
                        }
                    }"""

        props = [
            {
                "GenaiContextDocument": {
                    "identifier": document_id1,
                    "classIdentifier": "{01A3A8C2-7AEC-11D1-A31B-0020AF9FBB1C}",
                }
            },
            {
                "GenaiContextDocument2": {
                    "identifier": document_id2,
                    "classIdentifier": "{01A3A8C2-7AEC-11D1-A31B-0020AF9FBB1C}",
                }
            },
        ]

        var = {
            "repo": graphql_client.object_store,
            "props": props,
            "className": "GenaiDocumentComparison",
        }
        logger.info(f"Executing query: {query}")
        logger.info(f"Executing var: {var}")

        results: Union[ToolError, Dict[str, Any]] = (
            await graphql_client_execute_async_wrapper(
                logger, method_name, graphql_client, query=query, variables=var
            )
        )
        if isinstance(results, ToolError):
            return results
        return results["data"]["createCmAbstractPersistable"]["properties"][0]["value"]
