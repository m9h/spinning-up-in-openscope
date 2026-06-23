# 04 · Human EEG Plans & Matching Papers

## The honest status

There is **no published "human EEG arm" of OpenScope** and **no registered human protocol
templated on the mouse stimulus set** that we could find. The consortium paper (arXiv:2504.09614)
and the project documentation describe a **mouse + primate** effort.

What *does* exist — and what makes a human EEG study tractable to design — is the substantial prior
human EEG/MEG work by three of the co-authors, which already uses the **same paradigm families**
(oddball, roving/sequence, omission, temporal jitter, sensorimotor mismatch) and in several cases
is explicitly **cross-species**. These are the citable analogues to build a matched human protocol
from.

---

## Ryszard Auksztulewicz

**Maastricht University — Prediction and Memory Lab (PredLab, <https://www.pred-lab.com>)**, with
members in Maastricht and FU Berlin. Combines EEG/MEG/iEEG with **DCM** computational modeling.
Authoritative current list: <https://www.pred-lab.com/publications>.

| Paper | Year / venue | Maps to mouse paradigm |
|---|---|---|
| **Decoding the content of auditory sensory memory across species** ([Cereb Cortex 31(7):3226](https://academic.oup.com/cercor/article/31/7/3226/6148916)) — Cappotto, Auksztulewicz, … Schnupp | 2021 | ⭐ **Explicit cross-species design** — matched memory-decoding across humans + animals. Closest methodological template for OpenScope's cross-species goal. |
| **Not all predictions are equal: "what" and "when" predictions modulate auditory cortex via different mechanisms** ([J Neurosci 38(40):8680](https://www.jneurosci.org/content/38/40/8680)) | 2018 | Human iEEG dissociating **temporal ("when")** vs identity ("what") prediction → the **temporal/duration + jitter** paradigm. |
| **Temporal prediction elicits rhythmic pre-activation of relevant sensory cortices** ([Eur J Neurosci](https://onlinelibrary.wiley.com/doi/full/10.1111/ejn.15405); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9545120/)) — Barne, Cravo, Auksztulewicz | 2022 | Human MEG, rhythmic temporal expectation → **temporal/jitter**. |
| **Rhythmic temporal expectation boosts neural activity by increasing neural gain** ([J Neurosci 39(49):9806](https://www.jneurosci.org/content/39/49/9806)) | 2019 | Human MEG; temporal-prediction gain → **jitter**. |
| **Attentional enhancement of auditory mismatch responses: a DCM/MEG study** ([Cereb Cortex 25(11):4273](https://academic.oup.com/cercor/article/25/11/4273/2366858)) | 2015 | Human MEG **MMN** + attention → **oddball × attention/prediction**. |
| **The cumulative effects of predictability on synaptic gain in the auditory processing stream** ([J Neurosci 37(28):6751](https://www.jneurosci.org/content/37/28/6751)) | 2017 | Human MEG → **sequence-learning / roving**. |
| **Top-down prediction signals from mPFC govern auditory cortex prediction errors** ([Cell Reports](https://www.cell.com/cell-reports/fulltext/S2211-1247(25)00309-2)) | 2025 | Rodent — the animal bridge from his lab; pair with the human MEG rows above. |

---

## Krzysztof Basiński

**Medical University of Gdańsk** — Quality of Life Research + Auditory Neuroscience Lab. Human EEG,
auditory/music perception, temporal prediction.

| Paper | Year / venue | Maps to mouse paradigm |
|---|---|---|
| **Inharmonicity enhances brain signals of attentional capture and auditory stream segregation** ([Commun Biol](https://www.nature.com/articles/s42003-025-08999-5); [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.04.17.649377v1)) | 2025 | ⭐ **Roving oddball + jitter** — a **jitter manipulation** (constant vs randomized) gates MMN/P3a. Direct human analogue of the mouse **temporal-jitter** + oddball template. |
| **Non-linear relationships between auditory mismatch responses and the inharmonicity of complex sounds** ([Sci Rep](https://www.nature.com/articles/s41598-026-41129-7); [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.14.676123v2)) | 2026 | Human EEG oddball; parametric deviance → graded **oddball/deviant** processing. |
| **Enhanced mismatch negativity in harmonic compared with inharmonic sounds** ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9543822/)) — Quiroga-Martinez, Basiński | 2022 | Human EEG multi-feature **oddball** (MMN/P3a). Direct oddball analogue. |
| **Temporal hierarchies in the predictive processing of melody — from pure tones to songs** (Neurosci Biobehav Rev) | 2023 | Review of temporal prediction across timescales → **sequence/temporal** bridge. |

---

## André M. Bastos

**Vanderbilt University — Bastos Lab.** Local-global oddball, **predictive routing** (alpha/beta
vs gamma laminar dynamics), macaque + human iEEG/EEG, **and the mouse OpenScope visual-oddball
data (DANDI:000253)**.

| Paper | Year / venue | Role |
|---|---|---|
| **Predictive coding: a more cognitive process than we thought?** ([Trends Cogn Sci](https://www.cell.com/trends/cognitive-sciences/abstract/S1364-6613(25)00030-0); [lab PDF](https://bastoslab.squarespace.com/s/Manuscript.pdf)) — Gabhart, Xiong, Bastos | 2025 | ⭐ **Explicit cross-species synthesis** of local-global oddball across **mouse (OpenScope), macaque, and human neuroimaging**. The paper tying his human/macaque work to the OpenScope mouse data. |
| **Layer and rhythm specificity for predictive routing** ([PNAS 117(49)](https://www.pnas.org/doi/10.1073/pnas.2014868117)) | 2020 | Macaque laminar local-global; alpha/beta-suppression vs gamma-increase **predictive-routing** signature. Foundational for the laminar question. |
| **Propofol-mediated loss of consciousness disrupts predictive routing** ([PNAS 121](https://www.pnas.org/doi/10.1073/pnas.2315160121)) | 2024 | Macaque oddball + predictive routing under anesthesia. |
| **Ubiquitous predictive processing in the spectral domain of sensory cortex** ([eLife](https://elifesciences.org/reviewed-preprints/109053); [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.07.31.667946v1)) | 2025 | **The analysis of DANDI:000253** — spectral alpha/beta vs gamma. Code: [`BastosLab/epych`](https://github.com/BastosLab/epych). |

Bastos's species-matched contributions are **macaque + the mouse OpenScope data**, synthesized
against the human MMN/oddball literature in the 2025 TiCS review (rather than a standalone human
EEG oddball dataset of his own).

---

## Sensorimotor (motor/closed-loop) — a human noninvasive analogue

Not by these three authors, but the human counterpart to the mouse **closed-loop visuomotor
mismatch** paradigm:

- **Visuomotor mismatch EEG responses in occipital cortex of freely moving human subjects**
  ([bioRxiv 2025.08.14.670295](https://www.biorxiv.org/content/10.1101/2025.08.14.670295)), 2025.

---

## So, what would the human EEG version look like?

Reading the authors' existing paradigms back onto the mouse battery, the natural matched human
protocol (most likely **auditory**, given Auksztulewicz & Basiński) would be:

1. **Local/global auditory oddball** — direct analogue of DANDI:000253 and the Bekinschtein–Dehaene
   design; the cleanest cross-species bridge.
2. **Roving oddball + temporal jitter** — Basiński 2025 (Commun Biol) is essentially this already;
   matches mouse "standard oddball jitter random" + temporal-mismatch paradigms.
3. **"When"/temporal-expectation block** — Auksztulewicz 2018/2019; matches the duration-mismatch
   paradigm.
4. **Omission responses** — silent-deviant trials → matches the mouse omission (blank) deviant;
   "pure" prediction error with no bottom-up drive.
5. **Sensorimotor mismatch** — harder noninvasively, but the freely-moving visuomotor-mismatch EEG
   above shows it is feasible.

The analysis-side payoff is that these human ERP/time-frequency contrasts (MMN, P3a/P3b, alpha/beta
suppression, gamma increase, omission response) line up with exactly the contrasts Bastos's `epych`
pipeline computes on the mouse LFP — see [`05-cross-species-analysis.md`](05-cross-species-analysis.md).
