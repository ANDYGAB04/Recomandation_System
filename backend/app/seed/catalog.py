"""Catalogul demonstrativ HobbyShop: produse de test generate determinist, cu seed fix.

Fiecare tip de produs (de exemplu „Cort 2 persoane”) apare în trei linii:

- **Start**: pentru începători, buget redus, cel mai ieftin;
- **Activ**: pentru începători și intermediari, confort sau rezistență;
- **Pro**: pentru avansați, performanță / ultraușor / rezistență, cel mai scump.

Valorile din `usages`, `levels`, `styles`, `seasons` sunt cele din app/vocabulary.py, deci
produsele se compară direct cu setările de profil. Același seed dă mereu același catalog.
"""

import random
from dataclasses import dataclass

from ..vocabulary import LABELS, Activity, Level, Season, Style

CATALOG_SEED = 20261115

A, L, S, SZ = Activity, Level, Style, Season


@dataclass(frozen=True)
class ProductType:
    name: str
    category: Activity
    seasons: tuple[Season, ...]
    base_price: float
    description: str
    tags: tuple[str, ...]
    # Alte activități potrivite, pe lângă categorie.
    also: tuple[Activity, ...] = ()
    mid_styles: tuple[Style, ...] = (S.COMFORT, S.DURABLE)
    pro_styles: tuple[Style, ...] = (S.PERFORMANCE, S.ULTRALIGHT, S.DURABLE)
    # Stil fix pentru linia Activ, în locul celui ales aleator din `mid_styles`.
    activ_style: Style | None = None


@dataclass(frozen=True)
class Line:
    name: str
    levels: tuple[Level, ...]
    price_factor: float
    sentence: str


LINES = (
    Line("Start", (L.BEGINNER,), 0.6, "Variantă accesibilă, potrivită pentru primele ieșiri."),
    Line("Activ", (L.BEGINNER, L.INTERMEDIATE), 1.0, "Echilibru între preț și calitate, pentru ieșiri regulate."),
    Line("Pro", (L.ADVANCED,), 1.7, "Pentru utilizatori avansați și condiții solicitante."),
)

BRANDS = {A.HIKING: "Carpatia", A.CAMPING: "Bivuac", A.RUNNING: "Ritm", A.CYCLING: "Pedala"}

ALL_YEAR = (SZ.ALL_YEAR,)
SUMMER = (SZ.SUMMER,)
WINTER = (SZ.WINTER,)

