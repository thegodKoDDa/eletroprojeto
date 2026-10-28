"""Contextual candidates; never infer the distributor serving an address."""

STATES = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
UTILITIES = [
    dict(
        id=code,
        name=name,
        states=["SP"],
        document_ids=["nbr5410", document],
        status="awaiting_technical_validation",
        municipality_mapping="unverified",
    )
    for code, name, document in [
        ("energisa_sul_sudeste", "Energisa Sul-Sudeste", "ndu001"),
        ("cpfl_paulista", "CPFL Paulista", "ged13"),
        ("cpfl_piratininga", "CPFL Piratininga", "ged13"),
        ("cpfl_santa_cruz", "CPFL Santa Cruz", "ged13"),
        ("neoenergia_elektro", "Neoenergia Elektro", "elektro"),
        ("enel_sp", "Enel São Paulo", "enel_sp"),
        ("edp_sp", "EDP São Paulo", "edp_sp"),
    ]
]
for utility in UTILITIES:
    utility.update(document_ids=[], status="contextual", municipality_mapping="unverified")
    if utility["id"] == "neoenergia_elektro":
        utility["states"] = ["SP", "MS"]
