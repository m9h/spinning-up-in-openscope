# Scope — CCF registration for the OpenScope community ecephys sessions

**Question asked:** register the ~60 community Neuropixels sessions (DANDI **001191** "Loop" +
un-registered **001637** "PredProc-Ecephys") to Allen CCFv3 so they join the spatial-embedding
pretraining pool (per-unit `ccf_x/ccf_y/ccf_z` + region — the differentiator vs POYO's learnable
unit embeddings; see `brainsets_pipelines/allen_openscope_neuropixels/README.md`).

**Status:** scoping only — no registration run yet. Verified against the real NWBs on T9 +
a 6-agent tooling/upstream research sweep (2026-06-29).

---

## TL;DR — the "60 sessions" is really 46, and the primary path is *pull/await upstream*, not recompute

Two premise corrections from reading the actual files (not the catalog):

1. **001191 is already fully CCF-registered — in millimetres.** All **14/14** sessions carry real
   electrode `x/y/z` (~0–11 mm) + 47–61 anatomical regions; region centroids are anatomically
   tight and correctly ordered (CA3 ventral to CA1, APN in midbrain). Earlier tooling rejected
   them because a `≥100 µm` magnitude guard mis-read mm-scale CCF as "degenerate placeholders."
   **Fix = a unit-scale change in our extractor, not registration.** (Already fixed in
   `census_pool_ccf.py`; still TODO in the SpikeLab adapter `openscope_nwb.py`.)

2. **001637 is per-session heterogeneous: 2/48 already registered (µm), 46 pending.** The 2 done
   (`sub-820459` 2025-11-10, `sub-830795` 2026-02-26) went through AIND's live CCF pipeline; the
   other 46 have units but no electrode CCF (`location='unknown'`, no x/y/z).

So the genuine registration target is **46 sessions (001637 only)**. With the mm fix, the FM-ready
pool goes **92 → 106 / 153** before any registration work. `units.estimated_x/y/z` are **probe-space**
(spike-localization; `estimated_y` ≡ `units.depth`) — they do **not** provide CCF for the 46.

---

## The data picture (verified on real NWBs)

| set | sessions | electrode CCF | units | takeaway |
|---|---|---|---|---|
| 000253 / 000248 / 000563 | 14 / 12 / 14 | µm, uniform | yes | already in pool |
| 000690 | 51 | µm (50/51; one session has 0 units) | yes | already in pool |
| **001191 "Loop"** | **14** | **mm, 14/14** | yes | **free** — rescale mm→µm |
| **001637 "PredProc"** | **48** | µm on **2**; none on **46** | yes | **register the 46** |

- All are **AIND** data (`institution: Allen Institute for Neural Dynamics`,
  `session_id: ecephys_<subj>_<date>`). 001191 came through an **older** Allen/Loop export (mm,
  not on `aind-open-data`); 001637 through the **current** AIND Code Ocean pipeline (µm).
- **001637 un-registered NWBs contain only on-probe geometry** (`rel_x/rel_y`) — **no insertion
  anchor / angles / depth**, no `location`. That metadata gap is the crux for any recompute.

---

## Why "pull/await upstream" is the primary path for the 46

AIND's per-channel CCF is histology-based and is a **separate downstream step from spike sorting**:
`ephys_probe_tracking` (YoloV11 probe-track detection in SmartSPIM lightsheet) → per-probe CSV
(`channel_id, structure_acronym, structure_id, x/y/z_coord, …`, IBL-bregma→CCF µm) →
`nwb-ccf-packaging` appends to the electrodes table. Research findings:

- **No CCF asset to download today.** `s3://aind-open-data` has 001637 SmartSPIM histology but only
  **stitched, not CCF-registered**; no `*ccf*`/probe-track derivatives. 001191 isn't on the bucket.
- **But the histology exists and the pipeline is active** — which is exactly why 2/48 sessions are
  already done. CCF for the other 46 is **computable upstream at <100 µm** (histology-grade), in the
  **exact schema we want**, with **zero modeling risk** — strictly better than any no-histology
  estimate we'd compute ourselves.

**→ Recommended:** monitor `s3://aind-open-data` for `nwb-ccf-packaging` output on the 001637
subjects and **contact AIND** (Carter Peene, rcpeene@gmail.com) to ask the timeline / request the
per-probe CCF CSVs. This likely lands the 46 for free. *(001191 has no upstream histology — but it's
already registered, so it needs nothing.)*

---

## Fallback — headless recompute (only if we won't wait)

If the 46 are needed before AIND finishes:

