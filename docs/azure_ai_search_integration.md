# Azure AI Search Integration – Comprehensive Documentation

## 1. Objective
Our goal was to implement robust hybrid (vector + keyword) search using Azure Cognitive Search and LangChain for retrieving relevant tool information. The integration needed to:
- Support hybrid and vector search using OpenAI embeddings.
- Allow filtering by status (e.g., running, in progress, down, failure).
- Return specific fields (`tool_id`, `name`, `description`, `status`, `endpoint`).
- Provide detailed error handling for debugging.

## 2. Azure Search Resource Setup

### 2.1 Index Creation
We created two indexes:
- `marketplace_tools_index`
- `custom_tools_index`

**Index Schema:**
- `tool_id` (key, string)
- `name` (string)
- `description` (string, main content field)
- `status` (string)
- `endpoint` (string)
- `content_vector` (Collection(Single), vector field for embeddings)

**Index Creation JSON:**
```json
{
  "@odata.etag": "\"0x8DD93BB44D747F4\"",
  "name": "custom_tools_index",
  "fields": [
    {
      "name": "tool_id",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "stored": true,
      "sortable": true,
      "facetable": true,
      "key": true,
      "synonymMaps": []
    },
    {
      "name": "user_id",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "stored": true,
      "sortable": true,
      "facetable": true,
      "key": false,
      "synonymMaps": []
    },
    {
      "name": "name",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "stored": true,
      "sortable": true,
      "facetable": true,
      "key": false,
      "synonymMaps": []
    },
    {
      "name": "description",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "stored": true,
      "sortable": true,
      "facetable": true,
      "key": false,
      "synonymMaps": []
    },
    {
      "name": "status",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "stored": true,
      "sortable": true,
      "facetable": true,
      "key": false,
      "synonymMaps": []
    },
    {
      "name": "endpoint",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "stored": true,
      "sortable": true,
      "facetable": true,
      "key": false,
      "synonymMaps": []
    },
    {
      "name": "content_vector",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "filterable": false,
      "retrievable": false,
      "stored": true,
      "sortable": false,
      "facetable": false,
      "key": false,
      "dimensions": 1536,
      "vectorSearchProfile": "my-vector-profile",
      "synonymMaps": []
    }
  ],
  "scoringProfiles": [],
  "suggesters": [],
  "analyzers": [],
  "normalizers": [],
  "tokenizers": [],
  "tokenFilters": [],
  "charFilters": [],
  "similarity": {
    "@odata.type": "#Microsoft.Azure.Search.BM25Similarity"
  },
  "vectorSearch": {
    "algorithms": [
      {
        "name": "my-hnsw-algorithm",
        "kind": "hnsw",
        "hnswParameters": {
          "metric": "cosine",
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500
        }
      }
    ],
    "profiles": [
      {
        "name": "my-vector-profile",
        "algorithm": "my-hnsw-algorithm"
      }
    ],
    "vectorizers": [],
    "compressions": []
  }
}
```

The `custom_tools_index` was created with the same schema.

### 2.2 Data Sources
We defined data sources for both indexes pointing to the underlying storage (e.g., Azure Blob Storage or Cosmos DB).

**Example Data Source JSON:**
```json
{
  "@odata.context": "https://agentsbuilder-search-service.search.windows.net/$metadata#datasources/$entity",
  "@odata.etag": "\"0x8DD93A0754CD9A6\"",
  "name": "marketplace-tools-ds",
  "description": null,
  "type": "azuresql",
  "subtype": null,
  "credentials": {
    "connectionString": "Data Source=tcp:agents-builder-database-server.database.windows.net,1433;Initial Catalog=AgentsBuilder;User ID=...;Password=...;Connect Timeout=30;Encrypt=True;Trust Server Certificate=False"
  },
  "container": {
    "name": "marketplace_tools",
    "query": null
  },
  "dataChangeDetectionPolicy": null,
  "dataDeletionDetectionPolicy": null,
  "encryptionKey": null,
  "identity": null
}
```

### 2.3 Skillsets
Skillsets were defined to enrich and preprocess the ingested documents, e.g., extracting text, normalizing fields, and generating embeddings.

**Example Skillset JSON:**
```json
{
  "@odata.etag": "\"0x8DD93BBEB144E6E\"",
  "name": "tools-description-embedding-skillset",
  "skills": [
    {
      "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
      "name": "aoai-embedding-skill",
      "description": "Generate embeddings from description",
      "context": "/document",
      "resourceUri": "https://agentsbuilder-llms.openai.azure.com",
      "apiKey": "<redacted>",
      "deploymentId": "text-embedding-3-large",
      "dimensions": 1536,
      "modelName": "text-embedding-3-large",
      "inputs": [
        {
          "name": "text",
          "source": "/document/description",
          "inputs": []
        }
      ],
      "outputs": [
        {
          "name": "embedding",
          "targetName": "embedding"
        }
      ]
    }
  ]
}
```

### 2.4 Indexers
Indexers were configured to connect data sources, skillsets, and indexes, orchestrating the data flow.

