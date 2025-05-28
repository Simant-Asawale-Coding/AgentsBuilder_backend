import os
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "description"
from langchain_community.vectorstores.azuresearch import AzureSearch

from langchain_openai import AzureOpenAIEmbeddings

import os

from typing import List, Dict

import requests

import traceback

# Constants

MARKETPLACE_INDEX = "marketplace_tools_index"

CUSTOM_INDEX = "custom_tools_index"

EMBEDDING_FIELD = "content_vector"

MARKETPLACE_INDEXER = "marketplace-tools-indexer"

CUSTOM_INDEXER = "custom-tools-indexer"

API_VERSION = "2023-11-01"


def get_vector_store(index_name: str):

    embeddings = AzureOpenAIEmbeddings(

        azure_deployment="text-embedding-3-large",

        azure_endpoint="https://agentsbuilder-llms.openai.azure.com/",

        api_key="6NFo8ePXgDTN2nQktAMM6PzQ7NOXAgKxXc7gnMHdOLCmch3fd6ITJQQJ99BEACYeBjFXJ3w3AAABACOGogI9",

        api_version="2024-02-15-preview",

        dimensions=1536,

        model="text-embedding-3-large",

    )

    vector_store = AzureSearch(

        azure_search_endpoint=f"https://{os.getenv('AZURE_SEARCH_SERVICE', 'agentsbuilder-search-service')}.search.windows.net",

        azure_search_key=os.getenv("AZURE_SEARCH_ADMIN_KEY", "HIkt0rZiKGqdmSlczYT191lQhhvJrHc1uzuhXAgWdVAzSeAO5bRa"),

        index_name=index_name,

        embedding_function=embeddings.embed_query,

        embedding_field_name="content_vector",

        content_key="description",  # Sets doc.page_content

        metadata_fields=["tool_id", "name", "status", "endpoint"]  # These will be available in doc.metadata

    )

    return vector_store


def hybrid_search_langchain(index_name: str, query: str, top: int = 10, filters: str = None) -> List[Dict]:

    try:

        vector_store = get_vector_store(index_name)

        # Note: `search_fields` is removed unless you're using a custom patch

        docs = vector_store.hybrid_search(query=query, k=top, filters=filters)

        results = []

        for doc in docs:

            results.append({

                "tool_id": doc.metadata.get("tool_id"),

                "name": doc.metadata.get("name"),

                "description": doc.page_content,

                "status": doc.metadata.get("status"),

                "endpoint": doc.metadata.get("endpoint"),

            })

        return results

    except Exception as e:

        print("\n--- Exception in hybrid_search_langchain ---")

        print(f"Exception: {e}")

        traceback.print_exc()

        print("--- End Exception ---\n")

        raise


def hybrid_search_marketplace(query: str, top: int = 10, filters: str = None) -> List[Dict]:
    return hybrid_search_langchain(MARKETPLACE_INDEX, query, top, filters)


def hybrid_search_custom(query: str, top: int = 10, filters: str = None) -> List[Dict]:
    return hybrid_search_langchain(CUSTOM_INDEX, query, top, filters)


def trigger_indexer(indexer_name: str) -> bool:

    """Triggers an Azure Cognitive Search indexer by name using the REST API."""

    service = os.getenv("AZURE_SEARCH_SERVICE", "agentsbuilder-search-service")

    key = os.getenv("AZURE_SEARCH_ADMIN_KEY", "HIkt0rZiKGqdmSlczYT191lQhhvJrHc1uzuhXAgWdVAzSeAO5bRa")

    if not service or not key:

        raise ValueError("AZURE_SEARCH_SERVICE or AZURE_SEARCH_ADMIN_KEY environment variable is missing.")

    url = f"https://{service}.search.windows.net/indexers/{indexer_name}/run?api-version={API_VERSION}"

    headers = {"api-key": key, "Content-Type": "application/json"}

    response = requests.post(url, headers=headers)

    return response.status_code == 202


def trigger_marketplace_tools_indexer() -> bool:

    return trigger_indexer(MARKETPLACE_INDEXER)


def trigger_custom_tools_indexer() -> bool:

    return trigger_indexer(CUSTOM_INDEXER)


def delete_document_by_tool_id(index_name: str, tool_id: str) -> bool:
    """
    Delete a document from the specified Azure Search index by tool_id.
    Returns True if deletion was successful, False otherwise.
    """
    try:
        vector_store = get_vector_store(index_name)
        # Use the correct key field for deletion
        res = vector_store.client.delete_documents([{"tool_id": tool_id}])
        return len(res) > 0
    except Exception as e:
        print(f"Error deleting document with tool_id={tool_id} from {index_name}: {e}")
        return False


def delete_marketplace_tool(tool_id: str) -> bool:
    return delete_document_by_tool_id(MARKETPLACE_INDEX, tool_id)


def delete_custom_tool(tool_id: str) -> bool:
    return delete_document_by_tool_id(CUSTOM_INDEX, tool_id)


if __name__ == "__main__":

    test_query = "AI tool for data analysis"

    print("Marketplace hybrid search results:")

    try:
        results = hybrid_search_marketplace("AI tool", top=10, filters="status eq 'running'")
        for r in results:
            print(r)
    except Exception as e:
        print("Error:", e)

    print("Custom tools hybrid search results:")
    try:
        results = hybrid_search_custom("data", top=5, filters="status eq 'failure'")
        for r in results:
            print(r)
    except Exception as e:
        print("Error:", e)

    # Simulate deleting a tool from both indexes
    tool_id_to_delete = "tavily-80095237fb"
    print(f"\nDeleting tool_id '{tool_id_to_delete}' from marketplace index...")
    deleted_marketplace = delete_marketplace_tool(tool_id_to_delete)
    print(f"Deleted from marketplace: {deleted_marketplace}")

    print(f"Deleting tool_id '{tool_id_to_delete}' from custom index...")
    deleted_custom = delete_custom_tool(tool_id_to_delete)
    print(f"Deleted from custom: {deleted_custom}")

    print("Triggering marketplace tools indexer...")
    try:
        success = trigger_marketplace_tools_indexer()
        print("Marketplace indexer triggered:", success)
    except Exception as e:
        print("Error triggering marketplace indexer:", e)

    print("Triggering custom tools indexer...")
    try:
        success = trigger_custom_tools_indexer()
        print("Custom tools indexer triggered:", success)
    except Exception as e:

        print("Error triggering custom tools indexer:", e) 