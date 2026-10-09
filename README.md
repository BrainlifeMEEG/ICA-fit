# ICA Fitting Report

[![Run on Brainlife.io](https://img.shields.io/badge/Brainlife-bl.app.675-blue.svg)](https://doi.org/10.25663/brainlife.app.675)

## Description

This Brainlife.io app computes an Independent Component Analysis (ICA) decomposition on MEG/EEG raw data using MNE-Python's `mne.preprocessing.ICA`. The app fits an ICA model to the raw data (with optional high/low-pass filtering applied only for the fit), computes explained-variance diagnostics, and previews EOG/ECG artifact components for quality control. Component exclusion itself is not performed here — it is the job of the downstream `ICA-apply` app.

The app generates:
- The fitted ICA decomposition (`ica.fif`)
- A topographic plot of the ICA components
- Detailed property plots for a selectable number of components
- An HTML QC report with the ICA decomposition, component properties, and EOG/ECG scores
- A `product.json` summarizing the fit and embedding the component images

## Inputs

- **`mne`** (`neuro/meeg/mne/raw`): continuous MEG/EEG raw data to decompose with ICA (required)

## Outputs

- **`out_dir/ica.fif`**: fitted ICA decomposition object
- **`out_figs/components_topo.png`**: topographic plot of the first 20 ICA components
- **`out_figs/component_NN.png`**: detailed property plot for each of the selected components
- **`out_report/report.html`**: QC report with the ICA decomposition, component properties, and EOG/ECG correlation scores
- **`product.json`**: summary of the fit (explained variance, detected EOG/ECG components) with the component images embedded

## Configuration Parameters

| key | type | default | description |
|---|---|---|---|
| `n_components` | number | `None` | Number of principal components (from the pre-whitening PCA step) passed to the ICA algorithm during fitting. Can be an integer count or a float fraction of explained variance to keep (e.g. `0.999`). `None` lets MNE's `ICA` use its own default. |
| `l_freq` | number | `None` | Low frequency cut-off for optional high-pass filtering of the raw data before ICA. Filtering is only applied if both `l_freq` and `h_freq` are set; the filtered data itself is not saved. |
| `h_freq` | number | `None` | High frequency cut-off for optional filtering before ICA (see `l_freq`). |
| `method` | string | `"fastica"` | ICA method passed to `ICA(method=...)` (`'fastica'`, `'picard'`, `'infomax'`, etc.). Use `fit_params` for extended-Infomax/Picard options. |
| `noise_cov` | string | `None` | Optional noise covariance used for pre-whitening. If unset, channels are z-standardized by type instead. |
| `random_state` | number | `None` | Seed for the NumPy random number generator, for reproducible fits. |
| `max_iter` | string | `"auto"` | Maximum number of iterations during fit. `'auto'` sets 1000 for `'fastica'` and 500 for `'infomax'`/`'picard'`. |
| `allow_ref_meg` | boolean | `false` | Allow ICA on MEG reference channels. |
| `eog_ch` | string | `None` | EOG channel name (or index) used to preview EOG artifact components in this app's own report (does not exclude components). |
| `ecg_ch` | string | `None` | ECG channel name (or index) used to preview ECG artifact components in this app's own report (does not exclude components). |
| `picks_to_plot` | number | `5` | Number of components to generate detailed property plots for. `None`/unset defaults to the first 5 fitted components. |
| `fit_params` | string | `None` | Additional parameters passed to the ICA estimator (`FastICA`, `picard()`, `infomax()`), as a dict. |
| `decim` | number | `None` | Decimation factor applied only during fitting (`ica.fit(raw, decim=N)`): every Nth sample is used to fit, while the saved ICA solution and all other data are unaffected. `None` (default) means no decimation. |

## Usage

### Running on Brainlife.io

1. Select your MEG/EEG raw `.fif` dataset as the `mne` input.
2. Optionally set `l_freq`/`h_freq` to high/low-pass filter the data before fitting (recommended for best ICA decomposition).
3. Optionally set `eog_ch`/`ecg_ch` to preview automatically detected EOG/ECG artifact components in the report.
4. Adjust `n_components`, `method`, `max_iter`, `decim`, and the other advanced parameters as needed.
5. Submit the process.

### Local Testing

```bash
# Edit config.json to point "mne" at a real raw .fif file, then:
python main.py
```

## Technical Details

- Uses MNE-Python's `ICA` class for decomposition.
- Previews EOG and ECG artifact components via correlation analysis (`find_bads_eog`/`find_bads_ecg`); exclusion is performed downstream by `ICA-apply`.
- Generates an interactive QC report using `mne.Report`.
- Explained variance ratios are computed per channel type for diagnostic purposes.
- Results are compatible with `ICA-apply` for component exclusion.

## Authors

- Saeed Zahran (https://github.com/saeedzahranutc)
- Maximilien Chaumon (https://github.com/dnacombo)

## Citations

We kindly ask that you cite the following articles when publishing papers and code using this app:

Hayashi, S., Caron, B.A., Heinsfeld, A.S. et al. brainlife.io: a decentralized and open-source cloud platform to support neuroscience research. Nat Methods 21, 809–813 (2024). https://doi.org/10.1038/s41592-024-02237-2

Gramfort A, Luessi M, Larson E, Engemann DA, Strohmeier D, Brodbeck C, Goj R, Jas M, Brooks T, Parkkonen L, and Hämäläinen MS. MEG and EEG data analysis with MNE-Python. Frontiers in Neuroscience, 7(267):1–13, 2013. https://doi.org/10.3389/fnins.2013.00267

## Funding Acknowledgement

brainlife.io is publicly funded and for the sustainability of the project we kindly ask that you acknowledge the following funding sources:

[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-1636893](https://img.shields.io/badge/NSF_BCS-1636893-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-ACI-1916518](https://img.shields.io/badge/NSF_ACI-1916518-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1916518)
[![NSF-IIS-1912270](https://img.shields.io/badge/NSF_IIS-1912270-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1912270)
[![NIH-NIBIB-R01EB029272](https://img.shields.io/badge/NIH_NIBIB-R01EB029272-green.svg)](https://grantome.com/grant/NIH/R01-EB029272-01)
[![NIH-NIBIB-R01EB030896](https://img.shields.io/badge/NIH_NIBIB-R01EB030896-green.svg)](https://grantome.com/grant/NIH/R01-EB030896-01)

## License

Copyright (c) 2026 MEEG Brainlife team. Licensed under AGPL-3.0, see [license.txt](license.txt).
