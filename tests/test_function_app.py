from unittest.mock import MagicMock, patch

import azure.functions as func
import httpx
import pytest

from function_app import http_trigger


class TestHttpTrigger:
    """Test cases for http_trigger function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock HTTP request."""
        return func.HttpRequest(
            method="GET",
            url="/api/http_trigger",
            body=b"",
        )

    @patch.dict(
        "os.environ",
        {
            "API_URL": "https://api.example.com",
            "ADLS_FILE_SYSTEM": "test-container",
            "ADLS_PATH_PREFIX": "flights",
        },
    )
    @patch("function_app.get_secret")
    @patch("function_app.httpx.Client")
    @patch("function_app.get_blob_service_client")
    @patch("function_app.datetime")
    def test_http_trigger_success(
        self,
        mock_datetime,
        mock_get_blob_client,
        mock_httpx_client,
        mock_get_secret,
        mock_request,
    ):
        """Test successful execution of http_trigger."""
        # Mock secret retrieval
        mock_get_secret.return_value = "test-api-key"

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.text = '{"flights": []}'
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        # Mock datetime
        mock_now = MagicMock()
        mock_now.strftime.return_value = "20231110T120000Z"
        mock_datetime.now.return_value = mock_now

        # Mock blob storage
        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_get_blob_client.return_value = mock_blob_service

        # Execute
        response = http_trigger(mock_request)

        # Assertions
        assert response.status_code == 200
        assert "Data saved successfully" in response.get_body().decode()
        mock_get_secret.assert_called_once_with("api-key")
        mock_client_instance.get.assert_called_once_with(
            "https://api.example.com/flights?key=test-api-key"
        )
        mock_blob_client.upload_blob.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    def test_http_trigger_missing_api_url(self, mock_request):
        """Test http_trigger with missing API_URL environment variable."""
        response = http_trigger(mock_request)

        assert response.status_code == 500
        assert "Configuration error" in response.get_body().decode()

    @patch.dict(
        "os.environ",
        {"API_URL": "https://api.example.com", "ADLS_FILE_SYSTEM": "test-container"},
    )
    @patch("function_app.get_secret")
    def test_http_trigger_secret_retrieval_fails(self, mock_get_secret, mock_request):
        """Test http_trigger when secret retrieval returns None."""
        mock_get_secret.return_value = None

        response = http_trigger(mock_request)

        # Should fail when trying to concatenate None with string
        assert response.status_code in [500, 502]

    @patch.dict(
        "os.environ",
        {"API_URL": "https://api.example.com", "ADLS_FILE_SYSTEM": "test-container"},
    )
    @patch("function_app.get_secret")
    @patch("function_app.httpx.Client")
    def test_http_trigger_http_request_fails(
        self, mock_httpx_client, mock_get_secret, mock_request
    ):
        """Test http_trigger when HTTP request fails."""
        mock_get_secret.return_value = "test-api-key"

        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = httpx.HTTPError("Connection failed")
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        response = http_trigger(mock_request)

        assert response.status_code == 502
        assert "Failed to fetch data from endpoint" in response.get_body().decode()

    @patch.dict(
        "os.environ",
        {"API_URL": "https://api.example.com", "ADLS_FILE_SYSTEM": "test-container"},
    )
    @patch("function_app.get_secret")
    @patch("function_app.httpx.Client")
    @patch("function_app.get_blob_service_client")
    @patch("function_app.datetime")
    def test_http_trigger_blob_upload_fails(
        self,
        mock_datetime,
        mock_get_blob_client,
        mock_httpx_client,
        mock_get_secret,
        mock_request,
    ):
        """Test http_trigger when blob upload fails."""
        mock_get_secret.return_value = "test-api-key"

        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.text = '{"flights": []}'
        mock_response.raise_for_status = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        # Mock datetime
        mock_now = MagicMock()
        mock_now.strftime.return_value = "20231110T120000Z"
        mock_datetime.now.return_value = mock_now

        # Mock blob storage failure
        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob.side_effect = Exception("Storage error")
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_get_blob_client.return_value = mock_blob_service

        response = http_trigger(mock_request)

        assert response.status_code == 500
        assert "Failed to save data to storage" in response.get_body().decode()

    @patch.dict(
        "os.environ",
        {
            "API_URL": "https://api.example.com",
            "ADLS_FILE_SYSTEM": "test-container",
            # ADLS_PATH_PREFIX not set, should use default
        },
    )
    @patch("function_app.get_secret")
    @patch("function_app.httpx.Client")
    @patch("function_app.get_blob_service_client")
    @patch("function_app.datetime")
    def test_http_trigger_default_path_prefix(
        self,
        mock_datetime,
        mock_get_blob_client,
        mock_httpx_client,
        mock_get_secret,
        mock_request,
    ):
        """Test http_trigger uses default path prefix when env var not set."""
        mock_get_secret.return_value = "test-api-key"

        mock_response = MagicMock()
        mock_response.text = '{"flights": []}'
        mock_response.raise_for_status = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        mock_now = MagicMock()
        mock_now.strftime.return_value = "20231110T120000Z"
        mock_datetime.now.return_value = mock_now

        mock_blob_service = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_blob_service.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_get_blob_client.return_value = mock_blob_service

        response = http_trigger(mock_request)

        # Verify blob name uses default "flights" prefix
        call_args = mock_container_client.get_blob_client.call_args
        blob_name = call_args[0][0]
        assert blob_name.startswith("flights/")
        assert response.status_code == 200
