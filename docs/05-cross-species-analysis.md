# 05 · Combined Mouse ↔ Human Analyses

What can you actually *do* with the mouse data in hand (DANDI:000253) that prepares for — and later
combines with — the human EEG? The strategy is to compute the **same contrasts on the same
primitives** in both species, so the human data drops into machinery you've already validated on
mouse.

## The shared computational vocabulary

| Construct | Mouse (Neuropixels LFP/spikes) | Human (scalp EEG) | Tool both sides |
|---|---|---|---|
| **Deviance response** | deviant−standard PSTH / evoked LFP | **MMN** difference wave (deviant−standard) | MNE `Evoked`; PSTH on mouse |
| **Global vs local surprise** | `xxxX` vs `xxxY` contrast (already in 000253) | local-global MMN + **P3b** to global deviants | same epoching logic |
| **Predictive routing** | **gamma↑ / alpha-beta↓** for unpredictable (eLife paper) | gamma↑ / alpha-beta↓ over sensory cortex | Morlet/multitaper TFR in matched bands |
| **Omission response** | response to a blank where a stimulus was predicted | omission ERP / "missing stimulus" potential | evoked to silent-deviant trials |
| **Temporal expectation** | duration/jitter-block effects | "when"-prediction ERP/gain effects | block contrasts; entrainment metrics |
| **Trial-by-trial PE** | model-derived PE vs firing/LFP | PE-modulated single-trial EEG amplitude | **pyhgf / HGF** regressors |
| **Laminar / hierarchy** | CSD; granular→supra/infra timing | scalp can't resolve layers → **DCM-ERP** infers laminar connectivity | Elephant CSD (mouse); DCM (human) |

## Analyses you can run now (mouse only, EEG-ready)

1. **Reproduce the predictive-routing signature** on 000253 with `epych` (FOOOF + theta/alpha-beta/
   gamma + CSD). Output: per-area, per-band deviant−standard time-frequency maps. → these are the
   exact maps you'll later compute in MNE on human EEG.
2. **Local vs global dissociation.** Compute `xxxX` (global) vs `xxxY` (local) PSTH/LFP contrasts.
   The mouse result (deviance in spiking is largely *local*; global signatures show in
   field/neuroimaging) is itself a cross-species prediction to test in human EEG (Gabhart/Xiong/
   Bastos 2025, TiCS).
3. **Omission decoding.** Build the omission-trial evoked response in mouse; this is the cleanest
   "pure prediction error" and the most portable to a human omission paradigm.
4. **Define a fixed analysis spec** — bands, windows, baseline, cluster-permutation settings — as
   a small config used by *both* a mouse script and an MNE script. This is the single most useful
   prep artifact: it forces the human protocol's epoching to match the mouse from day one.

## Analyses that become possible once human EEG arrives

- **Matched-contrast cross-species comparison.** Same deviant−standard, same bands, same stats →
  qualitative homology of MMN/predictive-routing across species. (Cappotto/Auksztulewicz 2021 is
  the template for a *formally* matched cross-species decoding analysis.)
- **Generative-model bridge.** Fit **DCM-ERP** to the human MMN to infer laminar
  ascending-PE/descending-prediction connectivity, and compare those inferred laminar dynamics to
  the **directly measured** mouse CSD/laminar timing. Mouse provides the ground truth the human
  DCM can only infer — the core scientific payoff of pairing the two.
- **Shared latent model.** Fit one HGF/pyhgf belief-updating model to both species' trial
  sequences; use its precision-weighted PE/volatility regressors to predict mouse firing **and**
  human single-trial EEG — a common currency across species.
- **Representational comparison.** Decoding/RSA on mouse population activity vs human EEG
  sensor/source patterns for the same stimulus structure.

## What mouse adds that human EEG can't, and vice-versa

- **Mouse only:** cell-type-specific E/I (Sst/Vip/PV opto-tagging), laminar CSD, dendritic
  computation (SLAP2), single-unit prediction errors. → mechanism.
- **Human only:** behavior/report, conscious-access measures (P3b), language/music structure,
  whole-brain hierarchy, clinical translation. → relevance.
- **The pairing** lets you anchor a human scalp signature (e.g. MMN, gamma/alpha-beta routing) to a
  specific circuit mechanism measured directly in mouse — which is exactly the program
  arXiv:2504.09614 sets up.

## Practical next step

Stand up the mouse pipeline ([`03`](03-analysis-pipelines.md)) and the MNE skeleton in the same
repo/env, sharing one analysis-spec config. When the human EEG lands, you change only the data
reader, not the analysis. See [`notebooks/00_stream_and_explore_nwb.ipynb`](../notebooks/00_stream_and_explore_nwb.ipynb)
for the mouse entry point.
