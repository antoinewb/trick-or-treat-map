"""Command line entry point: trickortreat responses.csv -c config.toml"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from .geocode import Geocoder, Lookup, nominatim_lookup
from .render import build_map
from .responses import ColumnError, load_responses


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="trickortreat",
        description="Build a trick-or-treat map from a Google Forms CSV export.",
    )
    parser.add_argument("responses", type=Path, help="CSV downloaded from Google Forms/Sheets")
    parser.add_argument("-c", "--config", type=Path, default=Path("config.toml"))
    parser.add_argument("-o", "--out", type=Path, default=Path("output"))
    return parser.parse_args(argv)


def load_config(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"Config file not found: {path}  (copy config.example.toml to get started)")
    with open(path, "rb") as f:
        return tomllib.load(f)


def main(argv: list[str] | None = None, lookup: Lookup | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    map_cfg = config.get("map", {})
    geo_cfg = config.get("geocoding", {})

    try:
        loaded = load_responses(args.responses, config.get("columns"))
    except ColumnError as e:
        print(e, file=sys.stderr)
        return 2

    print(f"{len(loaded.houses)} houses signed up", end="")
    skipped = [
        f"{loaded.no_consent} without map consent" if loaded.no_consent else "",
        f"{loaded.duplicates} duplicate responses merged" if loaded.duplicates else "",
        f"{loaded.blank} blank addresses" if loaded.blank else "",
    ]
    skipped = [s for s in skipped if s]
    print(f" ({', '.join(skipped)})" if skipped else "")

    if lookup is None:
        contact = geo_cfg.get("contact", "").strip()
        if not contact:
            print("Set [geocoding] contact in config.toml (Nominatim requires it).", file=sys.stderr)
            return 2
        lookup = nominatim_lookup(contact)

    geocoder = Geocoder(
        lookup,
        cache_path=Path(geo_cfg.get("cache", "data/geocache.json")),
        area=geo_cfg.get("area", ""),
        overrides=config.get("overrides"),
    )
    located, failed = geocoder.locate_all(loaded.houses)

    if failed:
        print(f"\nCould not find {len(failed)} address(es); fix the spelling or add them under")
        print("[overrides] in config.toml as  \"<address>\" = [lat, lon]:")
        for house in failed:
            print(f"  - {house.address}")
    if not located:
        print("Nothing to map.", file=sys.stderr)
        return 1

    fmap = build_map(
        located,
        title=map_cfg.get("title", ""),
        show_addresses=map_cfg.get("show_addresses", True),
        dark=map_cfg.get("dark", True),
    )
    args.out.mkdir(parents=True, exist_ok=True)
    out_file = args.out / "map.html"
    fmap.save(out_file)
    print(f"\nMapped {len(located)} houses -> {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