PRODUCT_TYPES: tuple[ProductType, ...] = (
    # ---- Drumeție ----
    ProductType("Bocanci de drumeție", A.HIKING, (SZ.SUMMER, SZ.ALL_YEAR), 520, "Bocanci cu talpă aderentă și protecție la gleznă.", ("bocanci", "încălțăminte", "impermeabil")),
    ProductType("Bocanci de iarnă", A.HIKING, WINTER, 780, "Bocanci izolați, compatibili cu colțari, pentru zăpadă și gheață.", ("bocanci", "încălțăminte", "izolat"), pro_styles=(S.DURABLE,)),
    ProductType("Rucsac de zi 25L", A.HIKING, ALL_YEAR, 260, "Rucsac pentru ture de o zi, cu spate ventilat.", ("rucsac", "25 litri")),
    ProductType("Rucsac de tură 50L", A.HIKING, ALL_YEAR, 640, "Rucsac pentru ture de mai multe zile, cu centură lombară.", ("rucsac", "50 litri"), also=(A.CAMPING,)),
    ProductType("Bețe de trekking", A.HIKING, ALL_YEAR, 210, "Pereche de bețe telescopice, reglabile.", ("bețe", "telescopic")),
    ProductType("Geacă impermeabilă", A.HIKING, ALL_YEAR, 590, "Geacă cu membrană, care oprește ploaia și vântul.", ("geacă", "impermeabil", "ploaie"), also=(A.CAMPING,)),
    ProductType("Geacă de puf", A.HIKING, WINTER, 870, "Geacă izolată, caldă și compresibilă.", ("geacă", "puf", "izolat"), also=(A.CAMPING,), pro_styles=(S.ULTRALIGHT, S.DURABLE)),
    ProductType("Pantaloni de drumeție", A.HIKING, SUMMER, 280, "Pantaloni ușori, cu uscare rapidă și picioare detașabile.", ("pantaloni", "uscare rapidă")),
    ProductType("Strat de bază termic", A.HIKING, WINTER, 230, "Bluză din lână merinos, care păstrează căldura și când e umedă.", ("bluză", "merinos", "termic"), also=(A.CAMPING, A.RUNNING)),
    ProductType("Colțari de drumeție", A.HIKING, WINTER, 340, "Colțari ușori, pentru poteci înghețate.", ("colțari", "gheață"), pro_styles=(S.DURABLE,)),
    ProductType("Lanternă frontală", A.HIKING, ALL_YEAR, 150, "Lanternă frontală LED, cu acumulator.", ("lanternă", "LED"), also=(A.CAMPING, A.RUNNING)),
    # ---- Camping ----
    ProductType("Cort 2 persoane", A.CAMPING, SUMMER, 760, "Cort de vară pentru două persoane, montaj rapid.", ("cort", "2 persoane"), also=(A.HIKING,)),
    ProductType("Cort 4 anotimpuri", A.CAMPING, WINTER, 1650, "Cort de expediție, rezistent la vânt și zăpadă.", ("cort", "expediție", "4 anotimpuri"), also=(A.HIKING,), pro_styles=(S.DURABLE,)),
    ProductType("Cort de familie 4 persoane", A.CAMPING, SUMMER, 1100, "Cort spațios cu două dormitoare și vestibul.", ("cort", "4 persoane", "familie"), mid_styles=(S.COMFORT,), pro_styles=(S.COMFORT, S.DURABLE)),
    ProductType("Sac de dormit de vară", A.CAMPING, SUMMER, 330, "Sac de dormit ușor, temperatură de confort +10 °C.", ("sac de dormit", "vară"), also=(A.HIKING,)),
    ProductType("Sac de dormit de iarnă", A.CAMPING, WINTER, 990, "Sac de dormit cu puf, temperatură de confort −10 °C.", ("sac de dormit", "puf", "izolat"), also=(A.HIKING,), pro_styles=(S.DURABLE, S.ULTRALIGHT)),
    ProductType("Saltea autogonflabilă", A.CAMPING, ALL_YEAR, 310, "Saltea care se umflă singură, izolează de sol.", ("saltea", "izolare")),
    ProductType("Arzător pe gaz", A.CAMPING, ALL_YEAR, 190, "Arzător compact pentru cartușe de gaz.", ("arzător", "gătit"), also=(A.HIKING,)),
    ProductType("Set de gătit", A.CAMPING, ALL_YEAR, 170, "Set de vase din aluminiu care intră unele în altele.", ("vase", "gătit")),
    ProductType("Scaun pliabil", A.CAMPING, SUMMER, 140, "Scaun de camping pliabil, cu husă de transport.", ("scaun", "pliabil"), mid_styles=(S.COMFORT,)),
    ProductType("Filtru de apă", A.CAMPING, ALL_YEAR, 160, "Filtru portabil pentru apă din izvoare și râuri.", ("apă", "filtru"), also=(A.HIKING,)),
    ProductType("Lampă de cort", A.CAMPING, ALL_YEAR, 95, "Lampă LED cu lumină caldă, agățabilă în cort.", ("lampă", "LED")),
    # ---- Alergare ----
    ProductType("Pantofi de alergare pe șosea", A.RUNNING, (SZ.SUMMER, SZ.ALL_YEAR), 450, "Pantofi cu amortizare pentru asfalt.", ("pantofi", "încălțăminte", "amortizare"), pro_styles=(S.PERFORMANCE,)),
    ProductType("Pantofi de alergare trail", A.RUNNING, ALL_YEAR, 560, "Pantofi cu crampoane pentru poteci și teren accidentat.", ("pantofi", "încălțăminte", "trail"), also=(A.HIKING,)),
    ProductType("Tricou tehnic de alergare", A.RUNNING, SUMMER, 120, "Tricou respirabil, care elimină transpirația.", ("tricou", "respirabil")),
    ProductType("Colanți de iarnă", A.RUNNING, WINTER, 210, "Colanți termici cu interior pufos.", ("colanți", "termic")),
    ProductType("Geacă de vânt pentru alergare", A.RUNNING, ALL_YEAR, 320, "Geacă foarte ușoară, care se strânge în buzunar.", ("geacă", "vânt"), pro_styles=(S.ULTRALIGHT, S.PERFORMANCE)),
    ProductType("Vestă de hidratare", A.RUNNING, SUMMER, 290, "Vestă cu două flaconașe moi, pentru distanțe lungi.", ("vestă", "hidratare", "trail"), also=(A.HIKING,)),
    ProductType("Ceas GPS de alergare", A.RUNNING, ALL_YEAR, 890, "Ceas cu GPS, puls și planuri de antrenament.", ("ceas", "GPS", "puls"), also=(A.CYCLING, A.HIKING), pro_styles=(S.PERFORMANCE,)),
    ProductType("Șosete de alergare", A.RUNNING, ALL_YEAR, 45, "Șosete fără cusături, care previn bășicile.", ("șosete",)),
    ProductType("Centură de alergare", A.RUNNING, SUMMER, 75, "Centură elastică pentru telefon și chei.", ("centură", "telefon")),
    ProductType("Șapcă de alergare", A.RUNNING, SUMMER, 85, "Șapcă ușoară, cu protecție UV.", ("șapcă", "UV")),
    ProductType("Mănuși de alergare", A.RUNNING, WINTER, 90, "Mănuși subțiri, compatibile cu ecranul tactil.", ("mănuși", "termic")),
    # ---- Ciclism ----
    ProductType("Cască de bicicletă", A.CYCLING, ALL_YEAR, 330, "Cască ventilată, cu sistem de reglaj.", ("cască", "siguranță"), pro_styles=(S.PERFORMANCE, S.ULTRALIGHT), activ_style=S.ULTRALIGHT),
    ProductType("Mănuși de ciclism", A.CYCLING, SUMMER, 110, "Mănuși cu degete scurte și palme căptușite.", ("mănuși",)),
    ProductType("Pantaloni scurți cu bazon", A.CYCLING, SUMMER, 260, "Pantaloni scurți cu bazon pentru ture lungi.", ("pantaloni", "bazon"), activ_style=S.ULTRALIGHT),
    ProductType("Geacă de ciclism de iarnă", A.CYCLING, WINTER, 540, "Geacă izolată, protejează de vânt la coborâri.", ("geacă", "izolat", "vânt")),
    ProductType("Set de lumini LED", A.CYCLING, ALL_YEAR, 140, "Far și stop reîncărcabile prin USB.", ("lumini", "LED", "siguranță")),
    ProductType("Pompă de mână", A.CYCLING, ALL_YEAR, 90, "Pompă compactă cu manometru.", ("pompă",), activ_style=S.ULTRALIGHT),
    ProductType("Trusă de scule multifuncțională", A.CYCLING, ALL_YEAR, 120, "Trusă cu chei, șurubelnițe și extractor de lanț.", ("scule", "reparații")),
    ProductType("Bidon cu suport", A.CYCLING, SUMMER, 60, "Bidon de 750 ml și suport pentru cadru.", ("bidon", "hidratare")),
    ProductType("Ochelari de ciclism", A.CYCLING, SUMMER, 230, "Ochelari cu lentile interschimbabile și protecție UV.", ("ochelari", "UV"), also=(A.RUNNING,), activ_style=S.ULTRALIGHT),
    ProductType("Genți de bikepacking", A.CYCLING, ALL_YEAR, 480, "Set de genți pentru cadru, ghidon și șa.", ("genți", "bikepacking"), also=(A.CAMPING,)),
    ProductType("Lacăt de bicicletă", A.CYCLING, ALL_YEAR, 150, "Lacăt în formă de U, din oțel călit.", ("lacăt", "siguranță"), pro_styles=(S.DURABLE,)),
)


