# allen_openscope_neuropixels (brainset)

Ingests **OpenScope mouse Neuropixels** sessions (NWB on DANDI) into the
`temporaldata`/`torch_brain` format, so the OpenScope ecephys pool can train a **spiking**
foundation model — the Neuropixels counterpart of OmniMouse (which is two-photon).

## Why it's not just a primate pipeline with a swapped dandiset
The primate brainsets lean on POYO's **learnable per-session unit embeddings** (re-learned
for every session → weak zero-shot). This pipeline additionally extracts each unit's
**Allen CCFv3 coordinate (x,y,z µm) + region** from the NWB electrode table and attaches it
to `units` (`ccf_x/ccf_y/ccf_z/region`). A model can then build a **spatial unit embedding**
(MLP over CCF), so units in an unseen session get an identity for free → real zero-shot
transfer. Use it **with** (residual to) a learnable unit embedding, not instead of it.

## The pool (mouse ecephys, verified via DANDI API 2026-06-23)

| DANDI | project | mice | files | size |
|---|---|---|---|---|
| 000253 | Global/Local Oddball | 14 | 98 | 680 GB |
| 001637 | Predictive-Processing Community – Ecephys | 15 | 47 | 576 GB |
| 000248 | Illusion | 12 | 78 | 186 GB |
| 000563 | Barcoding | 14 | 94 | 200 GB |
| 000690 | Vision2Hippocampus | 25 | 156 | 600 GB |
| 001191 | Loop | 14 | 14 | 233 GB |
| **total** | | **94** | **487** | **~2.5 TB** |

Pool with the broader Allen mouse Neuropixels corpus (Visual Coding ~58 mice, Visual
Behavior 81 mice/153 sessions) for ~230 mice / ~690 sessions.

> **Not in the pool:** DANDI **001838** (Global/Local Oddball — *macaque*). It's a different
> species and, critically, **not in CCFv3** (macaque uses a different atlas), so the spatial
> embedding doesn't even apply. Its role is a **held-out cross-species transfer eval** (does
> a mouse-pretrained model carry to macaque on the *identical* paradigm, via the learnable
> unit-embedding path only) — never pretraining.

## Run

```bash
# one dandiset at a time (id selects the project); repeat across the pool
brainsets prepare ./brainsets_pipelines/allen_openscope_neuropixels --local \
    --raw-dir ./data/raw --processed-dir ./data/processed --dandiset 000253
```

## What each processed `.h5` contains
- `spikes` — `IrregularTimeSeries` (timestamps + unit_index), sorted
- `units` — `ArrayDict` with `ccf_x/ccf_y/ccf_z`, `region`, QC (`firing_rate/snr/isi_violations/quality`)
- `running` — `RegularTimeSeries` `speed` (cm/s, resampled; the continuous readout target)
- `stimulus` — `Interval` of all `*presentations` tables (orientation/contrast/TF/SF/phase/name)
- `train_domain/valid_domain/test_domain` — temporal 80/10/10 (per-session decoding eval)

## Validation checklist (per dandiset — column names drift)
- [ ] `units` has `peak_channel_id` (else map via `peak_channel`)
- [ ] `electrodes` has finite `x,y,z` (CCF) — unregistered probes → NaN coords
- [ ] `processing['running']` interface name (`running_speed` vs `speed`)
- [ ] which `*presentations` tables hold the oddball; derive `is_deviant`/`local`/`global`
      from `stimulus_name`/`orientation` per paradigm
- [ ] confirm a `RecordingTech` Neuropixels/multi-electrode member in your taxonomy version

Validated against `sub-621890_ses-1186358749` of DANDI:000253 (streamed 2026-06-23).
