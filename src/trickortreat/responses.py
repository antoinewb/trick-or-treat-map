"""Load neighbor sign-ups from a Google Forms CSV export."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

# Header text Google Forms uses for each field: the question titles from
# docs/google-form.md. Override any of these in config.toml under [columns].
DEFAULT_COLUMNS = {
    "address": "Street address",
    "name": "Name to show on the map",
    "notes": "Anything trick-or-treaters should know?",
    "teal_pumpkin": "Do you offer non-food or allergy-friendly treats?",
    "full_size": "Are you handing out full-size candy bars?",
    "consent": "OK to put your house on the shared neighborhood map?",
}

# Fields that must be present in the CSV. Set consent to "" in config.toml
# to turn the consent check off.
REQUIRED_FIELDS = ("address", "consent")


@dataclass(frozen=True)
class House:
    address: str
    name: str = ""
    notes: str = ""
    teal_pumpkin: bool = False
    full_size: bool = False


@dataclass
class LoadResult:
    houses: list[House] = field(default_factory=list)
    no_consent: int = 0
    duplicates: int = 0
    blank: int = 0


class ColumnError(ValueError):
    pass


def normalize_address(address: str) -> str:
    """Lowercase, drop punctuation and collapse whitespace so typing variants match."""
    address = re.sub(r"[.,#]", " ", address.lower())
    return " ".join(address.split())


def is_yes(value: str) -> bool:
    return value.strip().lower().startswith("yes")


def load_responses(path: Path, columns: dict[str, str] | None = None) -> LoadResult:
    """Read a Google Forms CSV export into a list of houses.

    When the same address shows up more than once, the last response wins.
    Google exports rows oldest first, so a neighbor can update or withdraw
    by submitting the form again.
    """
    columns = {**DEFAULT_COLUMNS, **(columns or {})}
    result = LoadResult()

    # utf-8-sig strips the byte-order mark some spreadsheet exports add.
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        columns = _match_headers(columns, headers)
        _check_columns(columns, headers)

        def get(row: dict[str, str], key: str) -> str:
            header = columns.get(key)
            if not header or header not in row:
                return ""
            return (row[header] or "").strip()

        latest: dict[str, tuple[House, bool]] = {}
        for row in reader:
            address = get(row, "address")
            if not address:
                result.blank += 1
                continue
            key = normalize_address(address)
            if key in latest:
                result.duplicates += 1
                del latest[key]  # re-insert so the order follows the newest response
            consented = is_yes(get(row, "consent")) if columns.get("consent") else True
            house = House(
                address=address,
                name=get(row, "name"),
                notes=get(row, "notes"),
                teal_pumpkin=is_yes(get(row, "teal_pumpkin")),
                full_size=is_yes(get(row, "full_size")),
            )
            latest[key] = (house, consented)

    for house, consented in latest.values():
        if consented:
            result.houses.append(house)
        else:
            result.no_consent += 1
    return result


def _header_key(title: str) -> str:
    return " ".join(title.lower().split())


def _match_headers(columns: dict[str, str], headers: list[str]) -> dict[str, str]:
    """Point each configured title at the CSV header that matches it, ignoring case
    and spacing, so small edits to a question title ("OK" vs "Ok") still work."""
    by_key = {_header_key(h): h for h in headers}
    return {
        key: by_key.get(_header_key(title), title) if title else title
        for key, title in columns.items()
    }


def _check_columns(columns: dict[str, str], headers: list[str]) -> None:
    missing = [
        f"{key} -> {columns[key]!r}"
        for key in REQUIRED_FIELDS
        if columns.get(key) and columns[key] not in headers
    ]
    if missing:
        found = "\n  ".join(headers) or "(no header row)"
        raise ColumnError(
            "The CSV is missing required columns:\n  "
            + "\n  ".join(missing)
            + f"\nColumns found:\n  {found}\n"
            "Rename them under [columns] in config.toml to match your form."
        )
