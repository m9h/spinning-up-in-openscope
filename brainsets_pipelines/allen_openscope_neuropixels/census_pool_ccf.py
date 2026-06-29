#!/usr/bin/env python
"""Per-session CCF + units census across the OpenScope ecephys pool.

Streams ONLY electrode/units *metadata* (no spike-data download) for every
non-probe NWB asset in each pool dandiset and classifies whether each session
is **FM-ready**: it has spike-sorted units AND absolute Allen-CCFv3 electrode
coordinates (not probe-space placeholders).

Why per session: CCF registration is a **per-session** property, not a
per-dandiset one. The 2026-06-27 001637 census found only 2/48 sessions
registered while the rest carry no absolute x/y/z — a one-session-per-dandiset
spot check (sweep_pool.py) is too coarse to gate FM pretraining. This tool
gives the true FM-ready session count.

Deps: numpy, h5py, remfile, dandi (same as sweep_pool.py's streaming path).
Reads only the electrodes table + units id length, so it is cheap per session.

Usage:
    python census_pool_ccf.py                       # whole pool
    python census_pool_ccf.py --dandiset 001637     # one dandiset
    python census_pool_ccf.py --json out.json       # also write a report
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np

POOL = ["000253", "000248", "000563", "000690", "001191", "001637"]

# A session counts as CCF-registered if its electrode x/y/z are real Allen
# anatomical coordinates -- which the pool ships in TWO unit conventions:
#   * micrometres (Allen/AIND nwb-ccf-packaging export; ~0-13200 um), and
#   * millimetres (the 001191 'Loop' export; ~0-13 mm).
# A degenerate placeholder (one constant value, or no anatomy) is rejected by
# requiring per-axis distinctness AND, for the mm branch, real `location`
# labels. NB: the 'um' magnitude floor (>=100) wrongly rejected mm-scale CCF
# in earlier versions -- 001191's ~0-10 values are real mm CCF, not noise.
CCF_MIN_MAX_UM = 100.0   # micrometre-scale CCF floor
CCF_MIN_MAX_MM = 1.0     # millimetre-scale CCF floor (with anatomy corroboration)
CCF_MIN_DISTINCT = 20    # per-axis distinct finite values
ELECTRODES_PATH = "/general/extracellular_ephys/electrodes"


def _n_real_locations(el):
    if "location" not in el.keys():
        return 0
    lv = np.unique(el["location"][:].astype(str))
    return len([s for s in lv if s.lower() not in ("unknown", "none", "")])


def classify_electrodes(el):
    """-> (registered: bool, detail: str, n_locations: int, unit: str|None)."""
    cols = set(el.keys())
    nloc = _n_real_locations(el)
    if not ({"x", "y", "z"} <= cols):
        return False, "no x/y/z cols", nloc, None
    X = [el[k][:] for k in ("x", "y", "z")]
    fin = np.isfinite(X[0]) & np.isfinite(X[1]) & np.isfinite(X[2])
    if not fin.any():
        return False, "xyz all-NaN", nloc, None
    mx = max(float(np.nanmax(np.abs(v[fin]))) for v in X)
    nd = min(int(len(np.unique(v[fin]))) for v in X)
    unit = None
    if nd >= CCF_MIN_DISTINCT:
        if mx >= CCF_MIN_MAX_UM:
            unit = "um"
        elif mx >= CCF_MIN_MAX_MM and nloc >= 5:  # mm CCF, anatomy-corroborated
            unit = "mm"
    reg = unit is not None
    return reg, f"max={mx:.4g} mindistinct={nd} unit={unit}", nloc, unit


def _n_units(f):
    for path in ("/units/id", "/units/spike_times_index"):
        try:
            return int(f[path].shape[0])
        except Exception:
            continue
    return 0


def census_dandiset(ds_id, rows):
    import remfile
    import h5py
    from dandi.dandiapi import DandiAPIClient

    c = DandiAPIClient()
    ds = c.get_dandiset(ds_id, "draft")
    assets = [a for a in ds.get_assets() if "probe-" not in a.path.lower()]
    assets.sort(key=lambda a: a.path)
    print(f"\n=== {ds_id}: {len(assets)} non-probe assets ===", flush=True)

    reg_n = ready_n = 0
    for a in assets:
        name = a.path.split("/")[-1]
        rec = {"dandiset": ds_id, "asset": name, "asset_id": a.identifier}
        try:
            url = a.get_content_url(follow_redirects=1, strip_query=True)
            rf = remfile.File(url)
            with h5py.File(rf, "r") as f:
                nu = _n_units(f)
                if ELECTRODES_PATH not in f:
                    reg, detail, nloc, unit = False, "no electrodes group", 0, None
                else:
                    reg, detail, nloc, unit = classify_electrodes(f[ELECTRODES_PATH])
            ready = bool(reg and nu > 0)
            reg_n += int(reg)
            ready_n += int(ready)
            rec.update(units=nu, registered=reg, fm_ready=ready,
                       detail=detail, n_locations=nloc, ccf_unit=unit)
            tag = "FM-READY  " if ready else ("reg/0units" if reg else "no-ccf    ")
            print(f"  {tag} | units={nu:5d} | loc={nloc:3d} | {detail:24s} | {name}",
                  flush=True)
        except Exception as e:
            rec.update(error=f"{type(e).__name__}: {e}")
            print(f"  ERR        | {type(e).__name__}: {e} | {name}", flush=True)
        rows.append(rec)
    print(f"  --> {ds_id}: {reg_n}/{len(assets)} CCF-registered, "
          f"{ready_n}/{len(assets)} FM-ready (units + CCF)", flush=True)
    return reg_n, ready_n, len(assets)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dandiset", default=None, help="one dandiset id (default: whole pool)")
    p.add_argument("--json", default=None, help="write per-session report to this path")
    args = p.parse_args(argv)

    targets = [args.dandiset] if args.dandiset else POOL
    rows = []
    totals = {}
    for ds_id in targets:
        try:
            totals[ds_id] = census_dandiset(ds_id, rows)
        except Exception as e:
            print(f"\n=== {ds_id}: FAILED ({type(e).__name__}: {e}) ===", flush=True)
            totals[ds_id] = (0, 0, 0)

    print("\n================ POOL CENSUS SUMMARY ================")
    print(f"{'dandiset':<10} {'sessions':>9} {'registered':>11} {'FM-ready':>9}")
    tr = tf = tn = 0
    for ds_id in targets:
        reg_n, ready_n, n = totals[ds_id]
        tr += reg_n; tf += ready_n; tn += n
        print(f"{ds_id:<10} {n:>9} {reg_n:>11} {ready_n:>9}")
    print(f"{'TOTAL':<10} {tn:>9} {tr:>11} {tf:>9}")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"summary": {k: {"sessions": v[2], "registered": v[0],
                                       "fm_ready": v[1]} for k, v in totals.items()},
                       "sessions": rows}, fh, indent=2)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
