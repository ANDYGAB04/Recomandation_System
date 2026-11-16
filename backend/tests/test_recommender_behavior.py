from types import SimpleNamespace

import numpy as np
import pytest

from app.models import Interaction
from app.recommender import (
    PERSONALIZED,
    POPULAR,
    ContentRecommender,
    History,
    popular,
    product_preference_features,
    recommend,
    similar,
)
from app.recommender.recommend import NO_MATCH_REASON, NO_PROFILE_REASON, _popular_text, combine_profiles
from tests.test_recommender_declared import CATALOG, MARIA, RADU, Profile


@pytest.fixture(scope="module")
def rec():
    return ContentRecommender(CATALOG)


def ids(result):
    return [item.product_id for item in result.items]


# ---- Istoricul ----

def test_history_caps_views_and_follows_the_last_favorite_action():
    history = History.from_events(
        [(1, "view")] * 6 + [(2, "favorite"), (2, "unfavorite"), (3, "favorite"), (4, "purchase")]
    )
    assert history.product_weights() == {1: 3.0, 3: 5.0, 4: 10.0}
    assert history.purchased == {4}
    assert [history.strongest_event(p) for p in (4, 3, 1, 2)] == ["purchase", "favorite", "view", None]


def test_history_can_be_built_from_interaction_models():
    interactions = [Interaction(event_id=f"e{i}", user_id=1, product_id=pid, type=t)
                    for i, (pid, t) in enumerate([(1, "view"), (1, "favorite"), (2, "purchase")])]
    assert History.from_interactions(interactions).product_weights() == {1: 6.0, 2: 10.0}


# ---- Criteriile de acceptare ----

def test_a_new_favorite_changes_the_order(rec):
    runner = Profile({"running": "high"}, level="beginner")
    before = ids(recommend(rec, runner, History(), {}, k=6))
    # Pantofii Pro (3) și ceasul GPS (5) au stilul „performanță”; favoritul îi ridică pe amândoi.
    after = ids(recommend(rec, runner, History.from_events([(3, "favorite")]), {}, k=6))
    assert before != after
    assert after.index(3) < before.index(3) and after.index(5) < before.index(5)


@pytest.mark.parametrize("profile", [MARIA, RADU, Profile({"running": "low"}, max_budget=250), None])
@pytest.mark.parametrize("events", [[], [(1, "purchase"), (6, "favorite")], [(3, "view"), (9, "purchase")]])
def test_excluded_products_never_appear(rec, profile, events):
    history = History.from_events(events)
    result = recommend(rec, profile, history, {6: 3, 1: 2, 12: 9}, k=50, exclude=[2])
    budget = profile.max_budget if profile else None
    for product_id in ids(result):
        product = rec.by_id[product_id]
        assert product.available
        assert product_id not in history.purchased and product_id != 2
        assert budget is None or product.price <= budget


def test_explanations_only_mention_choices_found_in_both_profile_and_product(rec):
    choices = {("activities", a) for a in MARIA.activities} | {("styles", s) for s in MARIA.styles}
    choices |= {("levels", MARIA.level), ("seasons", MARIA.season)}
    result = recommend(rec, MARIA, History.from_events([(4, "favorite")]), {}, k=10)
    assert any(item.explanation.matched for item in result.items)
    for item in result.items:
        features = product_preference_features(rec.by_id[item.product_id])
        for match in item.explanation.matched:
            assert (match.group, match.value) in choices
            prefix = {"activities": "usage", "styles": "style", "levels": "level", "seasons": "season"}[match.group]
            assert f"{prefix}:{match.value}" in features
            assert match.label.lower() in item.explanation.text.lower()


# ---- Rezerva pe popularitate ----

def test_no_settings_and_no_history_falls_back_to_popular(rec):
    result = recommend(rec, None, History(), {6: 3, 1: 5, 12: 9}, k=3)
    assert (result.strategy, result.fallback_reason) == (POPULAR, NO_PROFILE_REASON)
    assert ids(result) == [1, 6, 2]  # 12 este indisponibil; restul, după id
    assert result.items[0].explanation.text == "Printre cele mai cumpărate: 5 clienți."


