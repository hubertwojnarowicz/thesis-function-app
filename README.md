# func-thesis

Azure Functions application for fetching flight data from an external API and storing it in Azure Data Lake Storage (ADLS).

## Overview

This project implements a serverless HTTP-triggered Azure Function that:
- Fetches flight data from an external API endpoint
- Retrieves API credentials securely from Azure Key Vault
- Stores the fetched data as JSON files in Azure Data Lake Storage Gen2
- Uses Managed Identity for secure authentication to Azure resources

## Architecture

```
HTTP Trigger → Azure Function → External API
                     ↓
              Azure Key Vault (API Key)
                     ↓
              Azure Data Lake Storage (JSON files)
```

## Prerequisites

- Python 3.11 or higher
- [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local) v4
- [uv](https://github.com/astral-sh/uv) package manager
- Azure subscription with the following resources:
  - Azure Function App
  - Azure Key Vault
  - Azure Storage Account (ADLS Gen2)





