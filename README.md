# ICA initialize and fit


[![Abcdspec-compliant](https://img.shields.io/badge/ABCD_Spec-v1.1-green.svg)](https://github.com/brain-life/abcd-spec)
[![Run on Brainlife.io](https://img.shields.io/badge/Brainlife-bl.app.675-blue.svg)](https://doi.org/10.25663/brainlife.app.675)

Brainlife App to compute ICA object using `mne.preprocessing.ICA` and `ica.fit()`.


1) Input file is:
    * `meg/fif` meg data file
    
2) Input parameters:
    * `n_components` Number of principal components (from the pre-whitening PCA step) that are passed to the ICA algorithm during fitting.
    * `l_freq` Low frequency cut-off for (recommended) high-pass filtering before ICA. default is None (no high-pass filtering), but it is advisable to high-pass filter the data for best ICA decomposition.        
    * `method` The ICA method to use in the fit method. Use the fit_params argument to set additional parameters. Specifically, if you want Extended   Infomax, set method='infomax' and fit_params=dict(extended=True) (this also works for method='picard'). Defaults to 'fastica'. 
    * `noise_cov` Noise covariance used for pre-whitening. If None (default), channels are scaled to unit variance ("z-standardized") as a group by channel type prior to the whitening by PCA.
    * `eog_ch` EOG channel to be used to detect EOG events, create epochs and overlay with the same epochs after rejecting ICA components highly correlated with the channel. If no channel is provided, MNE will try to guess, and issue an error if no EOG channel is found.
    * `ecg_ch` ECG channel to be used to detect ECG events, create epochs and overlay with the same epochs after rejecting ICA components highly correlated with the channel. If no channel is provided, MNE will try to guess, and issue an error if no ECG channel is found.
    * `random_state` A seed for the NumPy random number generator (RNG). If None (default), the seed will be obtained from the operating system (see RandomState for details), meaning it will most likely produce different output every time this function or method is run. To achieve reproducible results, pass a value here to explicitly initialize the RNG with a defined state.
    * `max_iter` Maximum number of iterations during fit. If 'auto', it will set maximum iterations to 1000 for 'fastica' and to 500 for 'infomax' or 'picard'. The actual number of iterations it took ICA.fit() to complete will be stored in the n_iter_ attribute.
    * `allow_ref_meg` Allow ICA on MEG reference channels. Defaults to False.


3) Ouput files are:
    * `ica/fif` ica object file
    * a plots of the ICA components' topographies and properties
    * a html report showing the original and cleaned signal after eventual exclusion of components based on correlation with EOG and ECG channels.
   

## Authors
- Saeed ZAHRAN(saeedzahranutc@gmail.com)
- Maximilien Chaumon(maximilien.chaumon@icm-institute.org)

## Citations

*- brainlife.io Publishing and Apps:*

Avesani, P., McPherson, B., Hayashi, S. et al. **The open diffusion data derivatives, brain data upcycling via integrated publishing of derivatives and reproducible open cloud services**. Sci Data 6, 69 (2019). https://doi.org/10.1038/s41597-019-0073-y

*- MNE-Python package:* 

Gramfort A, Luessi M, Larson E, Engemann DA, Strohmeier D, Brodbeck C, Goj R, Jas M, Brooks T, Parkkonen L, and Hämäläinen MS.  **MEG and EEG data analysis with MNE-Python**. Frontiers in Neuroscience, 7(267):1–13, 2013. https://doi.org/10.3389/fnins.2013.00267

## Funding Acknowledgement
brainlife.io is publicly funded and for the sustainability of the project it is helpful to Acknowledge the use of the platform. We kindly ask that you acknowledge the funding below in your publications and code reusing this code.

[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-1636893](https://img.shields.io/badge/NSF_BCS-1636893-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-ACI-1916518](https://img.shields.io/badge/NSF_ACI-1916518-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1916518)
[![NSF-IIS-1912270](https://img.shields.io/badge/NSF_IIS-1912270-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1912270)
[![NIH-NIBIB-R01EB030896](https://img.shields.io/badge/NIH_NIBIB-R01EB030896-green.svg)](https://grantome.com/grant/NIH/R01-EB030896-01)


#### MIT Copyright (c) 2023 brainlife.io The University of Texas at Austin and Indiana University

## Citation

Hayashi, S., Caron, B.A., Heinsfeld, A.S. et al. brainlife.io: a decentralized and open-source cloud platform to support neuroscience research. Nat Methods 21, 809–813 (2024). https://doi.org/10.1038/s41592-024-02237-2
