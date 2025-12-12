"""
Tests for the config module.
"""

from moon_radar import config


def test_chain_configs_exist():
    """Test that chain configurations are defined."""
    assert hasattr(config, "CHAIN_CONFIGS")
    assert len(config.CHAIN_CONFIGS) > 0


def test_chain_config_structure():
    """Test that chain configs have required fields."""
    for chain_id, chain_config in config.CHAIN_CONFIGS.items():
        assert "exchange" in chain_config
        assert "name" in chain_config
        assert "default_pair" in chain_config


def test_token_addresses_exist():
    """Test that token addresses are defined."""
    assert hasattr(config, "TOKEN_ADDRESSES")
    assert len(config.TOKEN_ADDRESSES) > 0


def test_moralis_base_url():
    """Test that Moralis base URL is defined."""
    assert hasattr(config, "MORALIS_BASE_URL")
    assert config.MORALIS_BASE_URL.startswith("https://")


def test_request_timeout_positive():
    """Test that request timeout is a positive number."""
    assert config.REQUEST_TIMEOUT > 0


def test_parse_pair():
    """Test pair parsing function."""
    assert config.parse_pair("ethusdt") == ("ETH", "USDT")
    assert config.parse_pair("WBTCUSDC") == ("WBTC", "USDC")
    assert config.parse_pair("bnb/usdt") == ("BNB", "USDT")


def test_get_token_address():
    """Test token address lookup."""
    eth_usdt = config.get_token_address("eth", "USDT")
    assert eth_usdt.startswith("0x")
    assert len(eth_usdt) == 42
