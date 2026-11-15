from dataclasses import dataclass, field

import numpy as np
import pytest
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Product, UserProfile
from app.recommender import ContentRecommender, declared_profile_features


@dataclass
class P:
    id: int
    name: str
    category: str
    usages: list[str]
    levels: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    seasons: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""
    price: float = 100.0
    available: bool = True


@dataclass
class Profile:
    activities: dict[str, str] = field(default_factory=dict)
    level: str | None = None
    styles: list[str] = field(default_factory=list)
    season: str | None = None
    max_budget: float | None = None


CATALOG = [
    P(1, "Pantofi de alergare Start", "running", ["running"], ["beginner"], ["budget"], ["summer"], ["pantofi"], "Pantofi ieftini pentru primii kilometri.", 220),
    P(2, "Tricou tehnic Start", "running", ["running"], ["beginner"], ["budget", "comfort"], ["summer"], ["tricou"], "Tricou respirabil.", 60),
    P(3, "Pantofi de alergare Pro", "running", ["running"], ["advanced"], ["performance"], ["all_year"], ["pantofi"], "Pentru curse.", 790),
    P(4, "Vestă de hidratare Trail", "running", ["running", "hiking"], ["intermediate"], ["ultralight"], ["summer"], ["vestă"], "Vestă ușoară.", 330),
    P(5, "Ceas GPS", "running", ["running", "cycling", "hiking"], [], ["performance"], ["all_year"], ["ceas"], "Distanță și puls.", 1100),
    P(6, "Cort de iarnă Expediție", "camping", ["camping"], ["advanced"], ["durable"], ["winter"], ["cort"], "Rezistă la vânt și zăpadă.", 2100),
    P(7, "Sac de dormit -20°C", "camping", ["camping"], ["advanced"], ["durable"], ["winter"], ["sac de dormit"], "Pentru nopți foarte reci.", 1400),
    P(8, "Bocanci de iarnă", "hiking", ["hiking"], ["intermediate", "advanced"], ["durable"], ["winter"], ["bocanci"], "Impermeabili și izolați.", 950),
    P(9, "Rucsac Expediție 65L", "hiking", ["hiking", "camping"], ["advanced"], ["durable"], ["all_year"], ["rucsac"], "Pentru ture lungi.", 1200),
    P(10, "Cască de bicicletă Urban", "cycling", ["cycling"], ["beginner"], ["comfort"], ["all_year"], ["cască"], "Pentru oraș.", 250),
    P(11, "Lanternă frontală", "hiking", ["hiking", "camping", "running"], [], [], ["all_year"], ["lanternă"], "Pentru plecări înainte de răsărit.", 140),
    P(12, "Pantofi de alergare Start (stoc epuizat)", "running", ["running"], ["beginner"], ["budget"], ["summer"], ["pantofi"], "", 200, available=False),
]

MARIA = Profile({"running": "high"}, "beginner", ["budget"], "summer", 300)
RADU = Profile({"camping": "high", "hiking": "high"}, "advanced", ["durable"], "winter", None)


@pytest.fixture(scope="module")
def rec():
    return ContentRecommender(CATALOG)


def ids(items):
    return [item.product_id for item in items]


def test_running_beginner_budget_profile_gets_only_matching_running_products(rec):
    top = rec.recommend_declared(MARIA, k=2)
    assert ids(top) == [1, 2]
    assert all(rec.by_id[i].category == "running" and "beginner" in rec.by_id[i].levels for i in ids(top))


def test_profiles_without_common_preferences_get_disjoint_lists(rec):
    maria, radu = rec.recommend_declared(MARIA, k=4), rec.recommend_declared(RADU, k=4)
    assert set(ids(maria)).isdisjoint(ids(radu))
    assert {rec.by_id[i].category for i in ids(radu)} <= {"camping", "hiking"}


def test_budget_unavailable_and_excluded_products_are_filtered(rec):
    items = rec.recommend_declared(MARIA, k=20, exclude=[2])
    assert all(rec.by_id[i].price <= 300 and rec.by_id[i].available for i in ids(items))
    assert 2 not in ids(items) and 12 not in ids(items) and 3 not in ids(items)


def test_empty_profile_gives_no_vector_and_no_recommendations(rec):
    assert rec.declared_profile(Profile()) is None
    assert rec.recommend_declared(Profile()) == []


def test_score_is_cosine_similarity(rec):
    vector = rec.declared_profile(RADU)
    expected = cosine_similarity(vector.reshape(1, -1), rec.matrix.toarray()).ravel()
    assert np.allclose(rec.scores(vector), expected)


def test_text_block_does_not_change_the_order_for_a_declared_profile(rec):
    vector = rec.declared_profile(MARIA)
    preferences_only = rec.matrix[:, : rec.n_preference_features].toarray()
    pref_scores = cosine_similarity(vector[: rec.n_preference_features].reshape(1, -1), preferences_only).ravel()
    assert np.argsort(-rec.scores(vector), kind="stable").tolist() == np.argsort(-pref_scores, kind="stable").tolist()


def test_high_intensity_activity_outranks_low_intensity_one(rec):
    items = rec.recommend_declared(Profile({"cycling": "high", "camping": "low"}), k=3)
    assert rec.by_id[items[0].product_id].category == "cycling"


def test_neighbouring_level_matches_partially():
    weights = declared_profile_features(Profile(level="beginner"))
    assert weights["level:beginner"] > weights["level:intermediate"] > 0
    assert "level:advanced" not in weights


def test_all_year_products_match_a_summer_profile_partially():
    weights = declared_profile_features(Profile(season="summer"))
    assert weights["season:summer"] > weights["season:all_year"] > 0
    assert "season:winter" not in weights


def test_unknown_values_are_ignored_instead_of_crashing(rec):
    assert rec.declared_profile(Profile({"surfing": "high"}, level="expert", season="spring")) is None


def test_empty_catalog_is_rejected():
    with pytest.raises(ValueError):
        ContentRecommender([])


def test_sqlmodel_objects_work_directly():
    products = [
        Product(id=1, name="Cort", category="camping", usages=["camping"], styles=["durable"], seasons=["winter"], price=900),
        Product(id=2, name="Pantofi", category="running", usages=["running"], styles=["budget"], seasons=["summer"], price=200),
    ]
    rec = ContentRecommender(products)
    profile = UserProfile(user_id=1, activities={"camping": "high"}, styles=["durable"], season="winter")
    assert ids(rec.recommend_declared(profile, k=1)) == [1]
