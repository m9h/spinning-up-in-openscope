# /// brainset-pipeline
# python-version = "3.11"
# dependencies = ["dandi", "pynwb", "h5py", "numpy", "pandas"]
# ///
#
# allen_openscope_neuropixels — a brainsets pipeline that ingests OpenScope mouse
# Neuropixels sessions (NWB on DANDI) into the temporaldata/torch_brain format used by
# POYO/POYO+, so the OpenScope ecephys pool can train a spiking foundation model (the
# Neuropixels counterpart of OmniMouse, which is two-photon).
#
# WHAT MAKES THIS DIFFERENT FROM THE PRIMATE PIPELINES:
#   The primate brainsets (perich_miller, churchland, ...) rely on POYO's learnable
#   per-session UNIT embeddings, which must be re-learned for every new session (limits
#   zero-shot transfer). Here we additionally extract each unit's ALLEN CCFv3 COORDINATE
#   (x,y,z, microns) + region label from the NWB electrode table and attach them to the
#   `units` ArrayDict (ccf_x/ccf_y/ccf_z/region). The model can then build a SPATIAL unit
#   embedding (MLP over CCF coords) — units in a brand-new session get coordinates for
#   free, enabling true zero-shot cross-session/animal transfer. Keep the spatial term in
#   addition to (residual with) a learnable unit embedding, not instead of it.
#
# Run as a LOCAL brainset (same invocation as dmfc_rsg_pipeline):
#     brainsets prepare ./brainsets_pipelines/allen_openscope_neuropixels --local \
#         --raw-dir ./data/raw --processed-dir ./data/processed --dandiset 000253
#
# VALIDATED structure (streamed sub-621890_ses-1186358749 of DANDI:000253, 2026-06-23):
#   [V1] nwbfile.units: cols include spike_times, peak_channel_id, quality, firing_rate,
#        snr, isi_violations, amplitude  (2446 units in that session).
#   [V2] nwbfile.electrodes: cols include x, y, z (CCFv3 microns), location (region acronym),
#        probe_id, probe_vertical_position  (2304 rows). peak_channel_id -> electrode row.
#   [V3] processing modules: 'running', 'stimulus', 'optotagging'.
#   [V4] running speed in processing['running'] (TimeSeries, cm/s, explicit timestamps).
#   [V5] stimulus presentations live in nwbfile.intervals as *_presentations tables; the
#        TABLE NAMES VARY BY DANDISET/PARADIGM (e.g. init_grating_presentations here) — the
#        extractor scans for all '*presentations' interval tables. Confirm per dandiset.
from argparse import ArgumentParser
import datetime

import numpy as np
import pandas as pd
import h5py
from pynwb import NWBHDF5IO
from temporaldata import (
    Data,
    Interval,
    RegularTimeSeries,
    IrregularTimeSeries,
    ArrayDict,
)

from brainsets.descriptions import (
    BrainsetDescription,
    SessionDescription,
    DeviceDescription,
)
from brainsets.utils.dandi_utils import (
    extract_subject_from_nwb,
    get_nwb_asset_list,
    download_file,
)
from brainsets import serialize_fn_map
from brainsets.pipeline import BrainsetPipeline
from brainsets.taxonomy import RecordingTech  # enum members, NOT raw strings

parser = ArgumentParser()
parser.add_argument("--redownload", action="store_true")
parser.add_argument("--reprocess", action="store_true")
# Which OpenScope ecephys dandiset to ingest. The whole pool (drop-in ids):
#   000253 (global/local oddball), 001637 (predictive-processing community ecephys),
#   000248 (illusion), 000563 (barcoding), 000690 (vision2hippocampus), 001191 (loop).
parser.add_argument("--dandiset", default="000253")
parser.add_argument("--behavior-rate", type=float, default=50.0,
                    help="Hz to resample running speed onto a RegularTimeSeries.")

# Resample target for the running-speed readout (continuous, R2 — the cursor_velocity_2d
# analogue). cm/s; ~std used to normalise the POYO readout head downstream.
RUNNING_SPEED_STD = 10.0


