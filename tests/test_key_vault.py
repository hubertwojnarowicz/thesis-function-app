import os
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.keyvault.secrets import KeyVaultSecret

from key_vault import (
    get_blob_service_client,
    get_credential,
    get_secret,
    get_secret_client,
)


class TestGetCredential:
    """Test cases for get_credential function."""

    @patch("key_vault.DefaultAzureCredential")
    def test_get_credential_returns_credential(self, mock_credential):
        """Test that get_credential returns a DefaultAzureCredential instance."""
        # Clear the cache before test
        get_credential.cache_clear()

        mock_cred_instance = MagicMock()
        mock_credential.return_value = mock_cred_instance

        credential = get_credential()

        mock_credential.assert_called_once_with(
            exclude_interactive_browser_credential=False
        )
        assert credential == mock_cred_instance

    @patch("key_vault.DefaultAzureCredential")
    def test_get_credential_is_cached(self, mock_credential):
        """Test that get_credential caches the result."""
        get_credential.cache_clear()

        mock_cred_instance = MagicMock()
        mock_credential.return_value = mock_cred_instance

        credential1 = get_credential()
        credential2 = get_credential()

        # Should only be called once due to caching
        mock_credential.assert_called_once()
        assert credential1 is credential2


class TestGetSecretClient:
    """Test cases for get_secret_client function."""

    @patch.dict(os.environ, {"KEY_VAULT_URL": "https://test-vault.vault.azure.net/"})
    @patch("key_vault.SecretClient")
    @patch("key_vault.get_credential")
    def test_get_secret_client_returns_client(
        self, mock_get_credential, mock_secret_client
    ):
        """Test that get_secret_client returns a SecretClient instance."""
        get_secret_client.cache_clear()

        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        mock_client_instance = MagicMock()
        mock_secret_client.return_value = mock_client_instance

        client = get_secret_client()

        mock_secret_client.assert_called_once_with(
            vault_url="https://test-vault.vault.azure.net/", credential=mock_credential
        )
        assert client == mock_client_instance

    @patch.dict(os.environ, {}, clear=True)
    @patch("key_vault.get_credential")
    def test_get_secret_client_missing_env_var(self, mock_get_credential):
        """Test that get_secret_client raises KeyError when KEY_VAULT_URL is missing."""
        get_secret_client.cache_clear()

        with pytest.raises(KeyError):
            get_secret_client()


class TestGetSecret:
    """Test cases for get_secret function."""

    @patch("key_vault.get_secret_client")
    def test_get_secret_success(self, mock_get_secret_client):
        """Test successful secret retrieval."""
        mock_client = MagicMock()
        mock_secret = MagicMock(spec=KeyVaultSecret)
        mock_secret.value = "test-secret-value"
        mock_client.get_secret.return_value = mock_secret
        mock_get_secret_client.return_value = mock_client

        result = get_secret("test-secret")

        mock_client.get_secret.assert_called_once_with("test-secret")
        assert result == "test-secret-value"

    @patch("key_vault.get_secret_client")
    def test_get_secret_not_found(self, mock_get_secret_client):
        """Test get_secret returns None when secret is not found."""
        mock_client = MagicMock()
        mock_client.get_secret.side_effect = ResourceNotFoundError("Secret not found")
        mock_get_secret_client.return_value = mock_client

        result = get_secret("non-existent-secret")

        assert result is None

    @patch("key_vault.get_secret_client")
    def test_get_secret_general_exception(self, mock_get_secret_client):
        """Test get_secret returns None on general exceptions."""
        mock_client = MagicMock()
        mock_client.get_secret.side_effect = Exception("Generic error")
        mock_get_secret_client.return_value = mock_client

        result = get_secret("test-secret")

        assert result is None


class TestGetBlobServiceClient:
    """Test cases for get_blob_service_client function."""

    @patch.dict(os.environ, {"STORAGE_ACCOUNT_NAME": "teststorage"})
    @patch("key_vault.BlobServiceClient")
    @patch("key_vault.get_credential")
    def test_get_blob_service_client_success(
        self, mock_get_credential, mock_blob_client
    ):
        """Test successful BlobServiceClient creation."""
        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        mock_client_instance = MagicMock()
        mock_blob_client.return_value = mock_client_instance

        client = get_blob_service_client()

        mock_blob_client.assert_called_once_with(
            account_url="https://teststorage.blob.core.windows.net",
            credential=mock_credential,
        )
        assert client == mock_client_instance

    @patch.dict(os.environ, {}, clear=True)
    @patch("key_vault.get_credential")
    def test_get_blob_service_client_missing_env_var(self, mock_get_credential):
        """Test that get_blob_service_client raises KeyError when STORAGE_ACCOUNT_NAME is missing."""
        with pytest.raises(KeyError):
            get_blob_service_client()
