#!/usr/bin/env python
"""Compatibility sweep across the OpenScope mouse-ecephys pool.

Streams ONE session-level NWB from each pool dandiset and reports whether the
allen_openscope_neuropixels extractors will find what they need (units + unit->electrode
link, CCF coords, running speed, stimulus tables) plus any drift. Read-only, non-fatal,
runs in the spinning-up venv. Shares parsing with the pipeline via openscope_nwb.py.

    python sweep_pool.py                       # default pool
    python sweep_pool.py --dandisets 000253 001637

Requires: dandi pynwb h5py remfile numpy.
"""
import argparse
import sys

from openscope_nwb import quick_facts

POOL = ["000253", "001637", "000248", "000563", "000690", "001191"]


def session_assets(client, did, version):
    assets = list(client.get_dandiset(did, version).get_assets())
    non_probe = [a for a in assets if "probe-" not in a.path.lower()]
    return non_probe or assets


def open_nwb(asset):
    import h5py
    import remfile
    from pynwb import NWBHDF5IO
    url = asset.get_content_url(follow_redirects=1, strip_query=True)
    h5 = h5py.File(remfile.File(url), "r")
    return NWBHDF5IO(file=h5, mode="r", load_namespaces=True).read(), h5


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dandisets", nargs="+", default=POOL)
    ap.add_argument("--version", default="draft")
    ap.add_argument("--max-tries", type=int, default=3)
    args = ap.parse_args()

    try:
        from dandi.dandiapi import DandiAPIClient
    except ImportError as e:
        print(f"missing dep: {e}. pip install dandi pynwb h5py remfile"); return 2

    rows = []
    with DandiAPIClient() as client:
        for did in args.dandisets:
            print(f"\n=== DANDI:{did} ===", flush=True)
            try:
                cands = session_assets(client, did, args.version)
            except Exception as e:
                print(f"  [error] listing assets: {e}")
                rows.append((did, "LIST-ERR", None)); continue

            picked, facts = None, None
            for a in cands[:args.max_tries]:
                try:
                    nwb, h5 = open_nwb(a)
                except Exception as e:
                    print(f"  [skip] {a.path}: {type(e).__name__}: {e}"); continue
                facts = quick_facts(nwb)
                picked = a.path
                h5.close()
                if facts["units"] > 0:
                    break
                print(f"  [retry] {a.path}: no units, next non-probe asset")
            if facts is None:
                rows.append((did, "OPEN-ERR", None)); continue

            print(f"  file: {picked}")
            print(f"  units={facts['units']}  spikes={facts['spikes']:,}  link={facts['link']}  "
                  f"ccf={facts['ccf_pct']}% ({facts['ccf_distinct']} distinct) via {facts['ccf_cols']}  "
                  f"running={facts['run_mod']}/{facts['run_iface']}  "
                  f"stim_tables={len(facts['stim_tables'])}")
            for n, (cnt, vis) in list(facts["stim_tables"].items())[:8]:
                print(f"    - {n}: {cnt} rows, visual={vis}")
            if len(facts["stim_tables"]) > 8:
                print(f"    ... (+{len(facts['stim_tables']) - 8} more tables)")
            for note in facts["notes"]:
                print(f"    ! {note}")
            rows.append((did, picked, facts))

    print("\n" + "=" * 82)
    print(f"{'DANDI':7} {'units':>6} {'spk(M)':>7} {'CCF%':>5} {'link':>16} "
          f"{'running':>12} {'#stim':>5}  status")
    print("-" * 82)
    for did, picked, f in rows:
        if not f:
            print(f"{did:7} {'':>6} {'':>7} {'':>5} {'':>16} {'':>12} {'':>5}  {picked}")
            continue
        core = f["units"] > 0 and f["link"] != "none" and f["run_iface"] and f["stim_tables"]
        if core:
            status = ("READY" if f["ccf_pct"] else
                      "USABLE (no CCF; region-only)" if f["has_region"] else
                      "USABLE (no CCF/region)")
        else:
            status = "needs: " + "; ".join(f["notes"][:2])
        print(f"{did:7} {f['units']:>6} {f['spikes']/1e6:>7.1f} {str(f['ccf_pct'] or '-'):>5} "
              f"{str(f['link']):>16} {str(f['run_mod'] or '-'):>12} "
              f"{len(f['stim_tables']):>5}  {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
