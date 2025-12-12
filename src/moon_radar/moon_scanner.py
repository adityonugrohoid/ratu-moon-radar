"""
Moon scanner module for detecting early tokens with significant price/market cap changes.

Uses Moralis Market Data API to find:
- Top price movers (biggest 24h gains)
- New tokens by exchange
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

from moon_radar.config import (
    MAX_RETRIES,
    MORALIS_API_KEY,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
)

logger = logging.getLogger(__name__)


@dataclass
class MoonToken:
    """Represents a potential moon token."""

    rank: int
    name: str
    symbol: str
    address: str
    price_usd: float
    price_change_24h: float
    market_cap_usd: float
    chain: str


class MoonScanner:
    """
    Scanner for detecting early tokens with big market cap/price changes.

    Uses Moralis Market Data API endpoints.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Moon scanner."""
        self.api_key = api_key or MORALIS_API_KEY
        if not self.api_key:
            raise ValueError("MORALIS_API_KEY is required")

        self.base_url = "https://deep-index.moralis.io/api/v2.2"
        self.headers = {"X-API-Key": self.api_key}
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                headers=self.headers,
                timeout=REQUEST_TIMEOUT,
            )
        return self._client

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_top_gainers(self, chain: str = "eth", limit: int = 10) -> list[MoonToken]:
        """
        Get top gaining tokens by 24h price change.

        Args:
            chain: Chain to scan (eth, bsc, polygon, base)
            limit: Number of tokens to return

        Returns:
            List of MoonToken objects sorted by price change
        """
        # Use the market-data/erc20s/top-movers endpoint
        url = f"{self.base_url}/market-data/erc20s/top-movers"
        params = {"chain": chain}

        try:
            client = self._get_client()
            response = client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                gainers = data.get("gainers", [])

                results = []
                for i, token in enumerate(gainers[:limit]):
                    try:
                        results.append(
                            MoonToken(
                                rank=i + 1,
                                name=token.get("token_name", "Unknown"),
                                symbol=token.get("token_symbol", "???"),
                                address=token.get("token_address", ""),
                                price_usd=float(token.get("price_usd", 0)),
                                price_change_24h=float(token.get("price_24h_percent_change", 0)),
                                market_cap_usd=float(token.get("market_cap_usd", 0)),
                                chain=chain,
                            )
                        )
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Error parsing token: {e}")
                        continue

                return results
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return []

    def get_top_losers(self, chain: str = "eth", limit: int = 10) -> list[MoonToken]:
        """
        Get top losing tokens by 24h price change (for potential rebounds).

        Args:
            chain: Chain to scan (eth, bsc, polygon, base)
            limit: Number of tokens to return

        Returns:
            List of MoonToken objects sorted by price change (descending)
        """
        url = f"{self.base_url}/market-data/erc20s/top-movers"
        params = {"chain": chain}

        try:
            client = self._get_client()
            response = client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                losers = data.get("losers", [])

                results = []
                for i, token in enumerate(losers[:limit]):
                    try:
                        results.append(
                            MoonToken(
                                rank=i + 1,
                                name=token.get("token_name", "Unknown"),
                                symbol=token.get("token_symbol", "???"),
                                address=token.get("token_address", ""),
                                price_usd=float(token.get("price_usd", 0)),
                                price_change_24h=float(token.get("price_24h_percent_change", 0)),
                                market_cap_usd=float(token.get("market_cap_usd", 0)),
                                chain=chain,
                            )
                        )
                    except (ValueError, TypeError):
                        continue

                return results
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error fetching top losers: {e}")
            return []
