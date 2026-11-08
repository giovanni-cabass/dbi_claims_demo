# Claim dependency graph

Generated from `claims.json` by `generate_views.py` -- do not hand-edit.
An arrow `A --> B` means claim B depends on (cites as a premise) claim A.

```mermaid
graph TD
    dbi_static_gauge_formula["dbi_static_gauge_formula<br/>eq:static-gauge-formula"]
    dbi_boost_spatial_exact["dbi_boost_spatial_exact<br/>eq:delta-phi-spatial"]
    dbi_boost_temporal_hcorrected["dbi_boost_temporal_hcorrected<br/>eq:delta-phi-temporal"]
    dbi_boost_flat_precursor["dbi_boost_flat_precursor<br/>eq:flat-dbi-boost"]
    induced_metric_ds5_embedding["induced_metric_ds5_embedding<br/>eq:induced-metric"]
    dbi_static_gauge_formula --> dbi_boost_spatial_exact
    dbi_static_gauge_formula --> dbi_boost_temporal_hcorrected
```

**Claim count:** 5 citable claims (0 given, 5 established).
