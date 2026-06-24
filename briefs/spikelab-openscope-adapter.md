# Agent Brief — OpenScope/Allen adapter for SpikeLab (mouse Neuropixels)

**Type:** scoped tooling contribution (adapter + upstream PR). **Not** an FM effort.
**Upstream:** [braingeneers/SpikeLab](https://github.com/braingeneers/SpikeLab) (v0.1.2).
**Prereq met:** feasibility gate passed 2026-06-23 (SpikeLab loads Allen OpenScope ecephys
NWB → `SpikeData` cleanly; see "Verified facts" below).

## Mission (one paragraph)
Make SpikeLab genuinely useful on **in-vivo mouse Neuropixels** OpenScope data by adding a thin
**OpenScope adapter** that enriches a loaded `SpikeData` with the things SpikeLab currently drops
(per-unit CCF + region, visual-stimulus structure, running/pupil behavior), plus a small set of
**EDA skills** (deviant-vs-standard PSTH, pool QC sweep). Land the generic improvements as an
**upstream PR**; keep OpenScope-specific glue in a separate adapter module. Reuse the already-
validated parsing in `openscope_nwb.py` — do **not** re-derive it.

## Verified facts (don't re-discover)
- **Install (no CUDA):** `uv pip install "spikelab[neo,io] @ git+https://github.com/braingeneers/SpikeLab.git"` (Python 3.12). `[neo]`=pynwb, `[io]`=pandas. **Avoid** `[kilosort4]`,`[hippie]` (Torch/CUDA → GB10 sm_121 wall).
- **Loader:** `from spikelab.data_loaders import load_spikedata_from_nwb(filepath: str, *, prefer_pynwb=True, length_ms=None, start_time_ms=None, allow_no_units=False) -> SpikeData`. **Path-only** (no streaming); reads `units.to_dataframe()` spike_times.
- **Gate result on DANDI:000253 session (`sub-647836_…_ogen.nwb`):** loads fine — `SpikeData(N=2170, length≈7.99e6 ms, 98.5M spikes)`, good session/subject metadata. **BUT** `sd.electrodes is None`, `sd.unit_locations is None`, `neuron_attributes == [{'unit_id': k}, …]` only; `sd.metadata['electrodes_by_channel']` exists (raw electrode info reachable, just not wired to units). **No stimulus, no behavior** are read.
- **`SpikeData` API surface (use, don't rebuild):** `N, length, start_time, train, times, idces_times, raster, sparse_raster, channel_raster, align_to_events, split_epochs, subtime, subset, binned, get_pop_rate, get_pairwise_ccg, get_pairwise_latencies, curate_by_{firing_rate,isi_violations,snr,min_spikes,merge_duplicates}, compute_waveform_metrics, neuron_attributes, metadata, unit_locations, neuron_to_channel_map, to_nwb, to_hdf5, plot, plot_aligned_pop_rate`.
- **Eval artifacts on T9 (reuse):** venv `/mnt/t9/venvs/spikelab-eval`; sample session `/mnt/t9/tmp/spikelab-eval/sub-647836_ses-1227858756_ogen.nwb`.

## Reuse this (the hard part is already done)
`spinning-up-in-openscope/brainsets_pipelines/allen_openscope_neuropixels/openscope_nwb.py`
(copy or vendor it) provides, pure-numpy, the OpenScope NWB drift handling the gate proved is
needed — **validated across 6 dandisets**:
- `unit_ccf(nwb)` → per-unit (coords, regions, link_method, ccf_cols). Handles **both** unit→electrode
  conventions (`peak_channel_id` id→row; newer `units.electrodes` region + `extremum_channel_index`
  peak — NOT first row), the **CCF plausibility guard** (rejects degenerate ~0–10 placeholders), and
  region-independent-of-CCF.
- `find_running(nwb)` / `resample_running(ts, rate, max_cm_s)` → handles `running`/`running_new`,
  `running_speed`/`running_speed_new`, artifact rejection (`|v|>150 cm/s`).
- `stim_tables(nwb)` → the `*presentations` tables (+ counts, visual cols).
- Pool status (one session each): **READY w/ real CCF** = 000253, 000248, 000563, 000690; **no CCF
  (region/probe-space only, need registration)** = 001191 (Loop), 001637 (PredProc-Ecephys).

## Deliverables (ordered)
1. **`spikelab_openscope` adapter** (new module, separate from SpikeLab core):
   `enrich_spikedata(sd, nwb_or_path) -> SpikeData` that, using `openscope_nwb`, sets per-unit
   `neuron_attributes` to include `ccf_x/ccf_y/ccf_z`, `region`, `peak_channel`; attaches a
   **stimulus event table** (start/stop + orientation/contrast/stimulus_name/block, incl. oddball
   labels where derivable) usable with `SpikeData.align_to_events`; and a **running-speed** series.
2. **EDA skills** (follow SpikeLab's own `src/spikelab/agent/` skill structure):
   `oddball_psth` (deviant-vs-standard via `align_to_events` + `get_pop_rate`/`binned`) and
   `pool_qc_sweep` (stream/download one session per READY dandiset, run `curate_by_*` + report).
3. **Upstream PR to braingeneers/SpikeLab:** make `load_spikedata_from_nwb` populate
   `unit_locations`/`neuron_attributes` from `electrodes_by_channel` for Allen-style NWB (it
   currently returns `None`). Optional second PR: `remfile`/fsspec streaming so multi-GB sessions
   needn't be fully downloaded. Keep these GENERIC (not OpenScope-specific).
4. **Tests + a `validate_openscope.py`** that loads `sub-647836` and asserts: CCF populated for a
   READY session, a stimulus event table with >0 rows, running present; and that 001637 degrades
   gracefully (region/none, no crash).

## Boundaries / non-goals (do not cross)
- **No FM work** — no spike tokenization, unit/CCF embeddings, masking, POYO, transformers. That
  lives in `torch_brain`/`brainsets`, not here.
- **No reimplementing AllenSDK / OpenScope Databook** analyses — only the thin adapter + a couple
  of skills. If an analysis already exists in SpikeLab, reuse it.
- **No sorting / Kilosort / CUDA** — use the provided NWB sorts (GB10 is sm_121).
- **Prefer upstream PR over a divergent fork.** Don't maintain a "mouse SpikeLab" fork.
- **Don't touch** the `spinning-up-in-openscope` FM scaffold (`brainsets_pipelines/`, `harness/`,
  `docs/`) except to copy `openscope_nwb.py`.

## Constraints
- **Home NVMe is ~98% full** — put venvs and downloaded NWB on **`/mnt/t9`** (1.2 TB free). Reuse
  `/mnt/t9/venvs/spikelab-eval` and `/mnt/t9/tmp/spikelab-eval/`. If the global uv cache errors,
  `export UV_CACHE_DIR=/mnt/t9/uv-cache-mhough`.
- Loader is **path-based** → download sessions to T9 (the smallest 000253 `_ogen` sessions are
  ~2.1 GB) unless/until the streaming PR lands.
- Work in a clone under `/mnt/t9` (e.g. `/mnt/t9/dev/SpikeLab`), not under `~`.

## Acceptance criteria
- `enrich_spikedata` on a READY session (000253) yields `SpikeData` whose `neuron_attributes`
  carry **finite, per-unit-varying CCF** (sanity: ≥100 distinct coords) + region; a stimulus event
  table; and a running series.
- `oddball_psth` produces a deviant-vs-standard population PSTH figure on 000253.
- `pool_qc_sweep` runs on ≥2 READY dandisets without error and reports unit counts + QC.
- Upstream `load_spikedata_from_nwb` PR opened (or patch + test ready) populating unit locations.
- 001637/001191 handled gracefully (region/none, no crash), with a logged note that they need CCF
  registration.

## Suggested launch
`subagent_type: general-purpose`, working dir under `/mnt/t9`. First action: read this brief and
`openscope_nwb.py`; reproduce the gate (`load_spikedata_from_nwb` on the cached `sub-647836`
session) before building. Report back the PR link + the adapter module path.
