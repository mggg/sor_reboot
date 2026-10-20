"""National Origin and Background features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import B03001, B05002
from build_dataset.ingest.declarations.denominators import Denominator
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
)

NATIONAL_ORIGIN_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="MEXICANORIGIN",
        display_name="Mexican origin",
        description="Mexican origin. Top-level category; 58% of US Hispanics.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_MEXICAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="PUERTORICANORIGIN",
        display_name="Puerto Rican origin",
        description="Puerto Rican origin. Top-level category.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_PUERTO_RICAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="CUBANORIGIN",
        display_name="Cuban origin",
        description="Cuban origin. Top-level category.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_CUBAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="DOMINICANORIGIN",
        display_name="Dominican origin",
        description="Dominican (Dominican Republic) origin. Top-level category.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_DOMINICAN_DOMINICAN_REPUBLIC],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="CENTRALAMORIGIN",
        display_name="Central American origin",
        description="Central American origin, TOTAL across all countries. Contains the Guatemalan, "
        "Honduran and Salvadoran features below, plus Costa Rican, Nicaraguan and "
        "Panamanian, which are not modeled.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_CENTRAL_AMERICAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="GUATEMALANORIGIN",
        display_name="Guatemalan origin",
        description="Guatemalan origin. A subset of CENTRALAMORIGIN, not additional to it.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_CENTRAL_AMERICAN_GUATEMALAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HONDURANORIGIN",
        display_name="Honduran origin",
        description="Honduran origin. A subset of CENTRALAMORIGIN, not additional to it.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_CENTRAL_AMERICAN_HONDURAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="SALVADORANORIGIN",
        display_name="Salvadoran origin",
        description="Salvadoran origin. A subset of CENTRALAMORIGIN, not additional to it.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_CENTRAL_AMERICAN_SALVADORAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="SOUTHAMORIGIN",
        display_name="South American origin",
        description="South American origin, TOTAL across all countries. Contains the Colombian, "
        "Ecuadorian, Peruvian and Venezuelan features below, plus six smaller "
        "nationalities that are not modeled.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_SOUTH_AMERICAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="COLOMBIANORIGIN",
        display_name="Colombian origin",
        description="Colombian origin. A subset of SOUTHAMORIGIN, not additional to it.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_SOUTH_AMERICAN_COLOMBIAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="ECUADORIANORIGIN",
        display_name="Ecuadorian origin",
        description="Ecuadorian origin. A subset of SOUTHAMORIGIN, not additional to it.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_SOUTH_AMERICAN_ECUADORIAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="PERUVIANORIGIN",
        display_name="Peruvian origin",
        description="Peruvian origin. A subset of SOUTHAMORIGIN, not additional to it.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_SOUTH_AMERICAN_PERUVIAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="VENEZUELANORIGIN",
        display_name="Venezuelan origin",
        description="Venezuelan origin. A subset of SOUTHAMORIGIN, not additional to it.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.HISPANIC_OR_LATINO_SOUTH_AMERICAN_VENEZUELAN],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="OTHERORIGINTOTAL",
        display_name="Other Hispanic origin",
        description="Other Hispanic or Latino, TOTAL: everyone whose reported origin is not "
        "Mexican, Puerto Rican, Cuban, Dominican, Central American or South American. "
        "5.5% of US Hispanics. Contains the two features below.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.OTHER_HISPANIC_OR_LATINO],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="SPANIARDORIGIN",
        display_name="Spaniard origin",
        description="Spaniard (origin in Spain). A subset of OTHERORIGINTOTAL.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.OTHER_HISPANIC_OR_LATINO_SPANIARD],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPORIGINUNSPECIFIED",
        display_name="Hispanic origin unspecified",
        description="Reported a Hispanic or Latino identity but no specific national origin: "
        'write-ins such as "Hispanic", "Latino" or "Latin American", plus origins '
        "too small for the Census to tabulate separately. A subset of OTHERORIGINTOTAL, "
        "and 57% of it. 1.95 million people, 3.1% of US Hispanics.",
        variable_computer=FractionalShare(
            numerator_codes=[B03001.ALL_OTHER_HISPANIC_OR_LATINO],
            denominator_codes=[Denominator.HISPANIC_POPULATION_B03001],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="FBLATAMSHARE",
        display_name="Foreign born from Latin America",
        description="Of the foreign born, the share born in Latin America (naturalized plus "
        "non-citizen)",
        variable_computer=FractionalShare(
            numerator_codes=[
                B05002.FOREIGN_BORN_NATURALIZED_U_S_CITIZEN_LATIN_AMERICA,
                B05002.FOREIGN_BORN_NOT_A_U_S_CITIZEN_LATIN_AMERICA,
            ],
            denominator_codes=[Denominator.FOREIGN_BORN],
        ),
    ),
]
