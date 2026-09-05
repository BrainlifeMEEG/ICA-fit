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
    - decim: Optional decimation factor for fitting speed only (every Nth
      sample used to fit; saved/plotted data is unaffected)
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
import datetime
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

ica = ICA(**ica_params, verbose='INFO')

# == FIT ICA ==
# sklearn's FastICA has no per-iteration progress hook at all (an opaque
# blocking call), so this can legitimately show no new output for a long
# time even while genuinely computing -- that ambiguity is exactly what
# made a real, slow-but-correct fit look indistinguishable from a hang on
# the ICM cluster. verbose='INFO' (not 'DEBUG': that leaked into other
# calls below, e.g. report.save()'s own verbose=False stopped suppressing
# the HTML-asset "Embedding: ..." lines once this was 'DEBUG' -- MNE's
# logging isn't fully scoped to one object) keeps the two useful sub-step
# messages ("please be patient" / "Selecting by explained variance");
# combined with `main`'s python3 -u (unbuffered stdout, fixed alongside
# this), every print below now actually reaches the live slurm log instead
# of sitting in a buffer until the process exits.
# decim: fit on every Nth sample only (ica.fit's own decim kwarg -- affects
# fitting speed only, the saved ICA/raw data elsewhere are untouched). None
# (the default, no key or config['decim'] is None) means no decimation.
decim = config.get('decim')
if decim is not None:
    decim = int(decim)
print(f'[{datetime.datetime.now().isoformat()}] Starting ICA fit '
      f'({ica_params["method"]}, n_components={ica_params["n_components"]}, '
      f'decim={decim}) on {len(raw.ch_names)} channels, {raw.n_times} samples...',
      flush=True)
ica.fit(raw, decim=decim)
print(f'[{datetime.datetime.now().isoformat()}] ICA fit done, '
      f'{ica.n_components_} components', flush=True)