def test_empty_profile_object_also_falls_back(rec):
    assert recommend(rec, Profile(), History(), {}, k=3).strategy == POPULAR


def test_profile_matching_nothing_within_budget_falls_back_with_a_reason(rec):
    result = recommend(rec, Profile({"cycling": "high"}, max_budget=50), History(), {}, k=3)
    assert (result.strategy, result.fallback_reason) == (POPULAR, NO_MATCH_REASON)
    assert all(rec.by_id[i].price <= 50 for i in ids(result))


def test_popular_respects_budget_and_exclusions(rec):
    result = popular(rec, {6: 10, 1: 5}, k=5, exclude=[1], max_price=1000)
    assert 1 not in ids(result) and 6 not in ids(result)


@pytest.mark.parametrize("count, text", [
    (0, "Produs disponibil în catalog."),
    (1, "Printre cele mai cumpărate: 1 client."),
    (7, "Printre cele mai cumpărate: 7 clienți."),
    (20, "Printre cele mai cumpărate: 20 de clienți."),
    (101, "Printre cele mai cumpărate: 101 clienți."),
])
def test_popular_text_uses_correct_romanian_plural(count, text):
    assert _popular_text(count) == text


# ---- Profilul din comportament ----

def test_history_alone_gives_personalized_recommendations(rec):
    result = recommend(rec, None, History.from_events([(6, "purchase")]), {}, k=3)
    assert result.strategy == PERSONALIZED
    assert 6 not in ids(result)
    first = result.items[0]
    assert rec.by_id[first.product_id].category in {"camping", "hiking"}
    assert first.explanation.matched == [] and first.explanation.because_of[0] == 6
    assert "din cumpărăturile tale" in first.explanation.text


def test_favorite_product_itself_is_flagged_in_the_explanation(rec):
    result = recommend(rec, MARIA, History.from_events([(1, "favorite")]), {}, k=3)
    item = next(i for i in result.items if i.product_id == 1)
    assert item.explanation.text.startswith("Este în favoritele tale")
    assert 1 not in item.explanation.because_of


def test_alpha_selects_between_declared_and_behavior_profiles(rec):
    declared = rec.declared_profile(MARIA)
    behavior = rec.behavior_profile({6: 10.0})
    assert np.allclose(combine_profiles(declared, behavior, alpha=1.0), declared)
    assert np.allclose(combine_profiles(declared, behavior, alpha=0.0), behavior)
    assert combine_profiles(None, None) is None


def test_viewing_many_times_counts_as_much_as_three_views(rec):
    three = rec.behavior_profile(History.from_events([(4, "view")] * 3).product_weights())
    many = rec.behavior_profile(History.from_events([(4, "view")] * 30 + [(1, "view")]).product_weights())
    reference = rec.behavior_profile(History.from_events([(4, "view")] * 3 + [(1, "view")]).product_weights())
    assert np.allclose(many, reference) and not np.allclose(three, reference)


# ---- Produse similare ----

def test_similar_products_exclude_the_product_and_unavailable_ones(rec):
    items = similar(rec, 1, k=10)
    assert 1 not in [i.product_id for i in items] and 12 not in [i.product_id for i in items]
    top = items[0]
    assert rec.by_id[top.product_id].category == "running"
    assert top.explanation.text.startswith("Caracteristici comune: alergare")
    assert top.explanation.because_of == [1]


def test_works_with_plain_objects_from_the_seed_catalog():
    from app.seed.catalog import build_catalog

    products = [SimpleNamespace(id=i + 1, **data) for i, data in enumerate(build_catalog())]
    real = ContentRecommender(products)
    maria = recommend(real, MARIA, History(), {}, k=10)
    radu = recommend(real, RADU, History(), {}, k=10)
    assert maria.strategy == radu.strategy == PERSONALIZED
    assert set(ids(maria)).isdisjoint(ids(radu))
