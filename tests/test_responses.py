from pathlib import Path

import pytest

from trickortreat.responses import ColumnError, load_responses, normalize_address

SAMPLE = Path(__file__).parent.parent / "sample" / "responses.csv"


def write_csv(tmp_path: Path, text: str, encoding: str = "utf-8") -> Path:
    path = tmp_path / "responses.csv"
    path.write_text(text, encoding=encoding)
    return path


def test_sample_export():
    result = load_responses(SAMPLE)

    assert [h.address for h in result.houses] == ["130 Elm St", "123 Elm St."]
    assert result.no_consent == 1
    assert result.duplicates == 1

    no_name, smiths = result.houses
    assert no_name.teal_pumpkin and no_name.full_size
    assert smiths.notes == "Haunted garage 6-9pm (extended!)"  # latest response wins


def test_later_no_withdraws_consent(tmp_path):
    path = write_csv(
        tmp_path,
        "Street address,OK to put your house on the shared neighborhood map?\n"
        "1 Oak Ave,Yes\n"
        "1 oak ave,No\n",
    )
    result = load_responses(path)
    assert result.houses == []
    assert result.no_consent == 1


def test_blank_addresses_and_bom(tmp_path):
    path = write_csv(
        tmp_path,
        "Street address,OK to put your house on the shared neighborhood map?\n"
        ",Yes\n"
        "2 Oak Ave,Yes\n",
        encoding="utf-8-sig",
    )
    result = load_responses(path)
    assert [h.address for h in result.houses] == ["2 Oak Ave"]
    assert result.blank == 1


def test_custom_columns_and_consent_off(tmp_path):
    path = write_csv(tmp_path, "Where do you live?,Family\n3 Oak Ave,Lees\n")
    result = load_responses(path, {"address": "Where do you live?", "name": "Family", "consent": ""})
    assert result.houses[0].name == "Lees"


def test_column_titles_ignore_case_and_spacing(tmp_path):
    path = write_csv(
        tmp_path,
        "Street Address , ok to put your house on the shared  neighborhood map?\n"
        "5 Oak Ave,Yes\n",
    )
    result = load_responses(path)
    assert [h.address for h in result.houses] == ["5 Oak Ave"]


def test_missing_required_column_lists_headers(tmp_path):
    path = write_csv(tmp_path, "Address,Consent\n4 Oak Ave,Yes\n")
    with pytest.raises(ColumnError) as err:
        load_responses(path)
    assert "Street address" in str(err.value)
    assert "Address" in str(err.value)


def test_normalize_address():
    assert normalize_address("  123  Elm St., Apt #2 ") == "123 elm st apt 2"
