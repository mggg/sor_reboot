"""Hispanic population features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import PL_P2
from build_dataset.ingest.declarations.feature_utils import ModelVariable, SumFeature

# Count columns the PL derive step reads (Hispanic-of-race subtractions),
HISPANIC = "HISPANIC"
NONHISPANICWHITEALONE = "NONHISPANICWHITEALONE"
NONHISPANICSORALONE = "NONHISPANICSORALONE"
NONHISPANICWHITESOR = "NONHISPANICWHITESOR"

PL_HISP_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="PL",
        var_name=HISPANIC,
        display_name="Hispanic or Latino",
        description="Hispanic or Latino",
        variable_computer=SumFeature(codes=[PL_P2.HISPANIC_OR_LATINO]),
    ),
    ModelVariable(
        source="PL",
        var_name=NONHISPANICWHITEALONE,
        display_name="Non-Hispanic White alone",
        description="Not Hispanic or Latino: White alone",
        variable_computer=SumFeature(codes=[PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_ALONE]),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICBLACKALONE",
        display_name="Non-Hispanic Black alone",
        description="Not Hispanic or Latino: Black or African American alone",
        variable_computer=SumFeature(
            codes=[PL_P2.NOT_HISPANIC_OR_LATINO_BLACK_OR_AFRICAN_AMERICAN_ALONE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name=NONHISPANICSORALONE,
        display_name="Non-Hispanic SOR alone",
        description="Not Hispanic or Latino: Some Other Race alone",
        variable_computer=SumFeature(
            codes=[PL_P2.NOT_HISPANIC_OR_LATINO_SOME_OTHER_RACE_ALONE]
        ),
    ),
    # --- Two races ---
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACK",
        display_name="Non-Hispanic White and Black",
        description="Not Hispanic or Latino: White; Black or African American",
        variable_computer=SumFeature(
            codes=[PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIAN",
        display_name="Non-Hispanic White and AIAN",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native",
        variable_computer=SumFeature(
            codes=[PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEASIAN",
        display_name="Non-Hispanic White and Asian",
        description="Not Hispanic or Latino: White; Asian",
        variable_computer=SumFeature(codes=[PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_ASIAN]),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITENHPI",
        display_name="Non-Hispanic White and NHPI",
        description="Not Hispanic or Latino: White; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name=NONHISPANICWHITESOR,
        display_name="Non-Hispanic White and SOR",
        description="Not Hispanic or Latino: White; Some Other Race",
        variable_computer=SumFeature(
            codes=[PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_SOME_OTHER_RACE]
        ),
    ),
    # --- Three races ---
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIAN",
        display_name="Non-Hispanic White, Black, and AIAN",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKASIAN",
        display_name="Non-Hispanic White, Black, and Asian",
        description="Not Hispanic or Latino: White; Black or African American; Asian",
        variable_computer=SumFeature(
            codes=[PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKNHPI",
        display_name="Non-Hispanic White, Black, and NHPI",
        description="Not Hispanic or Latino: White; Black or African American; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKSOR",
        display_name="Non-Hispanic White, Black, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIANASIAN",
        display_name="Non-Hispanic White, AIAN, and Asian",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native; Asian",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIANNHPI",
        display_name="Non-Hispanic White, AIAN, and NHPI",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIANSOR",
        display_name="Non-Hispanic White, AIAN, and SOR",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEASIANNHPI",
        display_name="Non-Hispanic White, Asian, and NHPI",
        description="Not Hispanic or Latino: White; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEASIANSOR",
        display_name="Non-Hispanic White, Asian, and SOR",
        description="Not Hispanic or Latino: White; Asian; Some Other Race",
        variable_computer=SumFeature(
            codes=[PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_ASIAN_SOME_OTHER_RACE]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITENHPISOR",
        display_name="Non-Hispanic White, NHPI, and SOR",
        description="Not Hispanic or Latino: White; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    # --- Four races ---
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIANASIAN",
        display_name="Non-Hispanic White, Black, AIAN, and Asian",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native; Asian",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIANNHPI",
        display_name="Non-Hispanic White, Black, AIAN, and NHPI",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIANSOR",
        display_name="Non-Hispanic White, Black, AIAN, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKASIANNHPI",
        display_name="Non-Hispanic White, Black, Asian, and NHPI",
        description="Not Hispanic or Latino: White; Black or African American; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKASIANSOR",
        display_name="Non-Hispanic White, Black, Asian, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; Asian; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKNHPISOR",
        display_name="Non-Hispanic White, Black, NHPI, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIANASIANNHPI",
        display_name="Non-Hispanic White, AIAN, Asian, and NHPI",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIANASIANSOR",
        display_name="Non-Hispanic White, AIAN, Asian, and SOR",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native; Asian; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIANNHPISOR",
        display_name="Non-Hispanic White, AIAN, NHPI, and SOR",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEASIANNHPISOR",
        display_name="Non-Hispanic White, Asian, NHPI, and SOR",
        description="Not Hispanic or Latino: White; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    # --- Five races ---
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIANASIANNHPI",
        display_name="Non-Hispanic White, Black, AIAN, Asian, and NHPI",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIANASIANSOR",
        display_name="Non-Hispanic White, Black, AIAN, Asian, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native; Asian; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIANNHPISOR",
        display_name="Non-Hispanic White, Black, AIAN, NHPI, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKASIANNHPISOR",
        display_name="Non-Hispanic White, Black, Asian, NHPI, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEAIANASIANNHPISOR",
        display_name="Non-Hispanic White, AIAN, Asian, NHPI, and SOR",
        description="Not Hispanic or Latino: White; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
    # --- Six races ---
    ModelVariable(
        source="PL",
        var_name="NONHISPANICWHITEBLACKAIANASIANNHPISOR",
        display_name="Non-Hispanic White, Black, AIAN, Asian, NHPI, and SOR",
        description="Not Hispanic or Latino: White; Black or African American; American Indian and Alaska Native; Asian; Native Hawaiian and Other Pacific Islander; Some Other Race",
        variable_computer=SumFeature(
            codes=[
                PL_P2.NOT_HISPANIC_OR_LATINO_WHITE_BLACK_OR_AFRICAN_AMERICAN_AMERICAN_INDIAN_AND_ALASKA_NATIVE_ASIAN_NATIVE_HAWAIIAN_AND_OTHER_PACIFIC_ISLANDER_SOME_OTHER_RACE
            ]
        ),
    ),
]
