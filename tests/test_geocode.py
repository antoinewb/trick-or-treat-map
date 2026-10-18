import json

from trickortreat.geocode import Geocoder
from trickortreat.responses import House


class FakeLookup:
    def __init__(self, known):
        self.known = known
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        return self.known.get(query)


def test_area_suffix_cache_and_failures(tmp_path):
    cache = tmp_path / "geocache.json"
    lookup = FakeLookup({"1 Elm St, Springfield, IL": (39.1, -89.1)})
    geocoder = Geocoder(lookup, cache, area="Springfield, IL")

    located, failed = geocoder.locate_all([House("1 Elm St"), House("999 Nowhere Rd")])

    assert [(s.lat, s.lon) for s in located] == [(39.1, -89.1)]
    assert [h.address for h in failed] == ["999 Nowhere Rd"]
    assert json.loads(cache.read_text()) == {"1 elm st springfield il": [39.1, -89.1]}

    # Second run: the hit comes from the cache, the failure is retried.
    lookup2 = FakeLookup({})
    Geocoder(lookup2, cache, area="Springfield, IL").locate_all(
        [House("1 Elm St."), House("999 Nowhere Rd")]
    )
    assert lookup2.queries == ["999 Nowhere Rd, Springfield, IL"]


def test_town_already_in_address(tmp_path):
    geocoder = Geocoder(FakeLookup({}), tmp_path / "c.json", area="Springfield, IL")
    assert geocoder.query_for("1 Elm St, springfield") == "1 Elm St, springfield"


def test_overrides_skip_lookup(tmp_path):
    lookup = FakeLookup({})
    geocoder = Geocoder(lookup, tmp_path / "c.json", overrides={"12 Hidden Ln": [39.5, -89.5]})
    located, failed = geocoder.locate_all([House("12 hidden ln.")])
    assert (located[0].lat, located[0].lon) == (39.5, -89.5)
    assert not failed and not lookup.queries
