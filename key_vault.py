import functools
import logging
import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient


@functools.cache
def get_credential():
    return DefaultAzureCredential(exclude_interactive_browser_credential=False)


@functools.cache
def get_secret_client():
    key_vault_url = os.environ["KEY_VAULT_URL"]
    return SecretClient(vault_url=key_vault_url, credential=get_credential())


def get_secret(secret_name: str) -> str | None:
    try:
        secret_client = get_secret_client()
        secret = secret_client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        logging.error(f"Error retrieving secret '{secret_name}': {e}")
        return None


def get_blob_service_client():
    storage_account_name = os.environ["STORAGE_ACCOUNT_NAME"]
    storage_account_url = f"https://{storage_account_name}.blob.core.windows.net"
    return BlobServiceClient(
        account_url=storage_account_url, credential=get_credential()
    )
