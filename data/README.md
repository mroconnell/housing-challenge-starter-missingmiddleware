# Data

Do **not** commit raw or large data to this repository. The root `.gitignore` already ignores everything in `data/` except this README and the `sample/` folder.

## How to obtain the data

Every candidate source is listed, with access steps and a data dictionary, in [docs/data-sources/](../docs/data-sources/README.md).

To refresh the small samples in `data/sample/`:

```sh
python3 scripts/fetch_samples.py            # all sources, standard library only
python3 scripts/build_data_dictionaries.py  # rewrite docs/data-sources/
```

The CSV samples are attribute snapshots, not spatial inputs. A few complete features per spatial source are in `data/sample/geo/` as GeoJSON, to show the geometry shape. See [What the samples leave out](../docs/data-sources/README.md#what-the-samples-leave-out).

[Full-data download steps for the sources the model uses go here once we pick them. Each step should keep full geometry, page through every record, record the coordinate system, and check joins.]

## Sample data

Keep only small, shareable samples in `data/sample/` so tests and demos can run without the full datasets. Confirm that any sample you commit is permitted by that dataset's license and contains no sensitive or restricted records.

## Provenance

Full source, version, license, and cleaning details for every dataset go in [docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md).
