# The four within-Hispanic shares, most-reported first.
TARGETS = [
    "Hisp SOR Alone Pct of Hisp",
    "Hisp White SOR Pct of Hisp",
    "Hisp White Alone Pct of Hisp",
    "Hisp White Pct of Hisp",
]
WEIGHT_COL = "HISPANIC"  # the weight that turns a places question into a people one
FULL = "full"  # the baseline pseudo-group: the entire feature matrix

# The default tree hyperparameters: both tree models share the count and
# depth cap so their comparison measures the model family, not the tuning.
# Overridable per run (the CLI flags in regression.main feed straight here);
# the defaults are what every historical number was produced with.
DEFAULT_PARAMS = {
    "n_estimators": 100,
    "max_depth": 8,
    "learning_rate": 0.1,  # lgbm only
    "num_leaves": 31,  # lgbm only
}
