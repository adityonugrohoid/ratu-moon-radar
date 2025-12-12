"""
Pytest configuration and shared fixtures for Moon Radar tests.
"""

import pytest


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "test_api_key_12345"


@pytest.fixture
def sample_chain_config():
    """Provide sample chain configuration."""
    return {
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48",
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "exchange": "uniswapv3",
        "name": "Ethereum Mainnet",
    }