**Example Indexer JSON:**
```json
{
  "@odata.context": "https://agentsbuilder-search-service.search.windows.net/$metadata#indexers/$entity",
  "@odata.etag": "\"0x8DD93C3C00847C3\"",
  "name": "marketplace-tools-indexer",
  "description": null,
  "dataSourceName": "marketplace-tools-ds",
  "skillsetName": "tools-description-embedding-skillset",
  "targetIndexName": "marketplace_tools_index",
  "disabled": null,
  "schedule": {
    "interval": "PT1H",
    "startTime": "2025-05-15T13:14:34.775Z"
  },
  "parameters": {
    "batchSize": 1000,
    "maxFailedItems": 10,
    "maxFailedItemsPerBatch": 5,
    "configuration": {}
  },
  "fieldMappings": [
    {
      "sourceFieldName": "tool_id",
      "targetFieldName": "tool_id",
      "mappingFunction": null
    },
    {
      "sourceFieldName": "user_id",
      "targetFieldName": "user_id",
      "mappingFunction": null
    },
    {
      "sourceFieldName": "name",
      "targetFieldName": "name",
      "mappingFunction": null
    },
    {
      "sourceFieldName": "description",
      "targetFieldName": "description",
      "mappingFunction": null
    },
    {
      "sourceFieldName": "status",
      "targetFieldName": "status",
      "mappingFunction": null
    },
    {
      "sourceFieldName": "endpoint",
      "targetFieldName": "endpoint",
      "mappingFunction": null
    }
  ],
  "outputFieldMappings": [
    {
      "sourceFieldName": "/document/embedding",
      "targetFieldName": "content_vector",
      "mappingFunction": null
    }
  ],
  "cache": null,
  "encryptionKey": null
}
```

The `custom-tools-indexer` was similarly configured.

#### Success Responses
Upon creation, Azure returned success JSONs confirming resource creation. (Refer to Azure Portal or CLI logs for exact responses.)

## 3. Python Integration Module

### 3.1 Dependencies
- `langchain_community` (for AzureSearch vectorstore)
- `langchain_openai` (for Azure OpenAI embeddings)
- `azure-search-documents` (Azure SDK)
- `requests` (for REST API calls)

### 3.2 Environment Variables
Sensitive configuration is managed via environment variables:
- `AZURE_SEARCH_SERVICE`
- `AZURE_SEARCH_ADMIN_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `AZURESEARCH_FIELDS_CONTENT` (set to `description`)

### 3.3 Core Functions
- **Hybrid Search**: Uses LangChain's AzureSearch, retrieves documents using both vector and keyword search, supports filtering by status.
- **Indexer Triggers**: Functions to trigger indexers via Azure REST API.
- **Delete by tool_id**: Allows deletion of documents by `tool_id`.

**Example Usage:**
```python
results = hybrid_search_marketplace("AI tool", top=10, filters="status eq 'running'")
deleted = delete_marketplace_tool("tavily-80095237fb")
```

### 3.4 Error Handling
- All search and indexer functions are wrapped in try/except blocks.
- Full tracebacks are printed for easier debugging.
- Environment variable for `AZURESEARCH_FIELDS_CONTENT` is set programmatically to ensure correct field mapping.

## 4. Major Issues & Resolutions

### 4.1 Circular Import Error
- **Problem:** Editing the package file directly led to circular import errors.
- **Resolution:** Reinstalled the `langchain_community` package and avoided modifying package internals. Used environment variables and function parameters for customizations.

### 4.2 Field Name Mismatch ('content' KeyError)
- **Problem:** The code expected a field named `content`, but our index used `description`.
- **Resolution:** Set `AZURESEARCH_FIELDS_CONTENT` to `description` at the top of our module, ensuring correct mapping.

### 4.3 Deletion by Wrong Key ('id' vs 'tool_id')
- **Problem:** Delete calls failed because the default key was `id`, but our schema uses `tool_id`.
- **Resolution:** Updated the delete logic to use `tool_id` as the key in delete requests.

### 4.4 Error Handling & Debugging
- **Problem:** Initial errors were hard to debug due to lack of detail.
- **Resolution:** Added comprehensive try/except blocks with full tracebacks in all major functions.

## 5. Final Structure & Usage

- **Indexes:** `marketplace_tools_index`, `custom_tools_index`
- **Data Sources:** `marketplace-tools-datasource`, `custom-tools-datasource`
- **Skillsets:** `tools-skillset`
- **Indexers:** `marketplace-tools-indexer`, `custom-tools-indexer`
- **Python Module:** `app/services/azure_search.py`
- **Docs:** This file (`docs/azure_ai_search_integration.md`)

## 6. References
- [Azure Cognitive Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [LangChain Docs](https://python.langchain.com/docs/integrations/vectorstores/azuresearch)

---

This documentation covers the complete journey of integrating Azure AI Search with LangChain in our project, including all design decisions, resource configurations, error handling, and final implementation details. For any further details or troubleshooting, refer to the codebase and Azure Portal logs.
