# 03 · Analysis Pipelines & Containers

Concrete, current (2024–2026) tooling to download/stream and analyze DANDI:000253, grouped by
purpose. Versions are noted where verified; re-check at install time.

> **GB10 note:** all the *core* NWB tools (pynwb, dandi, remfile, h5py) are pure-Python or ship
> self-contained manylinux wheels — they do **not** touch CUDA, so the sm_121 wheel problem does
> **not** apply. The CUDA risk is only in **spike sorting** (Kilosort 2.5/4 on sm_121); use CPU
> sorters or skip re-sorting (000253 ships sorted units).

## 1 · Data access

| Tool | Purpose | Install / use |
|---|---|---|
| **dandi-cli** (0.76.x, Py≥3.10) | download / validate / organize | `pip install dandi` → `dandi download DANDI:000253` or pin `DANDI:000253/0.240923.1441` (reserve ~680 GB) |
| **remfile + h5py + pynwb** | stream one NWB over S3, no full download | `pip install remfile fsspec aiohttp h5py pynwb` (see [`scripts/stream_first_nwb.py`](../scripts/stream_first_nwb.py)) |
| **LINDI** | faster remote NWB loads | `pip install lindi` |
| **Neurosift** | in-browser NWB viz, streams from DANDI | <https://neurosift.app> · [repo](https://github.com/flatironinstitute/neurosift) |
| **DANDI Hub** | free cloud JupyterHub next to the data (T4 GPU option) | <https://hub.dandiarchive.org> — best first look; "not for heavy compute" |

- Dandiset: <https://dandiarchive.org/dandiset/000253> · DOI `10.48324/dandi.000253/0.240923.1441` · **CC-BY-4.0**.

## 2 · NWB / electrophysiology stack

| Tool | Purpose | Install |
|---|---|---|
| **PyNWB** (3.1.x) | canonical NWB read/write API | `pip install -U pynwb` |
| **NWBWidgets** | Jupyter navigation of an NWB file | `pip install nwbwidgets` → `nwb2widget(nwbfile)` |
| **OpenScope Databook** (Py3.10) | Allen's executable notebooks (LFP, unit QC, receptive fields, optotagging, stimulus-aligned unit responses≈PSTH, CSD, Suite2p, CEBRA/TCA/GLM) | `pip install uv && uv sync --frozen --extra dev --python 3.10 && uv run jupyter notebook ./docs` · [repo](https://github.com/AllenInstitute/openscope_databook) |
| **AllenSDK** (2.16.2, **Py3.8–3.11 only**) | Allen Brain Observatory access + QC/methods reference | `pip install allensdk` — pin a 3.10/3.11 env; for 000253 load NWB directly with PyNWB, use AllenSDK as the methods reference |
| **SpikeInterface** (0.104.x, Py≥3.10) | (re)sorting, preprocessing, QC, viz | `pip install "spikeinterface[full,widgets]"` |

> **Oddball caveat:** the Databook has a *Global/Local Oddball* **project** page but **no dedicated
> oddball-analysis notebook**. Adapt its stimulus-aligned "unit responses" notebook into a proper
> deviant-vs-standard PSTH, and port the eLife paper's spectral analysis (below).

### The reference analysis for THIS dataset

Bastos Lab's **[`epych`](https://github.com/BastosLab/epych)** — the code behind the eLife
spectral-domain preprint, in `notebooks/passiveglo`. It does spectrograms (Syncopy), aperiodic/
oscillatory separation (**FOOOF/specparam**), band power (theta / alpha-beta / gamma), and
**laminar CSD** (Elephant), with cluster-based permutation stats. This is your template for the
mouse side and defines the contrasts to mirror in human EEG.

```bash
git clone https://github.com/BastosLab/epych && cd epych
# see notebooks/passiveglo for the global/local oddball analysis on DANDI:000253
```

## 3 · Containers / reproducible environments

