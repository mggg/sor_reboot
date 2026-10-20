"""PL features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import PL_P1
from build_dataset.ingest.declarations.feature_utils import ModelVariable, SumFeature

# Count columns referenced beyond their own declarations (DENSITY's
# numerator, the PL count and target derivations), spelled exactly once.
TOTALPOP = "TOTALPOP"
WHITEALONE = "WHITEALONE"
SORALONE = "SORALONE"
WHITESOR = "WHITESOR"

PL_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="PL",
        var_name=TOTALPOP,
        display_name="Total population",
        description="Total population",
        variable_computer=SumFeature(codes=[PL_P1.TOTAL]),
    ),
    ModelVariable(
        source="PL",
        var_name=WHITEALONE,
        display_name="White alone",
        description="White alone",
        variable_computer=SumFeature(codes=[PL_P1.WHITE_ALONE]),
    ),
    ModelVariable(
        source="PL",
        var_name="BLACKALONE",
        display_name="Black alone",
        description="Black or African American alone",
        variable_computer=SumFeature(codes=[PL_P1.BLACK_OR_AFRICAN_AMERICAN_ALONE]),
    ),
    ModelVariable(
        source="PL",
        var_name=SORALONE,
        display_name="SOR alone",
        description="Some Other Race alone",
        variable_computer=SumFeature(codes=[PL_P1.SOME_OTHER_RACE_ALONE]),
    ),
    # --- Two races ---
    ModelVariable(
        source="PL",
        var_name="WHITEBLACK",
        display_name="White and Black",
        description="White; Black or African American",
        variable_computer=SumFeature(codes=[PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN]),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIAN",
        display_name="White and AIAN",
        description="White; American Indian and Alaska Native",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEASIAN",
        display_name="White and Asian",
        description="White; Asian",
        variable_computer=SumFeature(codes=[PL_P1.WHITE_ASIAN]),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITENHPI",
        display_name="White and NHPI",
        description="White; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name=WHITESOR,
        display_name="White and SOR",
        description="White; Some Other Race",
        variable_computer=SumFeature(codes=[PL_P1.WHITE_SOME_OTHER_RACE]),
    ),
    # --- Three races ---
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIAN",
        display_name="White, Black, and AIAN",
        description="White; Black or African American; American Indian and Alaska Native",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKASIAN",
        display_name="White, Black, and Asian",
        description="White; Black or African American; Asian",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKNHPI",
        display_name="White, Black, and NHPI",
        description="White; Black or African American; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKSOR",
        display_name="White, Black, and SOR",
        description="White; Black or African American; Some Other Race",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_SOME_OTHER_RACE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIANASIAN",
        display_name="White, AIAN, and Asian",
        description="White; American Indian and Alaska Native; Asian",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIANNHPI",
        display_name="White, AIAN, and NHPI",
        description="White; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIANSOR",
        display_name="White, AIAN, and SOR",
        description="White; American Indian and Alaska Native; Some Other Race",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_SOME_OTHER_RACE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEASIANNHPI",
        display_name="White, Asian, and NHPI",
        description="White; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEASIANSOR",
        display_name="White, Asian, and SOR",
        description="White; Asian; Some Other Race",
        variable_computer=SumFeature(codes=[PL_P1.WHITE_ASIAN_SOME_OTHER_RACE]),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITENHPISOR",
        display_name="White, NHPI, and SOR",
        description="White; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    # --- Four races ---
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIANASIAN",
        display_name="White, Black, AIAN, and Asian",
        description="White; Black or African American; American Indian and Alaska Native; Asian",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIANNHPI",
        display_name="White, Black, AIAN, and NHPI",
        description="White; Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIANSOR",
        display_name="White, Black, AIAN, and SOR",
        description="White; Black or African American; American Indian and Alaska Native; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKASIANNHPI",
        display_name="White, Black, Asian, and NHPI",
        description="White; Black or African American; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKASIANSOR",
        display_name="White, Black, Asian, and SOR",
        description="White; Black or African American; Asian; Some Other Race",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN_SOME_OTHER_RACE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKNHPISOR",
        display_name="White, Black, NHPI, and SOR",
        description="White; Black or African American; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIANASIANNHPI",
        display_name="White, AIAN, Asian, and NHPI",
        description="White; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIANASIANSOR",
        display_name="White, AIAN, Asian, and SOR",
        description="White; American Indian and Alaska Native; Asian; Some Other Race",
        variable_computer=SumFeature(
            codes=[PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_SOME_OTHER_RACE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIANNHPISOR",
        display_name="White, AIAN, NHPI, and SOR",
        description="White; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEASIANNHPISOR",
        display_name="White, Asian, NHPI, and SOR",
        description="White; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    # --- Five races ---
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIANASIANNHPI",
        display_name="White, Black, AIAN, Asian, and NHPI",
        description="White; Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIANASIANSOR",
        display_name="White, Black, AIAN, Asian, and SOR",
        description="White; Black or African American; American Indian and Alaska Native; Asian; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIANNHPISOR",
        display_name="White, Black, AIAN, NHPI, and SOR",
        description="White; Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKASIANNHPISOR",
        display_name="White, Black, Asian, NHPI, and SOR",
        description="White; Black or African American; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="WHITEAIANASIANNHPISOR",
        display_name="White, AIAN, Asian, NHPI, and SOR",
        description="White; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    # --- Six races ---
    ModelVariable(
        source="PL",
        var_name="WHITEBLACKAIANASIANNHPISOR",
        display_name="White, Black, AIAN, Asian, NHPI, and SOR",
        description="White; Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P1.WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
]
