from trickortreat.geocode import Located
from trickortreat.render import MAX_FIT_ZOOM, build_map
from trickortreat.responses import House


def render(spots) -> str:
    return build_map(spots).get_root().render()


def test_single_house_zoom_is_capped():
    html = render([Located(House("1 Elm St"), 29.66, -95.15)])
    assert f'"maxZoom": {MAX_FIT_ZOOM}' in html


def test_locate_me_button():
    html = render([Located(House("1 Elm St"), 29.66, -95.15)])
    assert "L.control.locate" in html
    assert "Show my location" in html
