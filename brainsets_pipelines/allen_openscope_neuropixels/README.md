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

## Validate before a real run

`validate_one_session.py` (one session) and `sweep_pool.py` (one session per pool dandiset)
exercise the extractors with plain numpy/pandas (no temporaldata/brainsets), so they run in
the spinning-up venv. They share parsing with the pipeline via `openscope_nwb.py`.

```bash
python brainsets_pipelines/allen_openscope_neuropixels/validate_one_session.py --dandiset 000253
python brainsets_pipelines/allen_openscope_neuropixels/sweep_pool.py     # whole pool
```

### Pool compatibility (swept 2026-06-23, one session each)

| DANDI | units | spikes | unit→elec link | CCF (distinct/unit) | running | status |
|---|---|---|---|---|---|---|
| 000253 | 2446 | 110.7M | peak_channel_id | 100% (897) | running | **READY** |
| 000248 | 3026 | 137.1M | peak_channel_id | 99% (1030) | running | **READY** |
| 000563 | 2299 | 121.6M | peak_channel_id | 100% (970) | running | **READY** |
| 000690 | 3091 | 81.2M | peak_channel_id | 100% (1086) | running | **READY** |
| 001191 | 3307 | 131.4M | electrodes_region | — (region-only) | running_new | needs CCF reg. |
| 001637 | 4247 | 94.6M | electrodes_region+extremum | — (no anat.) | running | mostly needs reg.† |

> **† 001637 is per-session heterogeneous (censused 2026-06-27).** A streaming metadata
> census of all 48 non-probe 001637 sessions found **2 fully CCF-registered** —
> `sub-820459` (2025-11-10) and `sub-830795` (2026-02-26): real `x/y/z` (0–9700 µm) +
> 48–61 anatomical regions — and **46 with no absolute `x/y/z` columns** (location absent).
> The single swept session above happened to be un-registered. **CCF readiness is a
> per-session property, not a per-dandiset one.** Live-validated both paths: the adapter
> extracts correct CCF when present (`sub-830795` → 2225 units, 549 distinct coords, 48
> regions, 36 032 stimulus onsets, running → **full READY PASS**) and degrades gracefully —
> no crash, NaN coords, region/none — when absent (real `001191`, 3307 units, all-NaN CCF).
> Caveat: on 001637 the oddball labeler (tuned for 000253's global/local paradigm) returns
> `none` for every row; the stimulus table itself is fully populated and alignable.

**Two conventions, three gotchas the sweep caught:**
- **unit→electrode link:** older sets use `peak_channel_id` (→ electrode id); newer community
  sets use the `units.electrodes` region — and the *peak* is `extremum_channel_index`, NOT the
  first row (first row = electrode 0 for every unit → all-same-coordinate bug).
- **running module:** `running` vs `running_new` (iface `running_speed` vs `running_speed_new`).
- **CCF registration gap (assess per session):** the two newest **community SpikeInterface**
  sets (**001191, 001637**) are *mostly* not Allen-CCF-registered, but — as the 001637 census
  above shows — registration is **sporadic at the session level**, so gate on it per session.
  001191's electrode `x/y/z` are degenerate placeholders (~0–10, rejected by a magnitude
  guard); un-registered 001637 sessions have **no absolute `x/y/z` columns** and `location`
  absent/`unknown` (probe-space coords only). A magnitude+distinctness guard cleanly separates
  the two cases. For un-registered sessions, run CCF registration to unlock the spatial
  embedding; until then use region as a coarse token or the learnable unit-embedding path only.

### Per-session CCF census (whole pool, 2026-06-27)

`census_pool_ccf.py` streams **only** electrode/units metadata (no spike download) for every
non-probe session and classifies each as **FM-ready** = has spike-sorted units AND absolute
Allen-CCFv3 electrode coords (magnitude+distinctness guard rejects 001191's ~0–10 placeholders).
This is the gate sweep_pool.py is too coarse for — registration is per session, not per dandiset.

| DANDI | sessions | CCF-registered | FM-ready (units + CCF) |
|---|---|---|---|
| 000253 | 14 | 14 | 14 |
| 000248 | 12 | 12 | 12 |
| 000563 | 14 | 14 | 14 |
| 000690 | 51 | 51 | **50** |
| 001191 | 14 | 0 | 0 |
| 001637 | 48 | 2 | 2 |
| **total** | **153** | **93** | **92** |

- **92 FM-ready sessions** (units + real CCF) — the CCFv3 spatial-embedding pretraining pool.
  The four Allen dandisets are uniformly registered; the two community sets are the gap.
- **000690 anomaly:** `sub-717438_ses-1334311030_ecephys.nwb` is CCF-registered but has **0
  units** (no `/units` group — spikes live in a sibling file) → correctly excluded from FM-ready.
- **001191 (0/14) + 001637 (46/48 un-registered) = 60 sessions** with units but no absolute CCF.
  Still trainable via the learnable unit-embedding path, or after CCF registration to join the
  spatial-embedding pool.

```bash
python census_pool_ccf.py                         # whole pool
python census_pool_ccf.py --dandiset 001637       # one dandiset
python census_pool_ccf.py --json census.json      # per-session report
```

### Checklist (per dandiset — structure & column names drift)
- [x] **session vs per-probe files:** units/running/stimulus are in the SESSION file
      (`*_ogen.nwb` for 000253); `*_probe-N_ecephys.nwb` are LFP-only → `get_manifest` skips them.
- [x] `units` has `peak_channel_id`; `electrodes` has finite `x,y,z` (CCF) + `location`.
- [x] running speed = `processing['running'].running_speed` — **has encoder artifacts**
      (000253: down to −746 cm/s); pipeline rejects `|v|>150 cm/s` as NaN.
- [ ] which `*presentations` tables hold the oddball; derive `is_deviant`/`local`/`global`
      from `stimulus_name`/`orientation` **per paradigm** (4 tables in 000253). The 000253
      heuristic does **not** transfer to 001637 (its stimulus rows all label `none`) — each
      paradigm needs its own deviant/standard mapping; the raw stimulus table is paradigm-agnostic.
- [ ] confirm a `RecordingTech` Neuropixels/multi-electrode member in your taxonomy version.

**Validated 2026-06-23** against `sub-621890_ses-1186358749_ogen.nwb` (DANDI:000253, streamed):
ALL CHECKS PASSED — 2446 units / 110.7M spikes / **CCF coords 100% finite** (VISl/VISpm/CA1/
thalamus) / running + 4 stimulus tables present.

**Re-validated 2026-06-27** on real un-/registered community sessions (downloaded to T9):
`001191` `sub-747825` (11 GB, 3307 units) → **graceful** no-crash, CCF all-NaN + region note;
`001637` `sub-830795` (10 GB, 2225 units) → **full READY PASS** (549 distinct CCF, 48 regions,
36 032 stimulus onsets, running). Confirms both branches of the adapter on real data, and
that 001637 is per-session heterogeneous (2/48 registered — see census note above).
