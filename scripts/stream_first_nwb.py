#!/usr/bin/env python
"""Stream one NWB session from an OpenScope dandiset WITHOUT downloading it.

Reads HDF5 objects lazily over the DANDI S3 bucket via remfile, so you can scope
the file layout (acquisition, units, LFP, stimulus/trials tables) before committing
~680 GB of local disk. Safe on the GB10 box: nothing large is pulled into memory.

    python scripts/stream_first_nwb.py                 # first asset of 000253
    python scripts/stream_first_nwb.py --dandiset 000253 --index 0

Requires:  pip install dandi pynwb h5py remfile
"""
import argparse
import sys


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dandiset", default="000253", help="DANDI id (default 000253)")
    p.add_argument("--version", default="draft", help="version (default draft)")
    p.add_argument("--index", type=int, default=0, help="which asset to stream")
    args = p.parse_args()

    try:
        import h5py
        import remfile
        from pynwb import NWBHDF5IO
        from dandi.dandiapi import DandiAPIClient
    except ImportError as e:
        print(f"Missing dependency: {e}. Run: pip install dandi pynwb h5py remfile")
        return 1

    print(f"Resolving DANDI:{args.dandiset} ({args.version}) ...")
    with DandiAPIClient() as client:
        dandiset = client.get_dandiset(args.dandiset, args.version)
        assets = list(dandiset.get_assets())
        if not assets:
            print("No assets found.")
            return 1
        print(f"  {len(assets)} assets. Streaming asset #{args.index}:")
        asset = assets[args.index]
        s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)
        print(f"  path: {asset.path}")
        print(f"  url:  {s3_url}")

    # Lazy HDF5 over HTTP — only metadata + requested chunks are fetched.
    rem = remfile.File(s3_url)
    with h5py.File(rem, "r") as h5:
        with NWBHDF5IO(file=h5, mode="r", load_namespaces=True) as io:
            nwb = io.read()
            print("\n=== Session ===")
            print(f"  session_id:   {getattr(nwb, 'session_id', None)}")
            print(f"  description:  {nwb.session_description}")
            print(f"  subject:      {getattr(nwb.subject, 'subject_id', None)}"
                  f"  ({getattr(nwb.subject, 'genotype', None)})")
            print("\n=== Contents (no data pulled) ===")
            print(f"  acquisition:        {list(nwb.acquisition.keys())}")
            print(f"  processing modules: {list(nwb.processing.keys())}")
            if nwb.units is not None:
                print(f"  units:              {len(nwb.units)} sorted units, "
                      f"cols={list(nwb.units.colnames)}")
            if nwb.intervals:
                print(f"  interval tables:    {list(nwb.intervals.keys())}")
            if nwb.electrodes is not None:
                print(f"  electrodes:         {len(nwb.electrodes)} rows, "
                      f"cols={list(nwb.electrodes.colnames)}")
            print("\nStreamed OK. Next: window LFP / spike times for the oddball epochs "
                  "(see notebooks/00_stream_and_explore_nwb.ipynb).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
