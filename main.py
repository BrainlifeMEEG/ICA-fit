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
    - out_report/report_ica.html: QC report with component analysis
    - product.json: Metadata about ICA decomposition
"""

# Copyright (c) 2020 brainlife.io
#
# This app computes ICA decomposition on MNE raw data

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
    save_figure_with_base64
)

# Set up matplotlib for headless execution
setup_matplotlib_backend()

# Ensure output directories exist
ensure_output_dirs('out_dir', 'out_figs', 'out_report')

# Load configuration
config = load_config()
product_items = []

# == LOAD DATA ==
fname = config['mne']
raw = mne.io.read_raw_fif(fname, preload=True)

# == OPTIONAL FILTERING ==
if config.get('l_freq') is not None and config.get('h_freq') is not None:
    raw.filter(l_freq=config['l_freq'], h_freq=config['h_freq'])
    add_info_to_product(product_items, f'Applied bandpass filter: {config["l_freq"]}-{config["h_freq"]} Hz')

# == SET UP ICA ==
ica_params = {
    'n_components': int(config.get('n_components', 20)),
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
print(f'ICA fitted with {ica.n_components} components')

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
picks_to_plot = config.get('picks_to_plot', 5)
fs = ica.plot_properties(raw, picks=list(range(min(picks_to_plot, ica.n_components))), show=False)
for i, f in enumerate(fs):
    comp_fig_path = os.path.join('out_figs', f'component_{i:02d}.png')
    f.savefig(comp_fig_path, dpi=150)
    plt.close(f)

# == DETECT EOG/ECG ARTIFACTS ==
eog_evoked = None
ecg_evoked = None
eog_indices = []
ecg_indices = []

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
report.add_ica(ica, 'ICA Decomposition', inst=raw, 
               eog_evoked=eog_evoked, ecg_evoked=ecg_evoked,
               ecg_scores=ecg_indices, eog_scores=eog_indices)
report.save(os.path.join('out_report', 'report_ica.html'), overwrite=True)

# == CREATE PRODUCT.JSON ==
add_raw_info_to_product(product_items, raw)
add_image_to_product(product_items, components_fig_path, 'ICA Components')
add_info_to_product(product_items, f'ICA fitted with {ica.n_components} components, {len(ica.exclude)} excluded', msg_type='success')
create_product_json(product_items)



