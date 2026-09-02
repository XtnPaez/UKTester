# Configuration

All pipeline settings are read from `configs/config.yaml`. This file must be updated before running any scripts when adding a new country context.

## Required settings

### Country name

Set `country` to the full English name of your target country:

```yaml
country: Nepal
```

### Projected CRS

Add a projected CRS entry for the country under `analysis_crs`. This is used for all metric distance calculations.

```yaml
analysis_crs:
  Nepal: EPSG:24342
```

To find a suitable projected CRS, visit [epsg.io](https://epsg.io/) and search `<country> kind:PROJCRS`.

Countries already configured in `config.yaml`:

| Country | EPSG |
| --- | --- |
| Nepal | 24342 |
| Bangladesh | 9678 |
| Malawi | 20936 |
| UK | 27700 |
| Rwanda | 32736 |
| Switzerland | 2056 |

## Other settings

The following paths are set by default and should not normally need changing:

```yaml
data_dir: data/
outputs_dir: outputs/
datasets_config: configs/datasets.yaml
visualisation_crs: EPSG:4326 # i.e WSG84
```

`datasets_config` points to `configs/datasets.yaml`, which maps logical dataset names to file paths relative to `data_dir`. If you restructure data directories, update this file rather than the scripts.

## Next step

→ [03 — Data preparation](03-data-preparation.md)