| Option | What | Notes |
|---|---|---|
| **AIND ephys pipeline** | full Neuropixels Nextflow pipeline (dispatch→preprocess→sort→curate→QC→NWB), wraps SpikeInterface | [repo](https://github.com/AllenNeuralDynamics/aind-ephys-pipeline), [docs](https://aind-ephys-pipeline.readthedocs.io); local or SLURM configs. Code Ocean instance is private. |
| **AIND Docker images (GHCR)** | per-stage images | e.g. `ghcr.io/allenneuraldynamics/aind-ephys-spikesort-kilosort25-full:latest` (run `--gpus all --shm-size 8G`) — **Kilosort on sm_121 is the likely GB10 blocker** |
| **DANDI Hub image** | the JupyterHub NWB env | `docker pull dandiarchive/dandihub` |
| **OpenScope Databook** | ships a Dockerfile (ubuntu:22.04) | no published image — build locally; `uv.lock` is the most relevant reproducible env |
| **Apptainer / Singularity** | AIND supports it | via `pull_pipeline_images.sh` (converts the GHCR images). **Neurodesk** is Apptainer-based and bundles MNE/FieldTrip/EEGLAB — but **not** PyNWB/DANDI/SpikeInterface (it's the human-EEG/MRI side). |
| **Generic NGC PyTorch** (`nvcr.io/nvidia/pytorch:26.04-py3`) | the mouse NWB stack runs fine here | `pip install pynwb dandi h5py remfile` — pure-Python/manylinux, no CUDA. Smoke-test before committing. |

See [`env/`](../env) for a ready conda env, `requirements.txt`, and a Dockerfile/Apptainer recipe
in this repo.

## 4 · EEG-ready tooling (the cross-species bridge)

Build the mouse analysis on primitives that have a direct human-EEG twin, so the human data drops
into the same machinery later.

| Tool | Purpose | Install |
|---|---|---|
| **MNE-Python** (1.12.x) | **the bridge** — ERP (MMN = deviant−standard), `tfr_morlet`/`tfr_multitaper` time-frequency in the same theta/alpha-beta/gamma bands you run on mouse LFP | `pip install "mne[full]"` · <https://mne.tools> |
| **DCM for ERP (SPM)** (25.01, MATLAB) | generative predictive-coding model of ERPs (canonical microcircuit; ascending PE / descending predictions) — models MMN as synaptic-gain changes | <https://github.com/spm/spm> |
| **TAPAS / HGF** (MATLAB) | Hierarchical Gaussian Filter → trial-by-trial precision-weighted PE & volatility regressors for single-trial EEG | <https://github.com/translationalneuromodeling/tapas> |
| **pyhgf** (0.3.x, Python/JAX) | JAX port of the HGF (JIT, differentiable) | `pip install pyhgf` · [docs](https://computationalpsychiatry.github.io/pyhgf/) |
| **mTRFpy / naplib-python / mTRF-Toolbox** | temporal response functions for naturalistic/surprisal EEG | `pip install mtrf` · `pip install naplib` · [MATLAB ref](https://github.com/mickcrosse/mTRF-Toolbox) |

## Suggested first moves

1. **Stream before you pull.** 680 GB is large — start on **DANDI Hub** or stream with `remfile` +
   Neurosift to scope the NWB layout before committing local disk.
2. **Notebooks as templates.** Clone the **OpenScope Databook** for ready LFP/CSD/unit-QC code;
   adapt its stimulus-aligned unit-response notebook into an oddball PSTH; port `epych`'s
   FOOOF + band + CSD analyses.
3. **Same primitives on the EEG side.** Mirror the band/TF analysis in **MNE-Python** and the
   deviance response as MMN difference waves; add **pyhgf** trial-by-trial PE regressors and
   **DCM-ERP** as the mechanistic model. → [`05-cross-species-analysis.md`](05-cross-species-analysis.md)

## Caveats / verify-at-install

- `remfile` latest seen 0.1.13 (2024-05) — confirm at install.
- AllenSDK is stale (2023, ≤Py3.11) — pin the env; not the loader for 000253.
- pynwb-in-NGC and AIND-sorting-on-sm_121 are inferences — run a local smoke test.
- 000253's concrete S3 path isn't on the project's public data page — resolve via the DANDI asset API.