# == PRINT EXPLAINED VARIANCE ==
# The two earlier OOM "fixes" here (bounding report.add_ica's picks, then
# passing it inst=None) made zero observed difference on the ICM cluster --
# confirmed by the crash logs: no "Fraction of ... variance explained" line
# ever appeared, even though that print comes from THIS block, which runs
# before ica.save() and before any of the report/plotting code touched by
# those attempts. The real cost is here: ica.get_explained_variance_ratio()
# internally does inst.copy() + ica.apply(..., n_pca_components=0) (a full
# reconstruction of the recording from all components) + two independent
# get_data() calls, once per channel type (mag/grad) -- several more
# full-recording-sized arrays stacked on the ~20GB already resident from
# loading/filtering/fitting, on a 6-run-concatenated ~49min recording, is
# what actually exceeds 32GB. This print is purely informational (never
# used to drive fit/exclusion logic below), so compute it on a capped-size
# copy rather than the full recording -- correctness of a diagnostic
# variance-explained percentage doesn't need every sample, and this caps
# the cost regardless of whether `decim` above happens to be configured.
max_var_samples = int(raw.info['sfreq'] * 300)  # 5 minutes
if raw.n_times > max_var_samples:
    var_step = -(-raw.n_times // max_var_samples)  # ceiling division, no extra import
    var_inst = raw.copy().resample(raw.info['sfreq'] / var_step, npad='auto', verbose=False)
else:
    var_inst = raw
explained_var_ratio = ica.get_explained_variance_ratio(var_inst)
del var_inst
for channel_type, ratio in explained_var_ratio.items():
    msg = f'Fraction of {channel_type} variance explained by all components: {ratio:.4f}'
    print(msg)
    add_info_to_product(product_items, msg)

# == SAVE ICA ==
ica.save(os.path.join('out_dir', 'ica.fif'), overwrite=True)

# == PLOT COMPONENTS TOPOGRAPHY ==
# picks= an explicit range, NOT the previous no-picks call: ica.plot_components()
# batches components into groups of 20 per figure whenever there are more
# than 20 (118 here -> 6 figures: 0-19, 20-39, ..., 100-117), and since its
# own default is axes=None it always creates a fresh figure of its own --
# the plt.figure() previously called here never fed it, so it was dead
# code, and plt.savefig() below was silently saving whichever figure was
# left "current" afterward: the LAST one (components 100-117), not the
# first as intended. Limiting picks to the first 20 fixes both problems in
# one go (exactly one figure, matching MNE's own per-figure batch size)
# and is what was actually wanted -- an at-a-glance overview, not every
# component.
topo_picks = list(range(min(20, ica.n_components_)))
topo_fig = ica.plot_components(picks=topo_picks, show=False)
if isinstance(topo_fig, list):
    topo_fig = topo_fig[0]
components_fig_path = os.path.join('out_figs', 'components_topo.png')
# save_figure_with_base64: full-res file (out_figs/, for real inspection)
# + a much-lower-dpi thumbnail returned here for product.json below.
# product.json has a hard 1MB cap -- hit for real (1.09MB) with this one
# image alone at its previous full-150dpi/118-component size, before the
# per-component properties thumbnails below were even being embedded at
# all. dpi=30 leaves comfortable headroom for both together.
topo_base64 = save_figure_with_base64(topo_fig, components_fig_path, dpi_file=150, dpi_base64=30)

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
plot_picks = list(range(min(picks_to_plot, ica.n_components_)))
fs = ica.plot_properties(raw, picks=plot_picks, show=False)
# fs stays open (close_fig=False below) -- embedded into the HTML report
# further down, reusing this same render instead of having
# report.add_ica() recompute it a second time. Closed once that's done.
# Also collects a low-dpi base64 thumbnail per figure for product.json,
# same dual-dpi convention as the topo plot above -- these weren't
# embedded in product.json at all before (only saved to out_figs/), which
# is why the "a screen sized copy of components_topo + a handful of
# properties plots" request needs both, not just the one that already
# happened to be embedded (at full res, which is what blew the 1MB cap).
component_captions = []
component_base64 = []
for i, f in enumerate(fs):
    comp_fig_path = os.path.join('out_figs', f'component_{i:02d}.png')
    component_captions.append(f'ICA component {plot_picks[i]}')
    component_base64.append(
        save_figure_with_base64(f, comp_fig_path, dpi_file=150, dpi_base64=30, close_fig=False)
    )

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
# verbose=False on every call here (matching epoch/main.py's convention) --
# report-building is chatty (per-embedded-asset "Embedding: jquery...js"
# lines, etc.) and unrelated to the fit progress messages above, which
# stay at 'INFO' on purpose.
report = mne.Report(title='ICA Fitting Report', verbose=False)
# Pass the real score arrays (find_bads_eog/ecg's 2nd return value), not
# the index lists -- report.add_ica's ecg_scores/eog_scores parameters are
# score arrays, not indices. Also pass None (not an empty list) when
# nothing was detected/scored: MNE's plot_ica_scores does `scores[0]`
# unconditionally, which IndexErrors on []. Confirmed on the ICM cluster:
# the previous ecg_scores=ecg_indices/eog_scores=eog_indices with both
# unset (this pipeline's normal case) crashed exactly that way.
# inst=None here (NOT raw) -- bounding picks alone (first attempt, commit
# d841371) did NOT fix the real OOM: confirmed on the ICM cluster, a
# second crash with picks already limited to plot_picks died at the exact
# same point with the exact same RSS trajectory. Root cause is
# report.add_ica's OTHER inst-driven step, unconditional whenever inst is
# not None regardless of picks: it calls ica.plot_overlay(inst=raw, ...),
# which (per MNE's own plot_ica_overlay source) does
# `ica.apply(inst.copy(), ..., start=0, stop=3)` -- .copy() duplicates the
# ENTIRE preloaded raw array (a second ~10GB+ copy stacked on the ~20GB
# already resident from loading+filtering+fitting) just to plot 3 seconds
# of before/after signal. inst=None skips this overlay entirely, and per
# report.add_ica's own docstring ("To only plot the ICA component
# topographies, explicitly pass None") also skips its properties
# recomputation -- which would otherwise redo the exact plot_properties()
# call already made above. The already-rendered `fs` figures are embedded
# directly instead, so the report doesn't lose that content, just the
# redundant recompute and the unbounded overlay.
# NOTE: no verbose= here -- unlike report.save()/mne.Report(), add_ica()
# has no verbose parameter at all in this MNE version (confirmed both
# locally and via a real cluster traceback: `verbose=False` had been on
# this call since before this OOM investigation started, masked the whole
# time because the process never reached this line until the
# get_explained_variance_ratio() fix above let it get this far).
report.add_ica(ica, 'ICA Decomposition', inst=None,
               eog_evoked=eog_evoked, ecg_evoked=ecg_evoked,
               ecg_scores=ecg_scores, eog_scores=eog_scores)
if fs:
    report.add_figure(fig=fs, title='ICA component properties',
                       caption=component_captions, section='ICA Decomposition')
for f in fs:
    plt.close(f)
report.save(os.path.join('out_report', 'report.html'), overwrite=True, verbose=False)

# == CREATE PRODUCT.JSON ==
add_raw_info_to_product(product_items, raw)
# base64_data=... (not filepath=) for both -- filepath= embeds the FULL-res
# file, which is exactly what pushed product.json over its 1MB cap before
# (the topo image alone was 860KB at 150dpi/118 components, ~1.14MB once
# base64-encoded, and that was the ONLY image being embedded). These reuse
# the low-dpi thumbnails already computed above; the full-res files are
# still written to out_figs/ for real inspection.
add_image_to_product(product_items, 'ICA Components', base64_data=topo_base64)
for i, b64 in enumerate(component_base64):
    add_image_to_product(product_items, f'ICA component {plot_picks[i]} properties', base64_data=b64)
add_info_to_product(product_items, f'ICA fitted with {ica.n_components} components, {len(ica.exclude)} excluded', msg_type='success')
create_product_json(product_items)



