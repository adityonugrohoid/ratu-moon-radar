"""
Configuration module for Moon Radar.

Contains chain configurations, API settings, and runtime constants.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY", "")
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

# =============================================================================
# Logging Configuration
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path("logs/moon_radar.log")

# =============================================================================
# Token Addresses (per chain)
# =============================================================================
# Common token addresses across major EVM chains

TOKEN_ADDRESSES = {
    "eth": {
        "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "DAI": "0x6B175474E89094C44Da98b954EesGdCB44A8b0D",
    },
    "bsc": {
        "BNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",   # WBNB
        "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "USDT": "0x55d398326f99059fF775485246999027B3197955",
        "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        "ETH": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
        "BTCB": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
    },
    "polygon": {
        "MATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
        "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    },
    "base": {
        "ETH": "0x4200000000000000000000000000000000000006",   # WETH
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
    },
}

# =============================================================================
# Chain Configurations
# =============================================================================
# Major EVM chains supported by Moralis getPairAddress API

CHAIN_CONFIGS = {
    "eth": {
        "exchange": "uniswapv2",
        "name": "Ethereum",
        "default_pair": ("ETH", "USDT"),
    },
    "bsc": {
        "exchange": "pancakeswapv2",
        "name": "BNB Chain",
        "default_pair": ("BNB", "USDT"),
    },
    "polygon": {
        "exchange": "quickswap",
        "name": "Polygon",
        "default_pair": ("MATIC", "USDC"),
    },
    "base": {
        "exchange": "uniswapv2",
        "name": "Base",
        "default_pair": ("ETH", "USDC"),
    },
}

# =============================================================================
# Scanner Settings
# =============================================================================

REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


def get_token_address(chain: str, symbol: str) -> str:
    """Get token address for a symbol on a given chain."""
    chain_tokens = TOKEN_ADDRESSES.get(chain, {})
    return chain_tokens.get(symbol.upper(), "")


def parse_pair(pair_str: str) -> tuple[str, str]:
    """
    Parse a pair string like 'ethusdt' or 'ETH/USDT' into (token0, token1).

    Args:
        pair_str: Pair string (e.g., 'ethusdt', 'ETH/USDT', 'eth-usdt')

    Returns:
        Tuple of (token0_symbol, token1_symbol)
    """
    # Normalize: uppercase, remove separators
    pair = pair_str.upper().replace("/", "").replace("-", "").replace("_", "")

    # Common pairs mapping
    KNOWN_PAIRS = {
        "ETHUSDT": ("ETH", "USDT"),
        "BTCUSDT": ("WBTC", "USDT"),
        "WBTCUSDT": ("WBTC", "USDT"),
        "ETHUSDC": ("ETH", "USDC"),
        "BTCUSDC": ("WBTC", "USDC"),
        "WBTCUSDC": ("WBTC", "USDC"),
        "BNBUSDT": ("BNB", "USDT"),
        "BNBUSDC": ("BNB", "USDC"),
        "MATICUSDT": ("MATIC", "USDT"),
        "MATICUSDC": ("MATIC", "USDC"),
        "USDCWETH": ("USDC", "WETH"),
        "USDTWETH": ("USDT", "WETH"),
        "DAIUSDC": ("DAI", "USDC"),
    }

    if pair in KNOWN_PAIRS:
        return KNOWN_PAIRS[pair]

    # Try to split at common token boundaries
    for token in ["USDT", "USDC", "WETH", "ETH", "BNB", "MATIC", "DAI"]:
        if pair.endswith(token):
            base = pair[:-len(token)]
            if base:
                return (base, token)

    # Default: split in half (best effort)
    mid = len(pair) // 2
    return (pair[:mid], pair[mid:])
