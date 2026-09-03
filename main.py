"""
Compute ICA decomposition on raw MEG/EEG data.

This app fits an ICA decomposition to raw MEG/EEG data, with optional filtering
and automatic detection of EOG/ECG artifact components. It saves the ICA object,
visualizes components, and generates a comprehensive QC report.

Inputs:
    - mne: Path to MNE raw .fif file
    - n_components: Number of ICA components to estimate
    - method: ICA method ('fastica', 'picard', 'infomax', etc.)
    - l_freq/h_freq: Optional bandpass filtering parameters
    - picks_to_plot: Number of components to show detailed plots for
    - eog_ch: EOG channel name/index for artifact detection
    - ecg_ch: ECG channel name/index for artifact detection

Outputs:
    - out_dir/ica.fif: ICA decomposition object
    - out_figs/components_topo.png: Topographic plot of ICA components
    - out_figs/component_*.png: Detailed properties for selected components
    - out_report/report.html: QC report with component analysis
    - product.json: Metadata about ICA decomposition
"""

# Copyright (c) 2026 brainlife.io
#
# This app computes ICA decomposition on MNE raw data
#
# Authors:
# - Saeed Zahran
# - Maximilien Chaumon (https://github.com/dnacombo)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brainlife_utils'))

# Standard imports
import mne
from mne.preprocessing import ICA, create_ecg_epochs, create_eog_epochs
import matplotlib.pyplot as plt

# Import shared utilities
from brainlife_utils import (
    load_config,
    setup_matplotlib_backend,
    ensure_output_dirs,
    create_product_json,
    add_info_to_product,
    add_raw_info_to_product,
    add_image_to_product,
    save_figure_with_base64,
    require_config_keys
)

# Set up matplotlib for headless execution
setup_matplotlib_backend()

# Ensure output directories exist
ensure_output_dirs('out_dir', 'out_figs', 'out_report')

# Load configuration
config = load_config()
require_config_keys(config, ['mne'])
product_items = []

# == LOAD DATA ==
fname = config['mne']
raw = mne.io.read_raw_fif(fname, preload=True)

# == OPTIONAL FILTERING ==
if config.get('l_freq') is not None and config.get('h_freq') is not None:
    raw.filter(l_freq=config['l_freq'], h_freq=config['h_freq'])
    add_info_to_product(product_items, f'Applied bandpass filter: {config["l_freq"]}-{config["h_freq"]} Hz')

# == SET UP ICA ==
n_components = config.get('n_components', 20)
# n_components is legitimately a float in MNE's own API (a fraction of
# explained variance to keep, e.g. 0.999 -- the Wakeman & Henson value),
# not just a component count. Forcing int() truncated any such fraction to
# 0 (int(0.999) == 0), which then made ICA.fit() select zero components and
# crash with "Found array with 0 feature(s)" -- only cast to int when the
# value is actually a whole-number count.
if isinstance(n_components, str):
    n_components = float(n_components)
if isinstance(n_components, float) and n_components.is_integer() and n_components > 1:
    n_components = int(n_components)
ica_params = {
    'n_components': n_components,
    'random_state': config.get('random_state', 42),
    'method': config.get('method', 'fastica'),
}

# Add optional parameters
if config.get('noise_cov') is not None:
    ica_params['noise_cov'] = config['noise_cov']
if config.get('fit_params') is not None:
    ica_params['fit_params'] = config['fit_params']
if config.get('max_iter') is not None:
    ica_params['max_iter'] = config['max_iter']
if config.get('allow_ref_meg') is not None:
    ica_params['allow_ref_meg'] = config['allow_ref_meg']

ica = ICA(**ica_params)

# == FIT ICA ==
ica.fit(raw)
print(f'ICA fitted with {ica.n_components_} components')

# == PRINT EXPLAINED VARIANCE ==
explained_var_ratio = ica.get_explained_variance_ratio(raw)
for channel_type, ratio in explained_var_ratio.items():
    msg = f'Fraction of {channel_type} variance explained by all components: {ratio:.4f}'
    print(msg)
    add_info_to_product(product_items, msg)

# == SAVE ICA ==
ica.save(os.path.join('out_dir', 'ica.fif'), overwrite=True)

# == PLOT COMPONENTS TOPOGRAPHY ==
plt.figure(figsize=(15, 8))
ica.plot_components(show=False)
components_fig_path = os.path.join('out_figs', 'components_topo.png')
plt.savefig(components_fig_path, dpi=150)
plt.close()

