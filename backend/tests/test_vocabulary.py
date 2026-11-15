from app.vocabulary import LABELS, VOCABULARY_KEYS


def test_every_value_has_a_romanian_label():
    for enum in VOCABULARY_KEYS.values():
        assert set(LABELS[enum]) == {member.value for member in enum}


def test_vocabulary_endpoint_lists_all_options(client):
    data = client.get("/vocabulary").json()
    assert set(data) == set(VOCABULARY_KEYS)
    assert {"value": "hiking", "label": "Drumeție"} in data["activities"]
    assert [o["value"] for o in data["seasons"]] == ["summer", "winter", "all_year"]
