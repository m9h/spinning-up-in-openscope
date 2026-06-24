#!/usr/bin/env python
"""Validate the allen_openscope_neuropixels extraction against a live DANDI session.

Streams one OpenScope Neuropixels NWB (no download) and exercises the SAME parsing the
pipeline does — units+CCF, running speed, stimulus — via the shared openscope_nwb module
(plain numpy/pandas, no temporaldata/brainsets), so it runs in the spinning-up venv.

    python validate_one_session.py --dandiset 000253          # auto-picks the session file
    python validate_one_session.py --dandiset 001637 --index 0

Exit 0 = all checks passed. Requires: dandi pynwb h5py remfile numpy pandas.
"""
import argparse
import sys

import numpy as np

from openscope_nwb import unit_ccf, find_running, resample_running, stim_tables


def stream_nwb(dandiset, version, index, prefer_main):
    import h5py
    import remfile
    from pynwb import NWBHDF5IO
    from dandi.dandiapi import DandiAPIClient

    with DandiAPIClient() as client:
        assets = list(client.get_dandiset(dandiset, version).get_assets())
    if not assets:
        raise SystemExit(f"No assets in DANDI:{dandiset}")
    if index is None:
        index = 0
        if prefer_main:  # session file carries units/running/stimulus; probe-N are LFP-only
            for i, a in enumerate(assets):
                if "probe-" not in a.path.lower():
                    index = i
                    break
    asset = assets[index]
    url = asset.get_content_url(follow_redirects=1, strip_query=True)
    print(f"[stream] {len(assets)} assets; #{index}: {asset.path}")
    h5 = h5py.File(remfile.File(url), "r")
    return NWBHDF5IO(file=h5, mode="r", load_namespaces=True).read(), asset.path


def check_units_ccf(nwb):
    n = len(nwb.units)
    n_spikes = int(nwb.units.spike_times_index.data[-1])
    coords, regions, method, ccf_cols = unit_ccf(nwb)
    fin = np.isfinite(coords).all(1)
    frac = fin.mean() if len(fin) else 0.0
    import pandas as pd
    top = pd.Series(regions).value_counts().head(6).to_dict()
    print(f"[units]  n_units={n}  n_spikes={n_spikes:,}  link={method}")
    print(f"[ccf]    cols={ccf_cols}  finite: {int(fin.sum())}/{len(fin)} ({frac:.0%})")
    if fin.any():
        ex = coords[fin][0]
        print(f"[ccf]    example (µm): x={ex[0]:.0f} y={ex[1]:.0f} z={ex[2]:.0f}")
    print(f"[ccf]    top regions: {top}")
    assert n > 0 and n_spikes > 0, "no units/spikes"
    assert method != "none", "no unit->electrode link (neither peak_channel_id nor electrodes)"
    assert frac > 0.0, "no units have finite CCF coords"


def check_running(nwb, rate=50.0):
    mod, iface, ts = find_running(nwb)
    assert ts is not None, f"no running speed (modules={list(nwb.processing)})"
    out = resample_running(ts, rate=rate)
    assert out is not None, "running speed too short after artifact rejection"
    _, speed = out
    print(f"[running] module='{mod}' iface='{iface}'  ->  {len(speed):,}@{rate:g}Hz; "
          f"clean range [{speed.min():.1f},{speed.max():.1f}] mean={speed.mean():.2f} cm/s")


def check_stimulus(nwb):
    tables = stim_tables(nwb)
    assert tables, f"no '*presentation*' tables (intervals={list(nwb.intervals or {})})"
    total = 0
    for name, (cnt, vis) in tables.items():
        total += cnt
        print(f"[stim]   {name}: {cnt} rows; visual={vis}")
    assert total > 0, "stimulus tables empty"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dandiset", default="000253")
    ap.add_argument("--version", default="draft")
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--no-prefer-main", action="store_true")
    args = ap.parse_args()

    try:
        nwb, path = stream_nwb(args.dandiset, args.version, args.index,
                               prefer_main=not args.no_prefer_main)
    except ImportError as e:
        print(f"missing dep: {e}. pip install dandi pynwb h5py remfile"); return 2

    failed = []
    for label, fn in [("units+CCF", check_units_ccf), ("running", check_running),
                      ("stimulus", check_stimulus)]:
        try:
            fn(nwb)
        except AssertionError as e:
            print(f"[FAIL] {label}: {e}"); failed.append(label)
        except Exception as e:
            print(f"[ERROR] {label}: {type(e).__name__}: {e}"); failed.append(label)

    print("-" * 60)
    if failed:
        print(f"FAILED: {failed}  (session: {path})"); return 1
    print(f"ALL CHECKS PASSED  (session: {path})"); return 0


if __name__ == "__main__":
    sys.exit(main())