1. **Recover the insertion trajectory** (anchor + 2 angles + depth) per probe. **Not in the NWB** —
   look in the AIND `session.json` / `procedures.json` on S3 (`aind-data-schema` can carry
   manipulator + targeted-CCF coordinates). **This is the gating prerequisite — check it first.**
2. **Compute per-channel CCF headlessly** with **IBL `EphysAlignment`** (`pip install iblatlas
   ibllib`, MIT, pure numpy, batchable on Slurm): synthesize `xyz_picks` from the insertion via
   `iblatlas …Insertion.from_dict({x,y,z,phi,theta,depth})`, feed `chn_depths` from `rel_y`, run the
   identity (geometry-only) alignment → per-channel CCF µm + Allen acronym **in the same bregma→CCF
   convention AIND uses** (matches the 2 registered sessions byte-for-byte). Region lookup via
   `brainglobe-atlasapi.structure_from_coords` (BSD-3, modern deps, headless) or `iblatlas`.
   Pre-cache the 25 µm atlas on the node (one-time network).
   - Optional precision: snap region boundaries to per-channel LFP/firing features (the IBL
     interactive step) — but that needs the GUI; skip for batch.
3. **If insertion coordinates are entirely unavailable**, drop to **ephys-feature region prediction**
   (IBL ephys-atlas / Hengen eLife 101506) — **region only, ~65–89%, no precise xyz.** Coarse;
   usable as a learnable-embedding token, not as the spatial differentiator.

**Accuracy:** no-histology trajectory ≈ **200–400 µm**, growing with depth (~7.5° angle error);
histology <100 µm. Tooling that's GUI-bound and *not* batchable (Pinpoint, NTE, SHARP-Track) is
useful only to visually QC a few probes.

**Within-subject propagation:** valid **only for chronic implants** (fixed probe across days).
001637 subjects have 2–4 sessions each — but AIND assigns CCF **per subject** (one brain → all that
subject's sessions at once), so propagation isn't a separate task; chronic-vs-acute was not
confirmed. Don't hand-copy one session's CCF to siblings without verifying the implant type.

---

## Recommended plan (phased)

- **Phase 0 — reclaim 001191 (free, ~½ day).** Apply the mm→µm rescale in the SpikeLab adapter
  `openscope_nwb.py` (done in `census_pool_ccf.py`); detect unit by magnitude, store µm. Re-census.
  Pool 92 → **106/153**. *No registration involved.*
- **Phase 1 — chase upstream for the 46 (low effort, high payoff).** Check S3 for new
  `nwb-ccf-packaging` output; email AIND for timeline / the per-probe CSVs. Build a tiny
  CSV→electrodes joiner keyed on `channel_id` (mirrors `nwb-ccf-packaging`) for whatever they share.
- **Phase 2 — recompute ONLY if Phase 1 stalls.** First verify insertion metadata exists in
  `session.json` on S3 (gating). If yes → IBL `EphysAlignment` headless batch over 46×~6 probes →
  write `ccf_x/y/z + region` into the pipeline's `units`. If no insertion metadata → ephys-feature
  region-only labels (coarse) + learnable-embedding path.
- **Don't block the FM.** The 46 can pretrain **now** via the learnable unit-embedding path; fold in
  CCF when Phase 1/2 lands. Per-session CCF gating already exists (`census_pool_ccf.py`).

## Acceptance criteria
- 001191 reclassified as registered (mm→µm) across all 14; pool count corrected to 106/153.
- A documented answer on upstream availability (S3 re-check + AIND contact outcome).
- For any recomputed session: per-channel CCF µm in the AIND bregma→CCF convention, validated
  against a registered reference (`sub-830795`) on overlapping anatomy, region labels via CCFv3
  annotation volume; flagged as `ccf_source=recomputed` (vs `histology`) so the FM can weight it.

## Effort / risk
- Phase 0: trivial, no risk (data already correct; tooling fix).
- Phase 1: low effort; risk = AIND timeline outside our control.
- Phase 2: moderate (IBL stack + atlas caching + transform validation); risk = **missing insertion
  metadata** (then only coarse labels) and ~200–400 µm error vs the µm-grade pool — acceptable as a
  residual-to-learnable embedding, weaker as the zero-shot differentiator.

## Open actions
- [ ] Apply mm→µm fix in SpikeLab `openscope_nwb.py`; re-run pool census (Phase 0).
- [ ] `aws s3 ls --no-sign-request s3://aind-open-data/` for new 001637 `*ccf*`/probe-track assets.
- [ ] Pull one 001637 `session.json`/`procedures.json` from S3 — does it carry insertion coords?
- [ ] Email AIND (rcpeene@gmail.com): CCF timeline for 001637 subjects / share per-probe CSVs.