class Pipeline(BrainsetPipeline):
    brainset_id = "allen_openscope_neuropixels"
    # dandiset_id is set per-run from --dandiset so one pipeline serves the whole pool.
    parser = parser

    @property
    def dandiset_id(self):
        return f"DANDI:{self.args.dandiset}"

    @classmethod
    def get_manifest(cls, raw_dir, args) -> pd.DataFrame:
        asset_list = get_nwb_asset_list(f"DANDI:{args.dandiset}")
        rows = [{"path": x.path, "url": x.download_url} for x in asset_list]
        # one processed file per NWB asset; id from the asset path (sub-XXX_ses-YYY...).
        for r in rows:
            stem = r["path"].split("/")[-1].replace(".nwb", "")
            r["id"] = f"{args.dandiset}_{stem}"
        return pd.DataFrame(rows).set_index("id")

    def download(self, manifest_item):
        self.update_status("DOWNLOADING")
        return download_file(
            manifest_item.path,
            manifest_item.url,
            self.raw_dir,
            overwrite=self.args.redownload,
        )

    def process(self, fpath):
        brainset_description = BrainsetDescription(
            id=self.brainset_id,
            origin_version=f"dandi/{self.args.dandiset}",
            derived_version="0.1.0",
            source=f"https://dandiarchive.org/dandiset/{self.args.dandiset}",
            description=(
                "Sorted-unit spiking from mouse visual cortex (+ thalamus/hippocampus) "
                "recorded with Neuropixels in the Allen Institute OpenScope program. "
                "Passive/active visual paradigms (oddball, sequence, omission, jitter). "
                "Units carry Allen CCFv3 coordinates + region for spatial unit embedding. "
                "Continuous readout = running speed; stimulus presentations carried as an "
                "Interval for encoding/decoding heads."
            ),
        )

        self.update_status("Loading NWB")
        io = NWBHDF5IO(fpath, "r")
        nwbfile = io.read()

        self.update_status("Extracting Metadata")
        subject = extract_subject_from_nwb(nwbfile)
        recording_date = nwbfile.session_start_time.strftime("%Y%m%d")
        sess = getattr(nwbfile, "session_id", None) or recording_date
        session_id = f"{subject.id}_{sess}"
        device_id = f"{subject.id}_{recording_date}_neuropixels"

        store_path = self.processed_dir / f"{session_id}.h5"
        if store_path.exists() and not self.args.reprocess:
            self.update_status("Skipped Processing")
            io.close()
            return

        session_description = SessionDescription(
            id=session_id,
            recording_date=datetime.datetime.strptime(recording_date, "%Y%m%d"),
            task=None,  # passive viewing: no Task taxonomy member
        )
        device_description = DeviceDescription(
            id=device_id,
            # Neuropixels; brainsets' sorted-spike-times mode label. Check for a
            # NEUROPIXELS / MULTI_ELECTRODE member in your taxonomy version.
            recording_tech=RecordingTech.MULTI_ELECTRODE_SPIKES,
        )

        self.update_status("Extracting Spikes + CCF")
        spikes, units = extract_spikes_units_ccf(nwbfile)

        self.update_status("Extracting Running Speed")
        running = extract_running_speed(nwbfile, rate=self.args.behavior_rate)

        self.update_status("Extracting Stimulus")
        stimulus = extract_stimulus(nwbfile)

        data = Data(
            brainset=brainset_description,
            session=session_description,
            device=device_description,
            spikes=spikes,
            units=units,
            domain="auto",
        )
        if running is not None:
            data.running = running
        if stimulus is not None:
            data.stimulus = stimulus

        # Temporal split of the session domain (80/10/10). For the FM, the scientifically
        # important holdouts (whole animal / whole paradigm) are configured at the MANIFEST
        # / harness level (recording_ids), not here; this in-file split is for per-session
        # decoding eval.
        self.update_status("Creating Splits")
        train_dom, valid_dom, test_dom = data.domain.split(
            [0.8, 0.1, 0.1], shuffle=False
        )
        data.train_domain = train_dom
        data.valid_domain = valid_dom
        data.test_domain = test_dom

        io.close()
        with h5py.File(store_path, "w") as file:
            data.to_hdf5(file, serialize_fn_map=serialize_fn_map)