def _price(rng: random.Random, value: float) -> float:
    # Prețuri „de raft”: rotunjite la leu, terminate în ,99.
    return max(round(value * rng.uniform(0.9, 1.1)), 10) - 0.01


def _season_text(seasons: tuple[Season, ...]) -> str:
    return "Sezon: " + ", ".join(LABELS[Season][s].lower() for s in seasons) + "."


def build_catalog(seed: int = CATALOG_SEED) -> list[dict]:
    """Lista produselor de test, mereu aceeași pentru același seed."""
    rng = random.Random(seed)
    products: list[dict] = []
    for ptype in PRODUCT_TYPES:
        usages = [ptype.category.value, *(a.value for a in ptype.also if a != ptype.category)]
        for line in LINES:
            if line.name == "Start":
                styles = [S.BUDGET] + ([S.COMFORT] if rng.random() < 0.4 else [])
            elif line.name == "Activ":
                # Alegerea aleatoare se face oricum, ca restul catalogului (prețuri, stoc) să rămână același.
                chosen = rng.choice(ptype.mid_styles)
                styles = [ptype.activ_style or chosen]
            else:
                styles = [rng.choice(ptype.pro_styles)]
            style_text = ", ".join(LABELS[Style][s].lower() for s in styles)
            products.append({
                "name": f"{ptype.name} {BRANDS[ptype.category]} {line.name}",
                "category": ptype.category.value,
                "usages": usages,
                "levels": [lv.value for lv in line.levels],
                "styles": [s.value for s in styles],
                "seasons": [s.value for s in ptype.seasons],
                "tags": list(ptype.tags),
                "description": f"{ptype.description} {line.sentence} Stil: {style_text}. {_season_text(ptype.seasons)}",
                "price": _price(rng, ptype.base_price * line.price_factor),
                "available": rng.random() >= 0.08,
                "is_test_data": True,
            })
    return products
