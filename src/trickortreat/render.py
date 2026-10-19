"""Draw the interactive Folium map."""

from __future__ import annotations

from html import escape

import folium

from .geocode import Located

ORANGE = "#ff7518"
TEAL = "#1fb5ac"

# Esri's street map loads from a map.html opened straight off disk or from an
# email attachment. OpenStreetMap's own tile servers block those requests
# (no Referer header) and show "403 Access blocked" tiles instead.
TILES_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
)
TILES_ATTR = "Tiles &copy; Esri &mdash; Sources: Esri, HERE, Garmin, OpenStreetMap contributors"

# Inverts the street map into a night-time look without needing a keyed dark
# tile service. Markers and popups aren't affected.
DARK_TILES_CSS = """
<style>.leaflet-tile-pane { filter: invert(1) hue-rotate(180deg) brightness(.85) contrast(.9); }</style>
"""

LEGEND = f"""
<div style="position: fixed; bottom: 24px; left: 12px; z-index: 1000;
            background: rgba(20, 20, 20, .85); color: #eee; padding: 8px 12px;
            border-radius: 8px; font: 14px/1.6 system-ui, sans-serif;">
  <div><span style="color:{ORANGE}">&#9679;</span> Handing out treats</div>
  <div><span style="color:{TEAL}">&#9679;</span> Allergy-friendly (teal pumpkin)</div>
  <div>&#11088; Full-size bars</div>
</div>
"""


def popup_html(spot: Located, show_address: bool) -> str:
    house = spot.house
    lines = []
    if house.name:
        lines.append(f"<b>{escape(house.name)}</b>")
    if show_address:
        lines.append(escape(house.address))
    if house.teal_pumpkin:
        lines.append(f'<span style="color:{TEAL}">Allergy-friendly treats</span>')
    if house.full_size:
        lines.append("&#11088; Full-size bars")
    if house.notes:
        lines.append(f"<i>{escape(house.notes)}</i>")
    return "<br>".join(lines) or "Treats here!"


def marker_icon(spot: Located) -> folium.DivIcon:
    color = TEAL if spot.house.teal_pumpkin else ORANGE
    star = "&#11088;" if spot.house.full_size else ""
    return folium.DivIcon(
        icon_size=(28, 28),
        icon_anchor=(14, 14),
        html=(
            f'<div style="width:22px;height:22px;border-radius:50%;background:{color};'
            'border:2px solid #111;box-shadow:0 0 6px rgba(0,0,0,.6);'
            f'font-size:11px;line-height:22px;text-align:center">{star}</div>'
        ),
    )


def build_map(
    spots: list[Located], title: str = "", show_addresses: bool = True, dark: bool = True
) -> folium.Map:
    if not spots:
        raise ValueError("No houses to put on the map.")

    fmap = folium.Map(tiles=None, control_scale=True)
    folium.TileLayer(tiles=TILES_URL, attr=TILES_ATTR, name="Streets", max_zoom=19).add_to(fmap)
    for spot in spots:
        folium.Marker(
            location=(spot.lat, spot.lon),
            icon=marker_icon(spot),
            tooltip=escape(spot.house.name) if spot.house.name else None,
            popup=folium.Popup(popup_html(spot, show_addresses), max_width=260),
        ).add_to(fmap)

    lats = [s.lat for s in spots]
    lons = [s.lon for s in spots]
    fmap.fit_bounds([(min(lats), min(lons)), (max(lats), max(lons))], padding=(30, 30))

    if title:
        fmap.get_root().html.add_child(
            folium.Element(
                '<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);'
                " z-index: 1000; background: rgba(20, 20, 20, .85); color: #ff7518;"
                ' padding: 6px 16px; border-radius: 8px; font: 600 18px system-ui, sans-serif;">'
                f"{escape(title)}</div>"
            )
        )
        fmap.get_root().header.add_child(folium.Element(f"<title>{escape(title)}</title>"))
    if dark:
        fmap.get_root().header.add_child(folium.Element(DARK_TILES_CSS))
    fmap.get_root().html.add_child(folium.Element(LEGEND))
    return fmap
