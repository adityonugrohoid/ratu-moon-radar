"""
Moralis API client for DEX pair scanning.

Provides both sync and async methods for querying the Moralis API.
Optimizations:
- Connection pooling with httpx
- Retry logic with exponential backoff
- Structured result objects
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from moon_radar.config import (
    CHAIN_CONFIGS,
    MAX_RETRIES,
    MORALIS_API_KEY,
    MORALIS_BASE_URL,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
)

logger = logging.getLogger(__name__)


@dataclass
class PairResult:
    """Represents a DEX pair scan result."""

    chain_id: str
    chain_name: str
    token0_address: str
    token1_address: str
    pair_address: str
    exchange: str
    symbol: str


class MoralisClient:
    """
    Client for Moralis DEX pair API.

    Provides efficient multi-chain pair scanning with connection reuse.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Moralis client."""
        self.api_key = api_key or MORALIS_API_KEY
        if not self.api_key:
            raise ValueError("MORALIS_API_KEY is required")

        self.base_url = MORALIS_BASE_URL
        self.headers = {"X-API-Key": self.api_key}
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client with connection pooling."""
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

    def get_pair_address(
        self,
        chain_id: str,
        token0: str,
        token1: str,
        exchange: str,
    ) -> Optional[str]:
        """
        Get DEX pair address for a token pair.

        Args:
            chain_id: Chain identifier (e.g., 'eth', 'bsc')
            token0: First token address
            token1: Second token address
            exchange: DEX exchange name

        Returns:
            Pair address if found, None otherwise
        """
        # Correct Moralis API format: /:token0/:token1/pairAddress
        url = f"{self.base_url}/{token0}/{token1}/pairAddress"
        params = {
            "chain": chain_id,
            "exchange": exchange,
        }

        for attempt in range(MAX_RETRIES):
            try:
                client = self._get_client()
                response = client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("pairAddress")
                elif response.status_code == 404:
                    # Pair not found on this exchange
                    logger.debug(f"Pair not found on {chain_id}/{exchange}")
                    return None
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = RETRY_DELAY * (2**attempt)
                    logger.warning(f"Rate limited on {chain_id}, waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error for {chain_id}: {response.status_code} - {response.text}")
                    return None

            except httpx.TimeoutException:
                logger.warning(f"Timeout on {chain_id}, attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Error querying {chain_id}: {e}")
                return None

        return None

    def scan_all_chains(self) -> list[PairResult]:
        """
        Scan all configured chains for USDC/WETH pairs.

        Returns:
            List of PairResult objects for found pairs
        """
        results = []

        for chain_id, config in CHAIN_CONFIGS.items():
            logger.info(f"Scanning {config['name']} ({chain_id})")

            pair_address = self.get_pair_address(
                chain_id=chain_id,
                token0=config["usdc"],
                token1=config["weth"],
                exchange=config["exchange"],
            )

            if pair_address:
                results.append(
                    PairResult(
                        chain_id=chain_id,
                        chain_name=config["name"],
                        token0_address=config["usdc"],
                        token1_address=config["weth"],
                        pair_address=pair_address,
                        exchange=config["exchange"],
                        symbol="USDC/WETH",
                    )
                )
                logger.info(f"Found pair on {chain_id}: {pair_address}")
            else:
                logger.warning(f"No pair found on {chain_id}")

        return results
