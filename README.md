# ICA Fitting Report

<!-- brainlife-app:begin (generated from the App manifest; edit the manifest, not this block) -->

> **Fits an ICA decomposition to raw MEG/EEG data with MNE-Python, with optional pre-filtering, and outputs the ICA solution, component plots and an HTML QC report with EOG/ECG scores.**

Fits mne.preprocessing.ICA (fastica, picard or infomax) on the raw data, high/low-pass filtering a copy first when l_freq and h_freq are set, and plots component topographies and properties. When eog_ch/ecg_ch are given, the report shows which components correlate with EOG/ECG artifacts, but no component is removed. Use it before an ICA-apply App to remove ocular or cardiac artifacts.

| | |
|---|---|
| 📥 **Inputs** | `neuro/meeg/mne/raw` |
| 📤 **Outputs** | `neuro/meeg/mne/ica` · `generic/image/png` · `report/html` |
| 🐳 **Container** | `brainlifemeeg/mne:1.12.1` |
| ⚙️ **Resources** | 4 CPUs · 32 GB memory |
| 🔗 **Run it** | [doi.org/10.25663/brainlife.app.675](https://doi.org/10.25663/brainlife.app.675) |

#### 📥 Inputs

| Input | Datatype | Required | Description |
|---|---|---|---|
| `fif` | `neuro/meeg/mne/raw` | yes | Continuous MEG/EEG data in MNE raw .fif format. |

#### 📤 Outputs

| Output | Datatype | Description |
|---|---|---|
| `out_dir` | `neuro/meeg/mne/ica` | Fitted ICA decomposition (ica.fif). |
| `out_figs` | `generic/image/png` | Topographic plot of the first ICA components and property plots of selected components (PNG). |
| `out_report` | `report/html` | HTML QC report with the ICA decomposition, component properties and EOG/ECG scores. |

<details>
<summary><b>⚙️ Parameters</b> (14)</summary>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `n_components` | number |  | Number of principal components (from the pre-whitening PCA step) that are passed to the ICA algorithm during fitting. |
| `l_freq` | number |  | Low frequency cut-off for (recommended) high-pass filtering before ICA. default is None (no high-pass filtering), but it is advisable to high-pass filter the data for best ICA decomposition. Notice: the filtered data is not saved. You have to use the filtering app if you want to use filtered data subsequently. |
| `h_freq` | number |  | High frequency cut-off for low-pass filtering before ICA. default is None (no low-pass filtering). Notice: the filtered data is not saved. You have to use the filtering app if you want to use filtered data subsequently. |
| `method` | string | `fastica` | The ICA method to use in the fit method. Use the fit_params argument to set additional parameters. Specifically, if you want Extended Infomax, set method='infomax' and fit_params=dict(extended=True) (this also works for method='picard'). Defaults to 'fastica'. |
| `noise_cov` | string |  | Noise covariance used for pre-whitening. If None (default), channels are scaled to unit variance (“z-standardized”) as a group by channel type prior to the whitening by PCA. |
| `random_state` | number |  | A seed for the NumPy random number generator (RNG). If None (default), the seed will be obtained from the operating system (see RandomState for details), meaning it will most likely produce different output every time this function or method is run. To achieve reproducible results, pass a value here to explicitly initialize the RNG with a defined state. |
| `max_iter` | string | `auto` | Maximum number of iterations during fit. If 'auto', it will set maximum iterations to 1000 for 'fastica' and to 500 for 'infomax' or 'picard'. The actual number of iterations it took ICA.fit() to complete will be stored in the n_iter_ attribute. |
| `allow_ref_meg` | boolean | `false` | Allow ICA on MEG reference channels. Defaults to False. |
| `eog_ch` | string |  | EOG channel to be used to detect EOG events, create epochs and overlay with the same epochs after rejecting ICA components highly correlated with the channel. If no channel is provided, MNE will try to guess, and issue an error if no EOG channel is found. |
| `ecg_ch` | string |  | ECG channel to be used to detect ECG events, create epochs and overlay with the same epochs after rejecting ICA components highly correlated with the channel. If no channel is provided, MNE will try to guess, and issue an error if no ECG channel is found. |
| `picks_to_plot` | string |  | Indices of the independent components (ICs) to visualize. If an integer, represents the index of the IC to pick. Multiple ICs can be selected using a list of int or a slice. The indices are 0-indexed, so picks=1 will pick the second IC: ICA001. None will pick the first 5 components. |
| `fit_params` | string |  | Additional parameters passed to the ICA estimator as specified by method. Allowed entries are determined by the various algorithm implementations: see FastICA, picard(), infomax(). |
| `decim` | number |  | Decimation factor applied only during ICA fitting (ica.fit(raw, decim=N) -- every Nth sample is used to fit, full-resolution data is unaffected everywhere else). Speeds up fitting substantially with little accuracy cost, since ICA components are spatial patterns, not fine temporal detail. If None (default), no decimation. |
| `picks` | string |  | Channels the ICA is fit on: 'meg', 'mag', 'grad' or 'eeg'. If empty (default), every data channel (MEG + EEG) not marked bad is used. Restricting the fit to one channel type keeps channels of the other types, which may contain unmarked bad channels, from taking components. |

</details>

📚 **References used by this App:**
- Hayashi S, Caron BA, Heinsfeld AS, et al. brainlife.io: a decentralized and open-source cloud platform to support neuroscience research. Nat Methods 21:809-813 (2024). [doi:10.1038/s41592-024-02237-2](https://doi.org/10.1038/s41592-024-02237-2)
- Gramfort A, et al. MEG and EEG data analysis with MNE-Python. Front Neurosci 7:267 (2013). [doi:10.3389/fnins.2013.00267](https://doi.org/10.3389/fnins.2013.00267)

<!-- brainlife-app:end -->

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
| `picks` | string | `""` | Channels the ICA is fit on (`ica.fit(raw, picks=...)`): `meg`, `mag`, `grad` or `eeg`. Empty/unset keeps MNE's default, every data channel (MEG + EEG) not marked bad. Restricting the fit to one channel type keeps channels of the other types, which may contain unmarked bad channels, from taking components. Any other value is an error. |

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
