# 02 · Mouse Data Available Now

## The published dataset: DANDI:000253

**"Allen Institute OpenScope – Global/Local Oddball project"**

| Field | Value |
|---|---|
| DANDI ID | [000253](https://dandiarchive.org/dandiset/000253) |
| Latest published version | `0.240923.1441` (2024-09-23) |
| Size | **~680 GB** (633 GiB; 679,753,396,585 bytes) |
| Assets | **98** NWB files |
| Subjects | 14 mice (incl. SSTAi32, PVAi32 lines) |
| Modality | **Neuropixels** (spikes + LFP), laminar |
| Brain areas | V1, LM, RL, AL, PM, AM (6 visual areas) |
| Contact | Jake Westerberg (Bastos Lab) |
| Embargo | OPEN |
| Format | NWB (Neurodata Without Borders) |

### What's in it — the global/local oddball

This is the **local–global** paradigm (the rodent/primate version of Bekinschtein–Dehaene):

- **Local oddball** `xxxY` — a repeated stimulus then a change (local surprise).
- **Global oddball** `xxxX` — a violation of the *learned sequence rule* even though the final
  stimulus locally repeats (global surprise; dissociates repetition from predictability).
- **Controls** — fully random sequences and fully predictable repetitions.
- Oriented drifting gratings, ~500 ms on / ~500–531 ms ISI.

This dataset is the one already analyzed in the eLife reviewed preprint **["Ubiquitous
predictive processing in the spectral domain of sensory cortex"](https://elifesciences.org/reviewed-preprints/109053)**
(Sennesh, Westerberg, Spencer-Smith, Bastos; bioRxiv `2025.07.31.667946`). Their analysis code is
public — see [`03-analysis-pipelines.md`](03-analysis-pipelines.md) (`BastosLab/epych`).

> **Why start here:** global/local is the paradigm with the strongest, oldest human EEG/MEG
> analogue, so a pipeline you build on 000253 transfers most directly to human data.

## The four newer community paradigms

The standard-oddball, sensorimotor, sequence, and temporal/duration paradigms (see
[`01`](01-project-overview.md)) are being collected under the community project. As of writing,
**000253 is the published, downloadable dataset**; the new-paradigm releases will appear under the
OpenScope / Allen Institute for Neural Dynamics DANDI account. To check for newer dandisets:

```bash
# search the DANDI archive for OpenScope predictive-processing dandisets
dandi ls "https://api.dandiarchive.org/api/dandisets/?search=openscope"
# or browse: https://dandiarchive.org/dandiset?search=oddball
```

Also watch the project's own data/analysis pages and DANDI links:
<https://allenneuraldynamics.github.io/openscope-community-predictive-processing/>

## Getting the data

### Option A — stream without downloading (recommended first step)

680 GB is large and your machine (GB10, 120 GB unified RAM) should **not** try to hold whole
sessions in memory. Stream individual objects over HTTP with `remfile`/`fsspec` — see
[`scripts/stream_first_nwb.py`](../scripts/stream_first_nwb.py) and
[`notebooks/00_stream_and_explore_nwb.ipynb`](../notebooks/00_stream_and_explore_nwb.ipynb).

### Option B — download one session locally

```bash
# list assets first, then pull a single NWB (tens of GB), not the whole 680 GB set
dandi ls DANDI:000253
bash scripts/download_dandi.sh 000253          # edit the script to pick one asset path
```

### Option C — DANDI Hub (cloud, zero local storage)

Analyze in the browser next to the data on AWS S3: <https://hub.dandiarchive.org/>. Good for a
first look before committing local disk.

> ⚠️ **GB10 / unified-memory note.** This box shares ~120 GB across CPU and GPU. Do not load whole
> sessions into memory; stream + window, and lazy-load spike times / LFP segments. See your infra note
> on the unified-memory OOM trap.

## License & citation

DANDI:000253 is OPEN. Cite the dandiset DOI (from its DANDI landing page) **and** the consortium
paper (arXiv:2504.09614) and the eLife spectral-domain preprint when using these data. Full list:
[`REFERENCES.md`](REFERENCES.md).
