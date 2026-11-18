
from datetime import timedelta

import numpy as np
from sqlmodel import Session, select

from ..models import Interaction, Product, RecommendationFeedback, SurveyResponse, User, UserProfile
from ..recommender import ContentRecommender, History, recommend
from ..survey import OPEN_IDS, SCALE_IDS
from .simulation import is_simulated_email
from .timeline import SIMULATION_END

TEST_DATA_SEED = 20261118
TEST_PARTICIPANTS = 12
VOTES_PER_PARTICIPANT = 5

TEST_COMMENTS = [
    "[date de test] Explicațiile m-au ajutat să înțeleg de ce apare fiecare produs.",
    "[date de test] Mi-ar plăcea mai multe filtre pe pagina de recomandări.",
    "[date de test] Recomandările s-au schimbat imediat după ce am schimbat bugetul.",
    "",
]


def seed_feedback_test_data(
    session: Session, participants: int = TEST_PARTICIPANTS, seed: int = TEST_DATA_SEED
) -> tuple[int, int]:
    if session.exec(select(SurveyResponse).where(SurveyResponse.is_test_data)).first() is not None:
        return 0, 0
    rng = np.random.default_rng(seed)
    products = list(session.exec(select(Product).order_by(Product.id)))
    if not products:
        return 0, 0
    rec = ContentRecommender(products)
    customers = [u for u in session.exec(select(User).order_by(User.id)) if is_simulated_email(u.email)][:participants]

    votes = 0
    for user in customers:
        events = session.exec(
            select(Interaction).where(Interaction.user_id == user.id).order_by(Interaction.created_at, Interaction.id)
        )
        result = recommend(rec, session.get(UserProfile, user.id), History.from_interactions(events), {},
                           k=VOTES_PER_PARTICIPANT, explain=False)
        for item in result.items:
            useful = bool(rng.random() < 0.45 + 0.5 * min(item.score, 1.0))
            session.add(RecommendationFeedback(user_id=user.id, product_id=item.product_id, useful=useful,
                                               strategy=result.strategy, created_at=SIMULATION_END,
                                               updated_at=SIMULATION_END))
            votes += 1

    for number in range(len(customers)):
        answers = {qid: int(rng.choice([2, 3, 4, 4, 5, 5])) for qid in SCALE_IDS}
        answers |= {qid: str(rng.choice(TEST_COMMENTS)) for qid in OPEN_IDS}
        session.add(SurveyResponse(answers=answers, is_test_data=True,
                                   created_at=SIMULATION_END + timedelta(minutes=number)))
    session.commit()
    return len(customers), votes
