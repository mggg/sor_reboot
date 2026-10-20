"""Language features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import B16005I, B16006
from build_dataset.ingest.declarations.denominators import Denominator
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
)

LANGUAGE_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="HISPENGONLY",
        display_name="Hispanic English-only at home",
        description="Hispanics who speak only English at home",
        variable_computer=FractionalShare(
            numerator_codes=[B16006.SPEAK_ONLY_ENGLISH],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16006],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPSPANVERYWELL",
        display_name="Spanish speakers, English very well",
        description='Spanish speakers who report speaking English "very well"',
        variable_computer=FractionalShare(
            numerator_codes=[B16006.SPEAK_SPANISH_SPEAK_ENGLISH_VERY_WELL],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16006],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPSPANWELL",
        display_name="Spanish speakers, English well",
        description='Spanish speakers who report speaking English "well"',
        variable_computer=FractionalShare(
            numerator_codes=[B16006.SPEAK_SPANISH_SPEAK_ENGLISH_WELL],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16006],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPSPANNOTWELL",
        display_name="Spanish speakers, English not well",
        description='Spanish speakers who report speaking English "not well"',
        variable_computer=FractionalShare(
            numerator_codes=[B16006.SPEAK_SPANISH_SPEAK_ENGLISH_NOT_WELL],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16006],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPSPANNOTATALL",
        display_name="Spanish speakers, English not at all",
        description='Spanish speakers who report speaking English "not at all"',
        variable_computer=FractionalShare(
            numerator_codes=[B16006.SPEAK_SPANISH_SPEAK_ENGLISH_NOT_AT_ALL],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16006],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPOTHERLANG",
        display_name="Hispanic other language at home",
        description="Hispanics who speak a language other than English or Spanish at home",
        variable_computer=FractionalShare(
            numerator_codes=[B16006.SPEAK_OTHER_LANGUAGE],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16006],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPNATIVEENGONLY",
        display_name="Native-born Hispanic English-only",
        description="Native-born Hispanics who speak only English at home",
        variable_computer=FractionalShare(
            numerator_codes=[B16005I.NATIVE_SPEAK_ONLY_ENGLISH],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16005I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPNATIVEOTHERVW",
        display_name="Native-born Hispanic bilingual, English very well",
        description='Native-born Hispanics who speak another language and English "very well"',
        variable_computer=FractionalShare(
            numerator_codes=[
                B16005I.NATIVE_SPEAK_ANOTHER_LANGUAGE_SPEAK_ENGLISH_VERY_WELL
            ],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16005I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPNATIVEOTHERLTVW",
        display_name="Native-born Hispanic English less than very well",
        description='Native-born Hispanics who speak another language and English less than "very '
        'well"',
        variable_computer=FractionalShare(
            numerator_codes=[
                B16005I.NATIVE_SPEAK_ANOTHER_LANGUAGE_SPEAK_ENGLISH_LESS_THAN_VERY_WELL
            ],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16005I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPFBENGONLY",
        display_name="Foreign-born Hispanic English-only",
        description="Foreign-born Hispanics who speak only English at home",
        variable_computer=FractionalShare(
            numerator_codes=[B16005I.FOREIGN_BORN_SPEAK_ONLY_ENGLISH],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16005I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPFBOTHERVW",
        display_name="Foreign-born Hispanic bilingual, English very well",
        description='Foreign-born Hispanics who speak another language and English "very well"',
        variable_computer=FractionalShare(
            numerator_codes=[
                B16005I.FOREIGN_BORN_SPEAK_ANOTHER_LANGUAGE_SPEAK_ENGLISH_VERY_WELL
            ],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16005I],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPFBOTHERLTVW",
        display_name="Foreign-born Hispanic English less than very well",
        description='Foreign-born Hispanics who speak another language and English less than "very '
        'well"',
        variable_computer=FractionalShare(
            numerator_codes=[
                B16005I.FOREIGN_BORN_SPEAK_ANOTHER_LANGUAGE_SPEAK_ENGLISH_LESS_THAN_VERY_WELL
            ],
            denominator_codes=[Denominator.HISPANIC_5_AND_OVER_B16005I],
        ),
    ),
]
