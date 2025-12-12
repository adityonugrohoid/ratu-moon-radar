"""
Main entry point for Moon Radar.

Moon Radar is a multi-chain DEX and token scanner that:
1. Discovers token liquidity pools across major EVM networks
2. Detects early tokens with biggest 24h price/market cap changes

Usage:
  uv run moon-radar              # Default pair scan (ETH/USDT)
  uv run moon-radar ethusdt      # Scan specific pair
  uv run moon-radar wbtcusdc     # Another pair
  uv run moon-radar moon eth     # Top gainers on Ethereum
  uv run moon-radar moon bsc     # Top gainers on BNB Chain
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from moon_radar.config import (
    CHAIN_CONFIGS,
    LOG_FILE,
    LOG_LEVEL,
    TOKEN_ADDRESSES,
    get_token_address,
    parse_pair,
)
from moon_radar.moon_scanner import MoonScanner, MoonToken
from moon_radar.scanner import MoralisClient, PairResult


def setup_logging():
    """Configure logging for the application."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def print_header(mode: str = "pairs", pair: str = None):
    """Print scan header."""
    print()
    print("=" * 70)
    if mode == "moon":
        print("  MOON RADAR - Early Token Scanner (Top Gainers)")
    else:
        print("  MOON RADAR - Multi-Chain DEX Pair Scanner")
    print("=" * 70)
    print()
    print(f"  Scan started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if mode == "moon":
        print("  Mode: Top price movers (24h change)")
    else:
        print(f"  Chains: {', '.join(CHAIN_CONFIGS.keys())}")
        print(f"  Target pair: {pair or 'ETH/USDT'}")
    print()
    print("-" * 70)


def print_scanning(chain_name: str, chain_id: str):
    """Print scanning status."""
    print(f"  Scanning {chain_name} ({chain_id})...", end=" ", flush=True)


def print_result(found: bool, pair_address: str = None):
    """Print scan result for a chain."""
    if found:
        print(f"Found: {pair_address[:20]}...")
    else:
        print("No pair found")


def print_pair_results(results: list[PairResult]):
    """Print pair scan results."""
    print("-" * 70)
    print()

    if not results:
        print("  No pairs found in this scan")
        print()
        return

    print("  SCAN RESULTS")
    print("  " + "-" * 66)
    print(f"  {'Chain':<12} {'Pair':<12} {'Exchange':<15} {'Pair Address':<30}")
    print("  " + "-" * 66)

    for r in results:
        print(f"  {r.chain_name:<12} {r.symbol:<12} {r.exchange:<15} {r.pair_address[:28]:<30}")

    print("  " + "-" * 66)
    print()
    print(f"  Total: {len(results)} pairs found across {len(set(r.chain_id for r in results))} chains")
    print()


def print_moon_results(gainers: list[MoonToken], chain: str):
    """Print moon token results."""
    print("-" * 70)
    print()

    if not gainers:
        print(f"  No top gainers found on {chain}")
        print()
        return

    print(f"  TOP GAINERS ON {chain.upper()} (24h Price Change)")
    print("  " + "-" * 66)
    print(f"  {'#':<3} {'Symbol':<8} {'Name':<20} {'Price':<12} {'24h %':<10} {'MCap':<15}")
    print("  " + "-" * 66)

    for token in gainers:
        price_str = f"${token.price_usd:.6f}" if token.price_usd < 1 else f"${token.price_usd:.2f}"
        change_str = f"+{token.price_change_24h:.1f}%" if token.price_change_24h > 0 else f"{token.price_change_24h:.1f}%"
        mcap_str = format_mcap(token.market_cap_usd)

        print(f"  {token.rank:<3} {token.symbol:<8} {token.name[:18]:<20} {price_str:<12} {change_str:<10} {mcap_str:<15}")

    print("  " + "-" * 66)
    print()
    print(f"  Found {len(gainers)} tokens with significant 24h gains")
    print()


def format_mcap(value: float) -> str:
    """Format market cap for display."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:.0f}"


def print_footer():
    """Print scan footer."""
    print("=" * 70)
    print(f"  Scan complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()


def run_pair_scan(pair_str: str = "ethusdt"):
    """Run DEX pair scanner with specified pair."""
    token0_sym, token1_sym = parse_pair(pair_str)
    pair_display = f"{token0_sym}/{token1_sym}"

    with MoralisClient() as client:
        results = []

        for chain_id, config in CHAIN_CONFIGS.items():
            # Get token addresses for this chain
            token0_addr = get_token_address(chain_id, token0_sym)
            token1_addr = get_token_address(chain_id, token1_sym)

            if not token0_addr or not token1_addr:
                # Skip chains where tokens aren't available
                continue

            print_scanning(config["name"], chain_id)

            pair_address = client.get_pair_address(
                chain_id=chain_id,
                token0=token0_addr,
                token1=token1_addr,
                exchange=config["exchange"],
            )

            if pair_address:
                results.append(
                    PairResult(
                        chain_id=chain_id,
                        chain_name=config["name"],
                        token0_address=token0_addr,
                        token1_address=token1_addr,
                        pair_address=pair_address,
                        exchange=config["exchange"],
                        symbol=pair_display,
                    )
                )
                print_result(True, pair_address)
            else:
                print_result(False)

        print_pair_results(results)


def run_moon_scan(chain: str = "eth"):
    """Run moon token scanner for top gainers."""
    print(f"  Fetching top gainers on {chain}...", flush=True)
    print()

    with MoonScanner() as scanner:
        gainers = scanner.get_top_gainers(chain=chain, limit=10)
        print_moon_results(gainers, chain)


def print_help():
    """Print usage help."""
    print("""
Moon Radar - Multi-Chain DEX & Token Scanner

Usage:
  moon-radar [pair]          Scan for a trading pair (default: ethusdt)
  moon-radar moon [chain]    Find top gaining tokens on a chain

Examples:
  moon-radar                 Scan ETH/USDT pairs across all chains
  moon-radar ethusdt         Same as above
  moon-radar wbtcusdc        Scan WBTC/USDC pairs
  moon-radar bnbusdt         Scan BNB/USDT pairs
  moon-radar moon eth        Top gainers on Ethereum
  moon-radar moon bsc        Top gainers on BNB Chain

Supported pairs: ETH, WETH, USDT, USDC, WBTC, BNB, MATIC, DAI
Supported chains: eth, bsc, polygon, base
""")


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parse command line args
    mode = "pairs"
    pair = "ethusdt"
    chain = "eth"

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ["help", "-h", "--help"]:
            print_help()
            return

        if arg == "moon":
            mode = "moon"
            if len(sys.argv) > 2:
                chain = sys.argv[2].lower()
        else:
            # Treat as pair
            pair = arg

    logger.info(f"Starting Moon Radar scan (mode={mode}, pair={pair})")

    try:
        if mode == "moon":
            print_header(mode)
            run_moon_scan(chain)
        else:
            token0, token1 = parse_pair(pair)
            print_header(mode, f"{token0}/{token1}")
            run_pair_scan(pair)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n  Error: {e}")
        print("  Please set MORALIS_API_KEY in your .env file")
        print()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        print(f"\n  Error: {e}")
        print()
        sys.exit(1)

    print_footer()
    logger.info("Moon Radar scan complete")


if __name__ == "__main__":
    main()
