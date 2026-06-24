"""Shared, dependency-light NWB parsing for OpenScope mouse Neuropixels sessions.

Pure numpy/pandas (NO temporaldata/brainsets) so the validator and the sweep use ONE
tested source of truth for the convention/column drift across dandisets. `pipeline.py`
stays self-contained (brainsets execs it standalone) but mirrors this logic — keep them in
sync. Drift handled (verified by the pool sweep, 2026-06-23):

  unit -> electrode link:
    older (000253/000248/000563/000690): units['peak_channel_id'] -> electrode *id*
    newer (001637/001191):               units['electrodes'] DynamicTableRegion -> row idx
  CCF columns on electrodes:
    ('x','y','z')  OR  ('*_ccf_coordinate' long names)  OR  absent (-> NaN coords)
  running module: 'running'  OR  'running_new'   (iface 'running_speed' etc.)
"""
import numpy as np

RUN_KEYS = ("running_speed", "running_speed_new", "speed", "running_wheel_velocity")
CCF_COLS = [
    ("x", "y", "z"),
    ("anterior_posterior_ccf_coordinate",
     "dorsal_ventral_ccf_coordinate",
     "left_right_ccf_coordinate"),
]
# Allen CCFv3 spans thousands of µm. Some community-processed sessions (001191) ship a
# degenerate x/y/z (values ~0-10) that are NOT CCF — require a plausible magnitude.
CCF_MIN_MAX_UM = 100.0
VISUAL = ("orientation", "contrast", "temporal_frequency", "spatial_frequency",
          "phase", "stimulus_name", "stimulus_block")


def electrode_ccf(nwb):
    """(coords [n_elec,3] µm or None, regions [n_elec] or None, ccf colnames or None),
    row-indexed. Region (from 'location') is returned INDEPENDENTLY of CCF, so datasets
    with region labels but no absolute CCF (e.g. 001637) still get region tokens."""
    el = nwb.electrodes
    cols = list(el.colnames)
    region = [str(s) for s in el["location"][:]] if "location" in cols else None
    for trio in CCF_COLS:
        if all(c in cols for c in trio):
            xyz = np.stack([np.asarray(el[c][:], float) for c in trio], axis=1)
            ok = xyz[np.isfinite(xyz).all(1)]
            if ok.size and np.nanmax(np.abs(ok)) >= CCF_MIN_MAX_UM:
                return xyz, region, trio  # plausible CCF µm
            # else degenerate placeholder (e.g. 001191 x,y,z in [0,10]) — not CCF
    return None, region, None


def unit_electrode_row(nwb):
    """(row index into electrodes per unit [-1 if unknown], method str). Handles both the
    peak_channel_id (id->row) and the units.electrodes-region (ragged) conventions."""
    units = nwb.units
    cols = list(units.colnames)
    n = len(units)
    if "peak_channel_id" in cols:
        elec_ids = np.asarray(nwb.electrodes.id[:])
        pos = {int(i): r for r, i in enumerate(elec_ids)}
        peak = np.asarray(units["peak_channel_id"][:])
        return np.array([pos.get(int(p), -1) for p in peak], int), "peak_channel_id"
    if "electrodes" in cols and getattr(units, "electrodes_index", None) is not None:
        # units.electrodes is the unit's FULL waveform electrode set (e.g. 480 chans), NOT a
        # peak-ordered list — so the first row is electrode 0 for every unit. The peak is
        # units['extremum_channel_index']: a within-set offset (0..group-1), or a global row.
        flat = np.asarray(units.electrodes.data[:])
        bounds = np.asarray(units.electrodes_index.data[:])
        starts = np.concatenate([[0], bounds[:-1]])
        n_elec = len(nwb.electrodes)
        ext = (np.asarray(units["extremum_channel_index"][:])
               if "extremum_channel_index" in cols else np.zeros(n, int))
        rows = np.full(n, -1, int)
        for i in range(n):
            s, e = int(starts[i]), int(bounds[i])
            grp, x = e - s, int(ext[i])
            if 0 <= x < grp:
                rows[i] = flat[s + x]          # within-set peak offset
            elif 0 <= x < n_elec:
                rows[i] = x                     # already a global row index
            elif e > s:
                rows[i] = flat[s]               # fallback: first of set
        method = ("electrodes_region+extremum" if "extremum_channel_index" in cols
                  else "electrodes_region")
        return rows, method
    return np.full(n, -1, int), "none"


