# -*- coding: utf-8 -*-
"""Script de téléchargement d'une série de prix de consommation en euros/kWh."""

import argparse
import sys
from pathlib import Path

root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from conso_api_tools.price_data import DEFAULT_PRICE_OUTPUT_PATH, download_price_history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Télécharger une série de prix de consommation en euros/kWh")
    parser.add_argument("--output", default=str(DEFAULT_PRICE_OUTPUT_PATH), help="Chemin du fichier CSV de sortie")
    parser.add_argument("--source-url", default=None, help="URL CSV/JSON contenant les prix à télécharger")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = download_price_history(output_path=args.output, source_url=args.source_url)
    print(f"📈 {len(data)} points de prix téléchargés vers {args.output}")


if __name__ == "__main__":
    main()
