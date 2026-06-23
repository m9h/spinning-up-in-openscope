# 06 · A Mouse Neuropixels Foundation Model from OpenScope

The unoccupied niche, the data, and the build plan. Scaffold:
[`brainsets_pipelines/allen_openscope_neuropixels/`](../brainsets_pipelines/allen_openscope_neuropixels/)
+ [`harness/poyo_openscope.py`](../harness/poyo_openscope.py).

## The gap

| | Spiking / ephys | Calcium / 2P |
|---|---|---|
| Primate motor/BCI | POYO-1, NDT3 | — |
| Mouse decision task | NEDS (IBL) | — |
| **Mouse passive visual cortex** | **← empty (this project)** | **OmniMouse** |

**OmniMouse** ([ICLR 2026, arXiv:2604.18827](https://arxiv.org/abs/2604.18827)) is the
Sensorium/Sinz **two-photon** model (3.1M neurons, 73 mice, 323 sessions, 150B tokens; a
"token" = strided 1D-conv over a calcium trace). It is the **calcium counterpart** of what
we build — not a substitute, because it's a different modality. The spiking + passive-
sensory + OpenScope cell is open.

## The data is there (verified DANDI counts, 2026-06-23)

OpenScope mouse ecephys: **94 mice / 487 sessions / ~2.5 TB** (000253, 001637, 000248,
000563, 000690, 001191). That alone exceeds **POYO-1** (7 animals / 158 sessions). Pool with
**Visual Coding** (~58 mice) + **Visual Behavior** (81 mice / 153 sessions) → **~230 mice /
~690 sessions**, comparable-to-larger than **NEDS** (83 mice). Full per-dandiset table in the
[pipeline README](../brainsets_pipelines/allen_openscope_neuropixels/README.md).

## The one OmniMouse result that sets the strategy

**Data-limited, not model-limited** — performance saturates beyond ~80M params but climbs
monotonically with data. So:
- Build a **modest (~50–80M) model**; spend effort on **data scale + diversity**, not params.
- That's **GB10-friendly**: an 80M model fine-tunes/evals on one GB10 (120 GB unified); the
  constraint is data throughput (stream from T9), not FLOPs.
- Open question worth publishing: **does the data-limited law hold for spikes too?** Our
  scaling curves answer it.

## Architecture (POYO + the CCF differentiator)

1. **Per-spike tokenization** — `Tᵢ = {Δtᵢ, posᵢ, unit_idᵢ}`, RoPE on Δt. (Keep POYO's
   sparse-event token; do **not** copy OmniMouse's dense-trace conv tokenizer.)
2. **Spatial unit embedding** — `posᵢ` = the unit's **CCFv3 (x,y,z)+region** (extracted by
   the brainset). MLP over CCF → a unit identity that **generalizes to unseen sessions**.
   Use it **residual with** a learnable unit embedding (spatial alone loses tuning identity).
3. **PerceiverIO** cross-attention bottleneck (O(N) over the spike stream) → latent
   self-attention → query-based cross-attention decoder. Same backbone as POYO/OmniMouse.
4. **Multimodal masking** (NEDS/OmniMouse recipe) — jointly model spikes + **stimulus**
   (video/grating via a small CNN/ViT) + **behavior** (running, pupil). Mask any subset,
   reconstruct the rest → one model does encoding, decoding, and forecasting.

## Objectives & readouts

- **Pretrain (SSL):** masked spike prediction + cross-modal masking. This is the right
  objective because OpenScope is mostly passive (no behavior label to supervise on).
- **Readout heads:** running speed (continuous, R²); **stimulus / deviant-vs-standard /
  local-vs-global** (the predictive-processing target); cell-type / region (zero-shot probe).

## Evaluation = holdouts + scaling curves

Four orthogonal splits:
1. held-out **sessions** (few-shot transfer — POYO's headline);
2. held-out **animals** (subject-level, no leakage);
3. held-out **paradigm** — keep all of 000253 global/local out of pretraining, fine-tune on
   it ("does the FM help on a *new* predictive-processing experiment");
4. within-session **temporal** holdout (the brainset's `train/valid/test_domain`).

Because the regime is data-limited, the **headline metric is a data-efficiency curve**
(fine-tuned-FM vs from-scratch as #sessions varies) — repoint your existing
`dataeff/poyo_area2_dataeff.py`.

## Why 001838 (macaque) is **not** in the pool

It's a different species, and CCFv3 is the **Allen *mouse*** atlas — macaque isn't in it, so
the spatial embedding can't transfer. Its only valid role is a **held-out cross-species
transfer eval**: does a mouse-pretrained model carry to macaque on the *identical* global/
local paradigm, through the learnable-unit-embedding path alone? That's an eval target, not
pretraining. (Mouse 000253 + macaque 001838 + the human local-global literature is the
cross-species axis from [`docs/05`](05-cross-species-analysis.md).)

## Compute & sequencing

- **Pretrain** on Modal / multi-GPU (your `modal_*.py`, `sbatch_poyo.sh`); **fine-tune + eval**
  on GB10. Don't re-sort spikes (Allen/IBL ship sorted units; Kilosort4 hits the sm_121 wall).
- **Reproduction-first:** settle the unmodified-POYO weight-collapse issue before scaling, or
  you debug data-packaging and the collapse bug at once.

## What's scaffolded here vs. what you wire in your harness
- **Here:** the brainset (`pipeline.py` emits spikes + CCF + running + stimulus; splits) and
  the readout config (`harness/poyo_openscope.py`).
- **In your harness:** the CCF spatial-embedding swap (torch_brain unit tokenizer), the
  multimodal masking heads, and `TRAIN_RECORDING_IDS` / holdout manifests.
