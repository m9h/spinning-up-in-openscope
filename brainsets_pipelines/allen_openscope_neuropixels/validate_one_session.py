#!/usr/bin/env python
"""Validate the allen_openscope_neuropixels extraction logic against a live DANDI session.

Streams one OpenScope Neuropixels NWB (no download) and exercises the SAME parsing that
pipeline.py does — units+CCF, running speed, stimulus presentations — but with plain
numpy/pandas (NO temporaldata/brainsets), so it runs in the spinning-up venv. Use it to
shake out per-dandiset column-name drift before a real `brainsets prepare`.

    python validate_one_session.py --dandiset 000253          # auto-picks a main (non-ogen) session
    python validate_one_session.py --dandiset 001637 --index 0

Exit code 0 = all checks passed. Requires: dandi pynwb h5py remfile numpy pandas.
"""
import argparse
import sys

import numpy as np
import pandas as pd


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
        if prefer_main:
            # The units/running/stimulus live in the SESSION-level file; `*_probe-N_ecephys.nwb`
            # are per-probe raw/LFP only. For 000253 the session file is `*_ogen.nwb`.
            for i, a in enumerate(assets):
                if "probe-" not in a.path.lower():
                    index = i
                    break
    asset = assets[index]
    url = asset.get_content_url(follow_redirects=1, strip_query=True)
    print(f"[stream] {len(assets)} assets; #{index}: {asset.path}")
    rem = remfile.File(url)
    h5 = h5py.File(rem, "r")
    nwb = NWBHDF5IO(file=h5, mode="r", load_namespaces=True).read()
    return nwb, asset.path


def check_units_ccf(nwb):
    """units count, total spikes (via index, cheap), and CCF coverage from peak channel."""
    n_units = len(nwb.units)
    n_spikes = int(nwb.units.spike_times_index.data[-1])
    cols = list(nwb.units.colnames)
    peak_col = "peak_channel_id" if "peak_channel_id" in cols else (
        "peak_channel" if "peak_channel" in cols else None)
    assert peak_col, f"no peak_channel(_id) column; units cols={cols}"
    peak = np.asarray(nwb.units[peak_col][:])

    elec = nwb.electrodes.to_dataframe()
    ecols = list(elec.columns)
    for k in ("x", "y", "z", "location"):
        assert k in ecols, f"electrodes missing '{k}'; cols={ecols}"

    xyz, regions = [], []
    for pc in peak:
        try:
            row = elec.loc[pc]
        except (KeyError, TypeError):
            xyz.append((np.nan, np.nan, np.nan)); regions.append("unknown"); continue
        x, y, z = (float(row["x"]), float(row["y"]), float(row["z"]))
        if not np.isfinite([x, y, z]).all() or min(x, y, z) <= 0:
            x = y = z = np.nan
        xyz.append((x, y, z)); regions.append(str(row["location"]))
    xyz = np.array(xyz)
    finite = np.isfinite(xyz).all(axis=1)
    frac = finite.mean() if len(finite) else 0.0
    top = pd.Series(regions).value_counts().head(6).to_dict()

    print(f"[units]  n_units={n_units}  n_spikes={n_spikes:,}  peak_col={peak_col}")
    print(f"[ccf]    finite CCF coords: {finite.sum()}/{len(finite)} ({frac:.0%})")
    if finite.any():
        ex = xyz[finite][0]
        print(f"[ccf]    example coord (µm): x={ex[0]:.0f} y={ex[1]:.0f} z={ex[2]:.0f}")
    print(f"[ccf]    top regions: {top}")
    assert n_units > 0 and n_spikes > 0, "no units/spikes"
    assert frac > 0.0, "no units have finite CCF coords (registration missing?)"
    return True


def check_running(nwb, rate=50.0):
    proc = nwb.processing.get("running")
    assert proc is not None, f"no 'running' processing module; have {list(nwb.processing)}"
    names = list(proc.data_interfaces)
    ts = None
    for key in ("running_speed", "speed", "running_wheel_velocity"):
        if key in proc.data_interfaces:
            ts = proc.data_interfaces[key]; chosen = key; break
    assert ts is not None, f"no known running-speed interface; have {names}"
    t = np.asarray(ts.timestamps[:], float)
    v = np.asarray(ts.data[:], float).reshape(-1)
    ok = np.isfinite(t) & np.isfinite(v)
    t, v = t[ok], v[ok]
    n = int(round((t[-1] - t[0]) * rate)) + 1
    grid = t[0] + np.arange(n) / rate
    speed = np.interp(grid, t, v)
    print(f"[running] interface='{chosen}' (avail={names})")
    print(f"[running] {len(t):,} samples; resampled->{n:,}@{rate:g}Hz; "
          f"speed range [{speed.min():.1f},{speed.max():.1f}] mean={speed.mean():.2f}")
    assert n > 1, "running speed too short"
    return True


def check_stimulus(nwb):
    tables = [k for k in nwb.intervals if "presentation" in k.lower()]
    assert tables, f"no '*presentation*' interval tables; have {list(nwb.intervals)}"
    visual = ("orientation", "contrast", "temporal_frequency", "spatial_frequency",
              "phase", "stimulus_name", "stimulus_block")
    total = 0
    for name in tables:
        df = nwb.intervals[name].to_dataframe()
        present = [c for c in visual if c in df.columns]
        total += len(df)
        print(f"[stim]   {name}: {len(df)} rows; visual cols={present}")
    assert total > 0, "stimulus tables are empty"
    return True


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

    checks = [("units+CCF", check_units_ccf), ("running", check_running),
              ("stimulus", check_stimulus)]
    failed = []
    for label, fn in checks:
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