def extract_spikes_units_ccf(nwbfile):
    """Spikes + units WITH Allen CCFv3 coordinates.

    Returns (spikes: IrregularTimeSeries, units: ArrayDict). Each unit gets its CCF
    coordinate + region from its peak channel's electrode row ([V1]/[V2]). Units that are
    unregistered (x/y/z missing or <=0) get NaN coords — the spatial-embedding MLP should
    learn a NaN/missing token, or fall back to the learnable unit embedding for those.
    """
    units_df = nwbfile.units.to_dataframe()
    elec_df = nwbfile.electrodes.to_dataframe()  # index = electrode id

    def ccf_for(peak_ch):
        try:
            row = elec_df.loc[peak_ch]
        except (KeyError, TypeError):
            return (np.nan, np.nan, np.nan, "unknown")
        x, y, z = (float(row.get(k, np.nan)) for k in ("x", "y", "z"))
        if not np.isfinite([x, y, z]).all() or min(x, y, z) <= 0:
            x = y = z = np.nan
        return (x, y, z, str(row.get("location", "unknown")))

    timestamps, unit_index, unit_meta = [], [], []
    for i, (uid, row) in enumerate(units_df.iterrows()):
        st = np.asarray(row["spike_times"], dtype=float)
        timestamps.append(st)
        unit_index.append(np.full(len(st), i, dtype=np.int64))
        peak_ch = row.get("peak_channel_id", row.get("peak_channel", -1))
        cx, cy, cz, region = ccf_for(peak_ch)
        unit_meta.append({
            "id": f"unit_{uid}",
            "unit_number": i,
            "count": len(st),
            "ccf_x": cx, "ccf_y": cy, "ccf_z": cz,
            "region": region,
            "firing_rate": float(row.get("firing_rate", np.nan)),
            "snr": float(row.get("snr", np.nan)),
            "isi_violations": float(row.get("isi_violations", np.nan)),
            "quality": str(row.get("quality", "")),
            "type": int(RecordingTech.MULTI_ELECTRODE_SPIKES),
        })

    units = ArrayDict.from_dataframe(pd.DataFrame(unit_meta), unsigned_to_long=True)
    spikes = IrregularTimeSeries(
        timestamps=np.concatenate(timestamps),
        unit_index=np.concatenate(unit_index),
        domain="auto",
    )
    spikes.sort()
    return spikes, units


def extract_running_speed(nwbfile, rate=50.0):
    """Running speed -> RegularTimeSeries `speed` (cm/s) resampled onto a uniform grid.

    Allen ecephys stores running speed with explicit (irregular) timestamps; POYO's
    continuous readout expects a RegularTimeSeries, so we linearly interpolate onto a
    fixed-rate grid spanning the recording ([V4]). Returns None if absent.
    """
    proc = nwbfile.processing.get("running")
    ts = None
    if proc is not None:
        for key in ("running_speed", "speed", "running_wheel_velocity"):
            if key in proc.data_interfaces:
                ts = proc.data_interfaces[key]
                break
    if ts is None:
        return None

    t = np.asarray(ts.timestamps[:], dtype=float)
    v = np.asarray(ts.data[:], dtype=float).reshape(-1)
    ok = np.isfinite(t) & np.isfinite(v)
    t, v = t[ok], v[ok]
    if t.size < 2:
        return None

    t0, t1 = float(t[0]), float(t[-1])
    n = int(round((t1 - t0) * rate)) + 1
    grid = t0 + np.arange(n) / rate
    speed = np.interp(grid, t, v).astype(np.float32).reshape(-1, 1)
    return RegularTimeSeries(
        sampling_rate=rate, speed=speed, domain="auto", domain_start=t0,
    )


def extract_stimulus(nwbfile):
    """All '*presentations' interval tables -> one `stimulus` Interval ([V5]).

    Concatenates every stimulus presentation table, tagging rows with `stim_table` (the
    source table name) and carrying common visual columns when present (orientation,
    contrast, temporal_frequency, spatial_frequency, phase, stimulus_name). Oddball labels
    (is_deviant, local/global, block) are paradigm-specific — derive them downstream from
    stimulus_name/orientation per dandiset. Returns None if no presentation tables.
    """
    keep_cols = [
        "orientation", "contrast", "temporal_frequency", "spatial_frequency",
        "phase", "stimulus_name", "stimulus_block", "frame",
    ]
    frames = []
    for name, table in nwbfile.intervals.items():
        if "presentation" not in name.lower():
            continue
        df = table.to_dataframe().rename(
            columns={"start_time": "start", "stop_time": "end"}
        )
        if "start" not in df or "end" not in df:
            continue
        sub = df[["start", "end"]].copy()
        for c in keep_cols:
            if c in df.columns:
                sub[c] = df[c].values
        sub["stim_table"] = name
        frames.append(sub)

    if not frames:
        return None
    alldf = pd.concat(frames, ignore_index=True).sort_values("start")
    alldf = alldf[np.isfinite(alldf["start"]) & np.isfinite(alldf["end"])]
    return Interval.from_dataframe(alldf.reset_index(drop=True))
