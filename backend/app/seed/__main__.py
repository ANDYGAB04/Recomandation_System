import argparse

from sqlmodel import Session

from ..config import get_settings
from ..db import create_db_engine, init_db
from . import DEMO_ACCOUNTS, reset_database, seed_all
from .simulation import SIMULATED_CUSTOMERS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Încarcă datele de test: catalogul, conturile demo și clienții simulați.",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="șterge toate datele (inclusiv conturile create din aplicație) și le recreează",
    )
    parser.add_argument("--customers", type=int, default=SIMULATED_CUSTOMERS, help="numărul de clienți simulați")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_db_engine(settings.database_file)
    if args.reset:
        reset_database(engine)
    else:
        init_db(engine)
    with Session(engine) as session:
        summary = seed_all(session, args.customers)
    engine.dispose()

    print(f"Baza de date: {settings.database_file}")
    print(f"Catalog: {summary.products_created} produse noi, {summary.products_updated} actualizate.")
    print(f"Conturi demo create: {summary.demo_accounts_created}; clienți simulați creați: {summary.simulated_customers_created}.")
    print(f"Date de test pentru evaluarea cu utilizatori: {summary.test_survey_responses_created} răspunsuri la chestionar, "
          f"{summary.test_votes_created} voturi „Ți-a fost utilă?” (marcate ca date de test, separate de cele reale).")
    for account in DEMO_ACCOUNTS:
        print(f"  {account.display_name}: {account.email} / {account.password}")


if __name__ == "__main__":
    main()
