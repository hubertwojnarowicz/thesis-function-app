import logging
import os
from datetime import datetime, timezone

import azure.functions as func
import httpx

from key_vault import get_blob_service_client, get_secret

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Fetch data from FLIGHTS_ENDPOINT and save to ADLS.
    """
    logging.info("Fetching flights data...")

    try:
        endpoint_url = os.environ["API_URL"] + "/flights"
        container_name = os.environ["ADLS_FILE_SYSTEM"]
        path_prefix = os.getenv("ADLS_PATH_PREFIX", "flights")
    except KeyError as e:
        logging.error(f"Missing environment variable: {e}")
        return func.HttpResponse(f"Configuration error: Missing {e}", status_code=500)

    api_key = get_secret("api-key")
    endpoint_url = endpoint_url + f"?key={api_key}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(endpoint_url)
            response.raise_for_status()
            data = response.text
            logging.info("Data fetched successfully.")
    except httpx.HTTPError as e:
        logging.error(f"HTTP request failed: {e}")
        return func.HttpResponse("Failed to fetch data from endpoint", status_code=502)

    try:
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(container_name)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        blob_name = f"{path_prefix.rstrip('/')}/{timestamp}.json"

        # Upload blob
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(data.encode("utf-8"), overwrite=True)

        logging.info(f"Data saved to {container_name}/{blob_name}")
        return func.HttpResponse(
            f"Data saved successfully to {container_name}/{blob_name}", status_code=200
        )
    except Exception as e:
        logging.error(f"Failed to save to storage: {e}")
        return func.HttpResponse(
            f"Failed to save data to storage: {str(e)}", status_code=500
        )
