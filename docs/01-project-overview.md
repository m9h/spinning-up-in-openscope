# 01 · Project Overview

## The paper

**[Neural mechanisms of predictive processing: a collaborative community experiment through the
OpenScope program](https://arxiv.org/abs/2504.09614)** — arXiv:2504.09614 (2025). ~53 authors,
including **Ryszard Auksztulewicz, Krzysztof Basiński, and André M. Bastos**.

Core thesis: the brain continuously predicts sensory input and signals **prediction errors** when
inputs violate predictions. The paper proposes a coordinated, community-run battery of mismatch
experiments to dissect the circuit mechanisms — stimulus adaptation, dendritic computation,
excitatory/inhibitory (E/I) balance, top-down feedback, and hierarchical/laminar processing.

It is run through the **OpenScope** program at the Allen Institute for Neural Dynamics — a
"shared observatory" model where the community proposes experiments, the Allen Institute collects
standardized data, and the data is released openly as NWB on the DANDI Archive.

- Project site: <https://allenneuraldynamics.github.io/openscope-community-predictive-processing/>
- Project repo: <https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing>
- OpenScope program: <https://www.allenneuraldynamics.org/projects/openscope>

## The mouse paradigms

All four community paradigms use **visual drifting gratings** (this is a visual-cortex project),
which matters when designing the human analogues (see [`04`](04-human-eeg-plans.md)).

| # | Paradigm | Design | What it isolates |
|---|---|---|---|
| 1 | **Standard mismatch (oddball)** | Passive viewing, ~120:1 standard:deviant. Deviants = orientation change (45°→90°), motion **halt** (0 Hz), or **omission** (blank). | Adaptation vs. genuine deviance detection; omission = "pure" prediction-error with no bottom-up input. |
| 2 | **Sensorimotor mismatch (closed-loop)** | Mouse runs on a wheel; visual flow is **coupled** to running speed. Deviants = flow decoupled from, or mismatched to, locomotion. | Motor-based prediction (efference copy) and visuomotor prediction error. |
| 3 | **Sequence mismatch** | Habituation to a **4-stimulus sequence** repeating ~1×/s for ~37 min; deviant introduced at the **3rd position**. | Learned temporal/structural sequence prediction (roving-like). |
| 4 | **Temporal (duration) mismatch** | Blocks of 250 ms stimuli / 500 ms ISI vs. blocks with 150 ms or 350 ms durations. | "When" prediction / temporal expectation, independent of stimulus identity. |

Plus auxiliary protocols: a **"standard oddball jitter random"** (temporal-jitter control), a
generic/flexible oddball, and **gamma-calibration** runs.

### Recording modalities

- **Neuropixels** laminar probes (>380 channels): spikes + LFP, enabling **current-source-density
  (CSD)** and laminar feedforward/feedback analyses. Areas: **V1, LM, AL, M1, M2**.
- **SLAP2** — ultra-fast (~220 Hz) subcellular two-photon imaging of **dendritic** compartments.
- **Mesoscope** — multi-plane calcium imaging across visual areas.

### Genetics (cell-type access)

Excitatory: **Slc17a7-IRES2-Cre**. Inhibitory: **Sst-IRES-Cre**, **Vip-IRES-Cre**
(the published global/local dataset uses **SSTAi32** and **PVAi32** opto-tagging lines). This
cell-type resolution is what lets the project test E/I and interneuron-specific predictions that
are invisible to scalp EEG — and is therefore a key reason to pair mouse with human (see
[`05`](05-cross-species-analysis.md)).

## Why this maps cleanly onto human EEG

The paradigm families are **modality-portable**. An oddball, a roving/sequence violation, an
omission, a temporal-jitter manipulation, and a sensorimotor mismatch can all be implemented in a
human EEG session (often more naturally in **audition**, which is where Auksztulewicz and Basiński
work). The **global/local oddball** that the published mouse data already implements has the most
direct, decades-old human EEG/MEG analogue. That is the bridge this repo is built around.
