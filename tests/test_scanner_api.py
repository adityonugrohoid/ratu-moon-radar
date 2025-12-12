"""
Tests for MoralisClient API methods with mocked HTTP responses.

These tests verify API method logic without making real network requests.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from moon_radar.scanner import MoralisClient, PairResult


class TestMoralisClientGetPairAddress:
    """Tests for get_pair_address method."""

    def test_get_pair_address_success(self, mock_api_key):
        """Test get_pair_address with successful response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pairAddress": "0xABCDEF1234567890"}

        with patch.object(MoralisClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = MoralisClient(api_key=mock_api_key)
            result = client.get_pair_address(
                chain_id="eth",
                token0="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48",
                token1="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                exchange="uniswapv3",
            )

            assert result == "0xABCDEF1234567890"
            client.close()

    def test_get_pair_address_not_found(self, mock_api_key):
        """Test get_pair_address returns None on 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(MoralisClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = MoralisClient(api_key=mock_api_key)
            result = client.get_pair_address(
                chain_id="eth",
                token0="0xInvalidToken",
                token1="0xAnotherToken",
                exchange="uniswapv3",
            )

            assert result is None
            client.close()

    def test_get_pair_address_rate_limited(self, mock_api_key):
        """Test get_pair_address handles 429 rate limit."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"pairAddress": "0xABCDEF"}

        with patch.object(MoralisClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            # First call returns 429, second call returns 200
            mock_client.get.side_effect = [mock_response_429, mock_response_200]
            mock_get_client.return_value = mock_client

            with patch("moon_radar.scanner.time.sleep"):  # Skip actual sleep
                client = MoralisClient(api_key=mock_api_key)
                result = client.get_pair_address(
                    chain_id="eth",
                    token0="0xToken0",
                    token1="0xToken1",
                    exchange="uniswapv3",
                )

                assert result == "0xABCDEF"
                client.close()

    def test_get_pair_address_timeout(self, mock_api_key):
        """Test get_pair_address handles timeout exception."""
        with patch.object(MoralisClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
            mock_get_client.return_value = mock_client

            with patch("moon_radar.scanner.time.sleep"):  # Skip actual sleep
                client = MoralisClient(api_key=mock_api_key)
                result = client.get_pair_address(
                    chain_id="eth",
                    token0="0xToken0",
                    token1="0xToken1",
                    exchange="uniswapv3",
                )

                # After all retries, should return None
                assert result is None
                client.close()

    def test_get_pair_address_api_error(self, mock_api_key):
        """Test get_pair_address handles API errors (5xx)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(MoralisClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = MoralisClient(api_key=mock_api_key)
            result = client.get_pair_address(
                chain_id="eth",
                token0="0xToken0",
                token1="0xToken1",
                exchange="uniswapv3",
            )

            assert result is None
            client.close()


class TestMoralisClientScanAllChains:
    """Tests for scan_all_chains method."""

    def test_scan_all_chains_mocked(self, mock_api_key):
        """Test scan_all_chains with mocked CHAIN_CONFIGS and get_pair_address."""
        # Mock CHAIN_CONFIGS with the structure expected by scan_all_chains
        mock_chain_configs = {
            "eth": {
                "name": "Ethereum",
                "exchange": "uniswapv3",
                "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48",
                "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            },
        }

        with patch("moon_radar.scanner.CHAIN_CONFIGS", mock_chain_configs):
            with patch.object(MoralisClient, "get_pair_address") as mock_get_pair:
                mock_get_pair.return_value = "0xPairAddress123"

                client = MoralisClient(api_key=mock_api_key)
                results = client.scan_all_chains()

                assert len(results) == 1
                assert isinstance(results[0], PairResult)
                assert results[0].chain_id == "eth"
                assert results[0].chain_name == "Ethereum"
                assert results[0].pair_address == "0xPairAddress123"
                client.close()

    def test_scan_all_chains_no_pairs_found(self, mock_api_key):
        """Test scan_all_chains when no pairs are found."""
        mock_chain_configs = {
            "eth": {
                "name": "Ethereum",
                "exchange": "uniswapv3",
                "usdc": "0xUSDC",
                "weth": "0xWETH",
            },
        }

        with patch("moon_radar.scanner.CHAIN_CONFIGS", mock_chain_configs):
            with patch.object(MoralisClient, "get_pair_address") as mock_get_pair:
                mock_get_pair.return_value = None

                client = MoralisClient(api_key=mock_api_key)
                results = client.scan_all_chains()

                assert len(results) == 0
                client.close()


class TestMoralisClientInit:
    """Tests for MoralisClient initialization."""

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch("moon_radar.scanner.MORALIS_API_KEY", None):
            with pytest.raises(ValueError, match="MORALIS_API_KEY is required"):
                MoralisClient(api_key=None)

    def test_custom_api_key(self, mock_api_key):
        """Test client accepts custom API key."""
        client = MoralisClient(api_key=mock_api_key)
        assert client.api_key == mock_api_key
        assert "X-API-Key" in client.headers
        assert client.headers["X-API-Key"] == mock_api_key
        client.close()
