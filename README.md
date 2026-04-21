# ICA Fitting Report

[![Abcdspec-compliant](https://img.shields.io/badge/ABCD_Spec-v1.1-green.svg)](https://github.com/brain-life/abcd-spec)
[![Run on Brainlife.io](https://img.shields.io/badge/Brainlife-bl.app.675-blue.svg)](https://doi.org/10.25663/brainlife.app.675)

## Description

This Brainlife.io app computes an Independent Component Analysis (ICA) decomposition on MEG/EEG data using MNE-Python. The app fits an ICA model to raw data with optional filtering and automatic detection of artifact components based on EOG/ECG channels.

## Inputs

- **mne**: Path to MNE raw `.fif` file containing MEG/EEG data

## Outputs

- **out_dir/ica.fif**: ICA decomposition object
- **out_figs/components_topo.png**: Topographic plot of ICA components
- **out_figs/component_*.png**: Detailed properties for individual components
- **out_report/report_ica.html**: Quality control report with component analysis, EOG/ECG correlations
- **product.json**: Metadata about ICA decomposition

## Configuration Parameters

- **n_components** (int, default: 20): Number of ICA components to estimate
- **method** (str, default: 'fastica'): ICA method ('fastica', 'picard', 'infomax', etc.)
- **l_freq** (float, optional): Low frequency cut-off for high-pass filtering before ICA
- **h_freq** (float, optional): High frequency cut-off for bandpass filtering
- **random_state** (int, optional): Seed for reproducible results
- **max_iter** (int or 'auto'): Maximum number of iterations during fitting
- **noise_cov** (optional): Noise covariance matrix for pre-whitening
- **fit_params** (dict, optional): Additional parameters passed to the ICA fit method
- **allow_ref_meg** (bool, default: False): Allow ICA on MEG reference channels
- **eog_ch** (str, optional): EOG channel name or index for artifact detection
- **ecg_ch** (str, optional): ECG channel name or index for artifact detection
- **picks_to_plot** (int, default: 5): Number of components to show detailed plots for

## Usage

The app is designed to run on the Brainlife.io platform via containerized execution. Provide a configuration file with the parameters listed above, and the app will generate ICA decomposition and associated visualizations.

## Technical Details

- Uses MNE-Python's `ICA` class for decomposition
- Automatically detects EOG and ECG artifact components via correlation analysis
- Generates interactive QC report using MNE Report
- All components are visualized for quality assessment
- Explained variance ratios are computed for each channel type
- Results compatible with ICA-apply for component exclusion
   

## Authors

- Saeed Zahran
- Maximilien Chaumon (https://github.com/dnacombo)

## Citations

Hayashi, S., Caron, B.A., Heinsfeld, A.S. et al. brainlife.io: a decentralized and open-source cloud platform to support neuroscience research. Nat Methods 21, 809–813 (2024). https://doi.org/10.1038/s41592-024-02237-2

### MNE-Python

Gramfort A, Luessi M, Larson E, Engemann DA, Strohmeier D, Brodbeck C, Goj R, Jas M, Brooks T, Parkkonen L, and Hämäläinen MS. **MEG and EEG data analysis with MNE-Python**. Frontiers in Neuroscience, 7(267):1–13, 2013. https://doi.org/10.3389/fnins.2013.00267

## Funding Acknowledgement

[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-1636893](https://img.shields.io/badge/NSF_BCS-1636893-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-ACI-1916518](https://img.shields.io/badge/NSF_ACI-1916518-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1916518)
[![NSF-IIS-1912270](https://img.shields.io/badge/NSF_IIS-1912270-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1912270)
[![NIH-NIBIB-R01EB030896](https://img.shields.io/badge/NIH_NIBIB-R01EB030896-green.svg)](https://grantome.com/grant/NIH/R01-EB030896-01)

## License

Copyright (c) 2026 brainlife.io

This project is licensed under the AGPL-3.0 License - see the LICENSE file for details.