def unit_ccf(nwb):
    """(coords [n_units,3] with NaN where missing/unregistered, regions, link method, ccf cols)."""
    xyz_el, region_el, found = electrode_ccf(nwb)
    rows, method = unit_electrode_row(nwb)
    n = len(nwb.units)
    coords = np.full((n, 3), np.nan)
    regions = ["unknown"] * n
    max_rows = (len(xyz_el) if xyz_el is not None
                else len(region_el) if region_el is not None else 0)
    for i, r in enumerate(rows):
        if 0 <= r < max_rows:
            if xyz_el is not None:
                c = xyz_el[r]
                if np.isfinite(c).all() and c.min() > 0:
                    coords[i] = c
            if region_el is not None:
                regions[i] = region_el[r]
    return coords, regions, method, found


def find_running(nwb):
    """(module_name, iface_name, TimeSeries) or (None, None, None). Scans any processing
    module whose name contains 'run' ('running', 'running_new', ...); prefers a known key,
    else any interface whose name contains 'speed' (catches 'running_speed_new')."""
    for mod in nwb.processing:
        if "run" not in mod.lower():
            continue
        di = nwb.processing[mod].data_interfaces
        for k in RUN_KEYS:
            if k in di:
                return mod, k, di[k]
        for k, v in di.items():
            if "speed" in k.lower():
                return mod, k, v
    return None, None, None


def resample_running(ts, rate=50.0, max_cm_s=150.0):
    """(t0, speed[n,1] float32) on a uniform grid, artifacts (|v|>max) rejected, or None."""
    t = np.asarray(ts.timestamps[:], float)
    v = np.asarray(ts.data[:], float).reshape(-1)
    v = np.where(np.abs(v) > max_cm_s, np.nan, v)
    ok = np.isfinite(t) & np.isfinite(v)
    t, v = t[ok], v[ok]
    if t.size < 2:
        return None
    t0, t1 = float(t[0]), float(t[-1])
    n = int(round((t1 - t0) * rate)) + 1
    grid = t0 + np.arange(n) / rate
    return t0, np.interp(grid, t, v).astype(np.float32).reshape(-1, 1)


def stim_tables(nwb):
    """{table_name: (n_rows, [present visual cols])} for every '*presentation*' interval."""
    out = {}
    for name in (nwb.intervals or {}):
        if "presentation" in name.lower():
            tbl = nwb.intervals[name]
            out[name] = (len(tbl), [c for c in VISUAL if c in tbl.colnames])
    return out


def quick_facts(nwb):
    """Cheap per-session summary for the sweep (no spike_times / running data loaded)."""
    f = {"units": 0, "spikes": 0, "link": None, "ccf_pct": None, "ccf_distinct": 0,
         "ccf_cols": None, "has_region": False, "run_mod": None, "run_iface": None,
         "stim_tables": {}, "notes": []}
    if getattr(nwb, "units", None) is not None and len(nwb.units) > 0:
        f["units"] = len(nwb.units)
        try:
            f["spikes"] = int(nwb.units.spike_times_index.data[-1])
        except Exception:
            f["notes"].append("no spike_times_index")
        coords, regions, method, ccf_cols = unit_ccf(nwb)
        f["link"] = method
        f["ccf_cols"] = ccf_cols
        fin = np.isfinite(coords).all(1)
        f["ccf_pct"] = round(100 * fin.mean(), 0) if len(fin) else 0
        # distinct finite coords — guards the "all units mapped to the same electrode" bug.
        f["ccf_distinct"] = int(len(np.unique(coords[fin], axis=0))) if fin.any() else 0
        f["has_region"] = any(r != "unknown" for r in regions)
        if method == "none":
            f["notes"].append(f"no unit->electrode link (cols={list(nwb.units.colnames)[:6]})")
        if ccf_cols is None:
            f["notes"].append("no absolute CCF columns" +
                              (" (region labels present — register to CCF or use region token)"
                               if f["has_region"] else " and no region labels"))
    else:
        f["notes"].append("no units in session file")

    mod, iface, _ = find_running(nwb)
    f["run_mod"], f["run_iface"] = mod, iface
    if iface is None:
        f["notes"].append(f"no running speed (proc={list(nwb.processing)[:5]})")

    f["stim_tables"] = stim_tables(nwb)
    if not f["stim_tables"]:
        f["notes"].append(f"no '*presentation*' tables (intervals={list(nwb.intervals or {})[:4]})")
    return f
