from pathlib import Path

from trickortreat.cli import main

SAMPLE = Path(__file__).parent.parent / "sample" / "responses.csv"


def test_builds_map_end_to_end(tmp_path, capsys):
    config = tmp_path / "config.toml"
    config.write_text(
        f"""
[map]
title = "Elm <Street> 2026"
show_addresses = false

[geocoding]
area = "Springfield, IL"
cache = "{(tmp_path / 'cache.json').as_posix()}"
"""
    )
    known = {
        "130 Elm St, Springfield, IL": (39.80, -89.65),
        "123 Elm St., Springfield, IL": (39.81, -89.64),
    }
    out = tmp_path / "out"

    code = main([str(SAMPLE), "-c", str(config), "-o", str(out)], lookup=known.get)

    assert code == 0
    # index.html so hosts like Netlify serve it at the site's root URL.
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "The Smiths" in html
    assert "Haunted garage 6-9pm" in html
    assert "The Garcias" not in html  # declined consent
    assert "123 Elm St" not in html  # show_addresses = false
    assert "Elm &lt;Street&gt; 2026" in html
    # OSM's tile servers block pages opened from disk; see render.TILES_URL.
    assert "tile.openstreetmap.org" not in html
    assert "server.arcgisonline.com" in html
    assert '<meta name="robots" content="noindex, nofollow">' in html
    assert "Mapped 2 houses" in capsys.readouterr().out


def test_reports_unfound_addresses(tmp_path, capsys):
    config = tmp_path / "config.toml"
    config.write_text(f'[geocoding]\ncache = "{(tmp_path / "c.json").as_posix()}"\n')
    known = {"130 Elm St": (39.8, -89.65)}

    code = main([str(SAMPLE), "-c", str(config), "-o", str(tmp_path)], lookup=known.get)

    assert code == 0
    out = capsys.readouterr().out
    assert "Could not find 1 address" in out
    assert "123 Elm St." in out


def test_requires_contact_for_nominatim(tmp_path, capsys):
    config = tmp_path / "config.toml"
    config.write_text("[geocoding]\n")
    assert main([str(SAMPLE), "-c", str(config), "-o", str(tmp_path)]) == 2
    assert "contact" in capsys.readouterr().err