# == PLOT DETAILED COMPONENT PROPERTIES ==
# picks_to_plot's declared app default is "" (an empty-string config field,
# same as everywhere else in this repo), which load_config() converts to
# None -- config.get('picks_to_plot', 5) does NOT catch that, since the key
# is present (just None-valued), not absent, so .get()'s own default never
# kicks in. Docstring says "None will pick the first 5 components", so
# handle that explicitly instead of relying on .get()'s fallback.
picks_to_plot = config.get('picks_to_plot')
if picks_to_plot is None:
    picks_to_plot = 5
# ica.n_components is the ORIGINAL fit parameter (still 0.999 here, a float
# fraction of variance -- confirmed via the app's own log line above), not
# the actual number of components found. list(range(...)) needs an int, and
# min(int, 0.999) always silently picks the float anyway (0.999 < 5) even
# when it's not: use ica.n_components_ (trailing underscore -- the real
# fitted count, e.g. 223) instead.
fs = ica.plot_properties(raw, picks=list(range(min(picks_to_plot, ica.n_components_))), show=False)
for i, f in enumerate(fs):
    comp_fig_path = os.path.join('out_figs', f'component_{i:02d}.png')
    f.savefig(comp_fig_path, dpi=150)
    plt.close(f)

# == DETECT EOG/ECG ARTIFACTS ==
# NOTE: component exclusion is deliberately NOT this app's job -- that's
# done downstream by ICA-apply. eog_ch/ecg_ch are only set here if a caller
# explicitly wants a preview scored in *this* app's own report; leaving
# them unset (the normal case in this pipeline) is expected, not an error.
eog_evoked = None
ecg_evoked = None
eog_indices = []
ecg_indices = []
eog_scores = None
ecg_scores = None

if config.get('eog_ch') and config['eog_ch'] != 'None':
    try:
        eog_evoked = create_eog_epochs(raw, ch_name=config['eog_ch'], verbose=False).average()
        eog_indices, eog_scores = ica.find_bads_eog(raw, ch_name=config['eog_ch'])
        print(f'Found {len(eog_indices)} EOG artifact components')
        add_info_to_product(product_items, f'Found {len(eog_indices)} EOG artifact components: {eog_indices}')
    except Exception as e:
        add_info_to_product(product_items, f'Could not detect EOG artifacts: {str(e)}', 'warning')

if config.get('ecg_ch') and config['ecg_ch'] != 'None':
    try:
        ecg_evoked = create_ecg_epochs(raw, ch_name=config['ecg_ch'], verbose=False).average()
        ecg_indices, ecg_scores = ica.find_bads_ecg(raw, ch_name=config['ecg_ch'])
        print(f'Found {len(ecg_indices)} ECG artifact components')
        add_info_to_product(product_items, f'Found {len(ecg_indices)} ECG artifact components: {ecg_indices}')
    except Exception as e:
        add_info_to_product(product_items, f'Could not detect ECG artifacts: {str(e)}', 'warning')

# Combine detected artifacts
ica.exclude = list(set(eog_indices + ecg_indices))
print(f'Total excluded components: {len(ica.exclude)}')

# == CREATE REPORT ==
report = mne.Report(title='ICA Fitting Report')
# Pass the real score arrays (find_bads_eog/ecg's 2nd return value), not
# the index lists -- report.add_ica's ecg_scores/eog_scores parameters are
# score arrays, not indices. Also pass None (not an empty list) when
# nothing was detected/scored: MNE's plot_ica_scores does `scores[0]`
# unconditionally, which IndexErrors on []. Confirmed on the ICM cluster:
# the previous ecg_scores=ecg_indices/eog_scores=eog_indices with both
# unset (this pipeline's normal case) crashed exactly that way.
report.add_ica(ica, 'ICA Decomposition', inst=raw,
               eog_evoked=eog_evoked, ecg_evoked=ecg_evoked,
               ecg_scores=ecg_scores, eog_scores=eog_scores)
report.save(os.path.join('out_report', 'report.html'), overwrite=True, verbose=False)

# == CREATE PRODUCT.JSON ==
add_raw_info_to_product(product_items, raw)
add_image_to_product(product_items, components_fig_path, 'ICA Components')
add_info_to_product(product_items, f'ICA fitted with {ica.n_components} components, {len(ica.exclude)} excluded', msg_type='success')
create_product_json(product_items)



