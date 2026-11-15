from sqlmodel import Session

from ..config import get_settings
from ..db import create_db_engine, init_db
from . import seed_catalog


def main() -> None:
    settings = get_settings()
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        created, updated = seed_catalog(session)
    engine.dispose()
    print(f"Catalog: {created} produse noi, {updated} actualizate ({settings.database_file}).")


if __name__ == "__main__":
    main()
