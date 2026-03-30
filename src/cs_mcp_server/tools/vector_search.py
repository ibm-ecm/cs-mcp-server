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

import json
import os
import uuid
from typing import Optional, Union, Dict, Any

from fastmcp import FastMCP

from cs_mcp_server.client.graphql_client import (
    GraphQLClient,
    graphql_client_execute_async_wrapper,
)
from cs_mcp_server.utils.common import ToolError
from cs_mcp_server.utils.constants import (
    DEFAULT_MAX_CHUNKS,
    DEFAULT_RELEVANCE_SCORE,
    GENAI_VECTOR_QUERY_CLASS,
)
from logging import Logger
import logging

# Logger for this module
logger: Logger = logging.getLogger(__name__)

# Environment variables for configuration
MAX_CHUNKS = int(os.environ.get("MAX_CHUNKS", DEFAULT_MAX_CHUNKS))
GENAI_LLM_MODEL_NAME = os.environ.get("GENAI_LLM_MODEL_NAME")
RELEVANCE_SCORE = float(os.environ.get("RELEVANCE_SCORE", DEFAULT_RELEVANCE_SCORE))


def register_vector_search_tool(mcp: FastMCP, graphql_client: GraphQLClient) -> None:
    @mcp.tool(name="document_qa_global")
    async def document_qa_global(
        prompt: str,
        return_chunks: Optional[bool] = False,
        llm_model_name: Optional[str] = None,
        number_of_chunks: Optional[int] = None,
    ) -> Union[list, ToolError]:
        """
        Answers natural language questions by scanning the entire document repository. Use this for broad questions where the specific documents are not known or when looking for patterns across the entire document repository.

        :param prompt: The question to ask
        :param return_chunks: Optional, Whether to return the chunks of the document that were used to answer the question
        :param ll_model_name: Optional, if specify, use this llm model for query
        returns: A list of doc ids or a list of doc chunks with id
        """
        method_name = "document_qa_global"
        if llm_model_name is None:
            llm_model_name = GENAI_LLM_MODEL_NAME
        max_chunks = MAX_CHUNKS
        if number_of_chunks is not None:
            max_chunks = number_of_chunks
        query = """
            mutation createVectorQuery($repo:String!, $prompt:String!, $maxchunks:Int, $llmmodel:String,
            $className:String!){
            createCmAbstractPersistable(repositoryIdentifier: $repo,
            classIdentifier:$className,
            cmAbstractPersistableProperties:
            {
                properties:
                [
                {
                GenaiLLMPrompt: $prompt
                },
                {
                GenaiLLMModelName: $llmmodel
                },
                {
                GenaiPerformLLMQuery: false
                },
                {
                GenaiMaxDocumentChunks: $maxchunks
                }
                ]
            })
            {
                id
                name
                creator
                properties(includes:[
                "GenaiVectorChunks", "GenaiLLMModelName"
                
                ])
                {
                
                value
                }
            }
            }
            """

        variables = {
            "repo": graphql_client.object_store,
            "prompt": prompt,
            "llmmodel": llm_model_name if llm_model_name is not None else None,
            "maxchunks": max_chunks,
            "className": GENAI_VECTOR_QUERY_CLASS,
        }

        response: Union[ToolError, Dict[str, Any]] = (
            await graphql_client_execute_async_wrapper(
                logger, method_name, graphql_client, query=query, variables=variables
            )
        )
        if isinstance(response, ToolError):
            return response

        try:
            chunks = response["data"]["createCmAbstractPersistable"]["properties"][0][
                "value"
            ]

            if not chunks:
                return {}
            data = json.loads(chunks)

            docs_list = data.get("docs", [])  # Provide an empty list as a default
            id_list = []
            chunk_list: list[Any] = []
            if not docs_list:
                pass  # TODO
            else:
                index = 0
                for i, item in enumerate(docs_list):
                    # Use chaining .get() methods to safely access nested values

                    onedoc = item.get("doc", {})
                    doc_id = onedoc.get("metadata", {}).get("id")
                    chunk = onedoc.get("page_content")
                    score = item.get("score")
                    if doc_id and score >= RELEVANCE_SCORE:

                        guid_doc_id = convert_guid(doc_id)
                        if return_chunks is False:
                            doc_title = onedoc.get("metadata", {}).get("originaltitle")

                            my_doc = {}
                            my_doc[guid_doc_id] = doc_title
                            id_list.append(my_doc)
                            index = index + 1
                        elif return_chunks is True:
                            my_chunk = {}
                            my_chunk[chunk] = doc_id
                            chunk_list.append(my_chunk)
                            index = index + 1

            if return_chunks is False:
                return id_list
            else:
                return chunk_list
        except Exception as e:

            return ToolError(
                message=f"{method_name} failed: got err {e}",
            )

    def convert_guid(hex_string: str) -> str:
        """
        Convert a 32-character hex string to standard GUID format (8-4-4-4-12).

        Uses Python's uuid module for validation and formatting.

        :param hex_string: A 32-character hexadecimal string without hyphens
        :return: A formatted GUID string with hyphens, or the original string if invalid
        """
        try:
            # Try to create a UUID object from the hex string
            # This validates the format and handles the conversion
            uuid_obj = uuid.UUID(hex_string)
            # Return the string representation which is in 8-4-4-4-12 format
            return str(uuid_obj)
        except (ValueError, AttributeError):
            # Return the original string if it's not a valid hex string
            return hex_string
