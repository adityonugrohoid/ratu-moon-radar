"""
Tests for the scanner module.
"""

import pytest

from moon_radar.scanner import MoralisClient, PairResult


def test_pair_result_dataclass():
    """Test PairResult dataclass creation."""
    result = PairResult(
        chain_id="ethereum",
        chain_name="Ethereum Mainnet",
        token0_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48",
        token1_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        pair_address="0x1234567890abcdef",
        exchange="uniswapv3",
        symbol="USDC/WETH",
    )
    assert result.chain_id == "ethereum"
    assert result.symbol == "USDC/WETH"


def test_moralis_client_stores_api_key(mock_api_key):
    """Test that MoralisClient stores the provided API key."""
    client = MoralisClient(api_key=mock_api_key)
    assert client.api_key == mock_api_key
    client.close()


def test_moralis_client_context_manager(mock_api_key):
    """Test MoralisClient context manager."""
    with MoralisClient(api_key=mock_api_key) as client:
        assert client.api_key == mock_api_key
