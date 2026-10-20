"""Employment and Industry features for ingestion from the Census Bureau's API."""

from build_dataset.ingest.declarations.census_codes import C23002I, C24010I, C24030
from build_dataset.ingest.declarations.denominators import (
    HISPANIC_LABOR_FORCE,
    Denominator,
)
from build_dataset.ingest.declarations.feature_utils import (
    FractionalShare,
    ModelVariable,
)

EMPLOYMENT_FEATURES: list[ModelVariable] = [
    ModelVariable(
        source="ACS",
        var_name="HISPOCCMGMT",
        display_name="Hispanic management occupations",
        description="Management, business, science, and arts occupations",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24010I.MALE_MANAGEMENT_BUSINESS_SCIENCE_AND_ARTS_OCCUPATIONS,
                C24010I.FEMALE_MANAGEMENT_BUSINESS_SCIENCE_AND_ARTS_OCCUPATIONS,
            ],
            denominator_codes=[Denominator.HISPANIC_CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPOCCSERVICE",
        display_name="Hispanic service occupations",
        description="Service occupations",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24010I.MALE_SERVICE_OCCUPATIONS,
                C24010I.FEMALE_SERVICE_OCCUPATIONS,
            ],
            denominator_codes=[Denominator.HISPANIC_CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPOCCSALESOFFICE",
        display_name="Hispanic sales and office occupations",
        description="Sales and office occupations",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24010I.MALE_SALES_AND_OFFICE_OCCUPATIONS,
                C24010I.FEMALE_SALES_AND_OFFICE_OCCUPATIONS,
            ],
            denominator_codes=[Denominator.HISPANIC_CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPOCCNATRESCONST",
        display_name="Hispanic natural resources and construction occupations",
        description="Natural resources, construction, and maintenance occupations",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24010I.MALE_NATURAL_RESOURCES_CONSTRUCTION_AND_MAINTENANCE_OCCUPATIONS,
                C24010I.FEMALE_NATURAL_RESOURCES_CONSTRUCTION_AND_MAINTENANCE_OCCUPATIONS,
            ],
            denominator_codes=[Denominator.HISPANIC_CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPOCCPRODTRANS",
        display_name="Hispanic production and transportation occupations",
        description="Production, transportation, and material moving occupations",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24010I.MALE_PRODUCTION_TRANSPORTATION_AND_MATERIAL_MOVING_OCCUPATIONS,
                C24010I.FEMALE_PRODUCTION_TRANSPORTATION_AND_MATERIAL_MOVING_OCCUPATIONS,
            ],
            denominator_codes=[Denominator.HISPANIC_CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="INDAGRICULTURE",
        display_name="Agriculture employment",
        description="Employed in agriculture, forestry, fishing and hunting",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24030.MALE_AGRICULTURE_FORESTRY_FISHING_AND_HUNTING,
                C24030.FEMALE_AGRICULTURE_FORESTRY_FISHING_AND_HUNTING,
            ],
            denominator_codes=[Denominator.CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="INDCONSTRUCTION",
        display_name="Construction employment",
        description="Employed in construction",
        variable_computer=FractionalShare(
            numerator_codes=[C24030.MALE_CONSTRUCTION, C24030.FEMALE_CONSTRUCTION],
            denominator_codes=[Denominator.CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="INDMANUFACTURING",
        display_name="Manufacturing employment",
        description="Employed in manufacturing",
        variable_computer=FractionalShare(
            numerator_codes=[C24030.MALE_MANUFACTURING, C24030.FEMALE_MANUFACTURING],
            denominator_codes=[Denominator.CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="INDEDUHEALTH",
        display_name="Education and health employment",
        description="Employed in educational services, health care, and social assistance",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24030.MALE_EDUCATIONAL_SERVICES_AND_HEALTH_CARE_AND_SOCIAL_ASSISTANCE,
                C24030.FEMALE_EDUCATIONAL_SERVICES_AND_HEALTH_CARE_AND_SOCIAL_ASSISTANCE,
            ],
            denominator_codes=[Denominator.CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="INDACCOMFOOD",
        display_name="Accommodation and food employment",
        description="Employed in accommodation and food services",
        variable_computer=FractionalShare(
            numerator_codes=[
                C24030.MALE_ACCOMMODATION_AND_FOOD_SERVICES,
                C24030.FEMALE_ACCOMMODATION_AND_FOOD_SERVICES,
            ],
            denominator_codes=[Denominator.CIVILIAN_EMPLOYED],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPLFP",
        display_name="Hispanic labor force participation",
        description="In the labor force (labor force participation rate)",
        variable_computer=FractionalShare(
            numerator_codes=[
                C23002I.MALE_16_TO_64_YEARS_IN_LABOR_FORCE,
                C23002I.MALE_65_YEARS_AND_OVER_IN_LABOR_FORCE,
                C23002I.FEMALE_16_TO_64_YEARS_IN_LABOR_FORCE,
                C23002I.FEMALE_65_YEARS_AND_OVER_IN_LABOR_FORCE,
            ],
            denominator_codes=[Denominator.HISPANIC_16_AND_OVER],
        ),
    ),
    ModelVariable(
        source="ACS",
        var_name="HISPUNEMPRATE",
        display_name="Hispanic unemployment rate",
        description="Unemployed as a share of the labor force",
        variable_computer=FractionalShare(
            numerator_codes=[
                C23002I.MALE_16_TO_64_YEARS_IN_LABOR_FORCE_CIVILIAN_UNEMPLOYED,
                C23002I.MALE_65_YEARS_AND_OVER_IN_LABOR_FORCE_UNEMPLOYED,
                C23002I.FEMALE_16_TO_64_YEARS_IN_LABOR_FORCE_CIVILIAN_UNEMPLOYED,
                C23002I.FEMALE_65_YEARS_AND_OVER_IN_LABOR_FORCE_UNEMPLOYED,
            ],
            denominator_codes=HISPANIC_LABOR_FORCE,
        ),
    ),
]
