# Setting up the Google Form

The tool reads the CSV that Google exports from the form's responses. It
matches columns by **question title**, so use these titles exactly, or change
them under `[columns]` in `config.toml`.

## Questions

| # | Question title | Type | Required | Notes |
|---|---|---|---|---|
| 1 | `Street address` | Short answer | Yes | Description: "House number and street, e.g. 123 Elm St" |
| 2 | `Name to show on the map` | Short answer | No | Description: "Optional, e.g. The Smiths. Leave blank to stay anonymous." |
| 3 | `Anything trick-or-treaters should know?` | Short answer | No | Hours, "haunted garage", "use side door", etc. |
| 4 | `Do you offer non-food or allergy-friendly treats?` | Multiple choice: `Yes` / `No` | No | Teal pumpkin houses get a teal marker |
| 5 | `Are you handing out full-size candy bars?` | Multiple choice: `Yes` / `No` | No | Adds a star to the marker |
| 6 | `OK to put your house on the shared neighborhood map?` | Multiple choice: `Yes, include my house` / `No, just for the organizer` | Yes | Only "Yes…" answers are mapped |

Answers count as "yes" when they start with "Yes", so you can reword options
as long as the yes option starts with that word.

## Form settings

- **Settings → Responses → Allow response editing**: on. Neighbors can fix
  typos with their edit link.
- Neighbors can also just submit again. When an address appears more than
  once, the **newest** response wins, so a later "No" removes the house.
- Leave "Collect email addresses" off unless you need it. The tool ignores it.

## Exporting the responses

1. Open the form → **Responses** tab → **Link to Sheets** (creates a sheet that updates on its own).
2. In the sheet: **File → Download → Comma-separated values (.csv)**.
3. Save it as `data/responses.csv` in this project. `data/` is git-ignored, so
   addresses never end up on GitHub.

Re-download and re-run whenever new responses come in. Addresses already
looked up are cached, so re-runs are fast.
