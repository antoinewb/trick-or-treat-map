# Trick-or-Treat Map

Neighbors sign up through a Google Form. This tool turns the responses into
an interactive map you can send back to them: one `map.html` file that opens in
any browser, including on phones.

- Orange markers for houses handing out treats, teal for allergy-friendly
  (teal pumpkin), a star for full-size bars
- Popups with the family name, notes and (optionally) the address
- Only houses that said yes to being on the shared map are included

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
cp config.example.toml config.toml
```

Edit `config.toml`: set the map title, your town under `area`, and a
`contact` email (OpenStreetMap's free geocoder requires one).

Create the form by following [docs/google-form.md](docs/google-form.md).

## Building the map

1. Download the responses as CSV to `data/responses.csv` (see the form guide).
2. Run:

   ```bash
   trickortreat data/responses.csv
   ```

3. Open `output/map.html` and check that every pin is in the right place.

Example output:

```
14 houses signed up (2 without map consent, 1 duplicate responses merged)

Could not find 1 address(es); fix the spelling or add them under
[overrides] in config.toml as  "<address>" = [lat, lon]:
  - 12 Hidden Ln

Mapped 13 houses -> output/map.html
```

Addresses are looked up through OpenStreetMap at one per second and cached in
`data/geocache.json`, so only new sign-ups take time on later runs. If a pin
lands in the wrong spot, add the address under `[overrides]` with coordinates
copied from Google Maps (right-click → click the coordinates).

## Sharing

- **Send the file**: attach `map.html` to an email or group chat.
- **One link that stays current**: publish it with GitHub Pages or
  [Netlify Drop](https://app.netlify.com/drop) and send the link once.
  Re-upload as new sign-ups come in.

The map shows only what neighbors agreed to share. For a public link,
consider `show_addresses = false` in `config.toml`.

Map data © OpenStreetMap contributors.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Roadmap

1. ~~Form responses → geocoded markers on an interactive map~~
2. Walking route with numbered stops
3. Printable PNG/PDF version
4. GPX export, QR code for flyers
