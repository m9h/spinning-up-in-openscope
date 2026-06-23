# Spinning Up in OpenScope

A getting-started guide for the **OpenScope Community Predictive-Processing** project: how to
download and analyze the openly available **mouse** data now, in preparation for the **human
noninvasive EEG** experiments being planned by Ryszard Auksztulewicz, Krzysztof Basiński, and
André Bastos to mirror the mouse paradigms.

> Named in the spirit of OpenAI's *Spinning Up in Deep RL* — an onboarding resource, not the
> primary project repo. The authoritative project lives at
> [AllenNeuralDynamics/openscope-community-predictive-processing](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing).

## What this is for

The consortium paper [*Neural mechanisms of predictive processing: a collaborative community
experiment through the OpenScope program*](https://arxiv.org/abs/2504.09614) (arXiv:2504.09614,
2025; 53 authors) lays out a battery of **mismatch / predictive-coding paradigms** recorded in
mouse cortex with Neuropixels, dendritic imaging (SLAP2), and mesoscope calcium imaging. The same
paradigm *families* (oddball, sequence/roving, omission, temporal jitter, sensorimotor mismatch)
have well-established **human EEG/MEG** analogues in the prior work of three of the co-authors.

This repo collects, in one place:

1. **What the project is** and what the mouse paradigms are. → [`docs/01-project-overview.md`](docs/01-project-overview.md)
2. **What mouse data is available now** and exactly how to pull it. → [`docs/02-mouse-data.md`](docs/02-mouse-data.md)
3. **Which pipelines / containers to install** to analyze it. → [`docs/03-analysis-pipelines.md`](docs/03-analysis-pipelines.md)
4. **The human-EEG plans & matching papers** by Auksztulewicz, Basiński, Bastos. → [`docs/04-human-eeg-plans.md`](docs/04-human-eeg-plans.md)
5. **What combined mouse↔human analyses** are feasible with data in hand. → [`docs/05-cross-species-analysis.md`](docs/05-cross-species-analysis.md)
6. **A mouse Neuropixels foundation model** from the OpenScope pool (the spiking counterpart of OmniMouse). → [`docs/06-mouse-ephys-foundation-model.md`](docs/06-mouse-ephys-foundation-model.md) · scaffold: [`brainsets_pipelines/allen_openscope_neuropixels/`](brainsets_pipelines/allen_openscope_neuropixels/)

## Quickstart

```bash
# 1. Environment (pick one). uv is the project default — fast, project-local .venv:
uv venv --python 3.12 .venv && uv pip install -r env/requirements.txt
source .venv/bin/activate
#   reproduce the exact verified set:  uv pip sync env/requirements.lock.txt
#   or conda:  conda env create -f env/environment.yml && conda activate openscope
#   or pip:    pip install -r env/requirements.txt
#   or docker: docker build -t spinning-up-openscope env/   (see env/Dockerfile)

# 2. Peek at the published mouse dataset WITHOUT downloading 680 GB (streaming)
python scripts/stream_first_nwb.py            # streams one session from DANDI:000253

# 3. Or grab a single session locally
bash scripts/download_dandi.sh 000253         # full set is ~680 GB — see the script for one-asset mode
```

> The `.venv` is verified working end-to-end (it streams a live 000253 session). Pins are
> snapshotted in [`env/requirements.lock.txt`](env/requirements.lock.txt). Python 3.12 here; the
> separate OpenScope Databook / AllenSDK tooling needs its own 3.10 env (see [`docs/03`](docs/03-analysis-pipelines.md)).

## The one-paragraph orientation

The published mouse dataset is **DANDI:000253** ("Allen Institute OpenScope – Global/Local
Oddball", ~680 GB, 98 NWB files, 14 mice, 6 visual areas). It implements the **local/global
oddball** — which is exactly the paradigm with the canonical human EEG/MEG analogue
(Bekinschtein–Dehaene local-global). Bastos's lab has already analyzed it (eLife reviewed
preprint *"Ubiquitous predictive processing in the spectral domain"*; analysis code at
[`BastosLab/epych`](https://github.com/BastosLab/epych)). The four *newer* community paradigms
(standard oddball, sensorimotor closed-loop, sequence, temporal/duration) are being collected and
will appear under the project's DANDI account. Start with 000253 + `epych` + the OpenScope
Databook, build an MNE-Python ERP/time-frequency pipeline that will transfer to the human EEG, and
you are "spun up."

## Status

| Piece | State |
|---|---|
| Mouse global/local oddball data (DANDI:000253) | **Published, downloadable now** |
| Four new community paradigms (mouse) | Being collected; watch the project DANDI account |
| Human EEG arm (matched protocol) | **Not yet a published OpenScope protocol** — see [`docs/04`](docs/04-human-eeg-plans.md) for the authors' existing matched paradigms |

See [`docs/REFERENCES.md`](docs/REFERENCES.md) for the full citation list.
