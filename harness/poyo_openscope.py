"""Drop-in POYO/POYO+ dataset for the allen_openscope_neuropixels brainset.

Mirrors poyo_datasets/poyo_mp.py (PoyoMPDataset): a thin subclass that attaches a
READOUT_CONFIG per recording via get_recording_hook. Copy this into your harness'
`poyo_datasets/` and register it alongside poyo_mp/flint/odoherty/churchland.

Two things differ from the primate datasets:
  1. Readout target is RUNNING SPEED (continuous, R2) — OpenScope is passive viewing, so
     there's no cursor/hand kinematics. (Add a stimulus-classification head as a second
     readout if you want the predictive-processing target: deviant-vs-standard / local-vs-
     global, derived from `stimulus.*` in the brainset.)
  2. Units carry CCFv3 coords (units.ccf_x/ccf_y/ccf_z + region). Point the model's unit
     tokenizer at these to build a SPATIAL embedding (MLP over CCF), residual with the
     learnable unit embedding — see docs/06. That swap lives in torch_brain's unit
     embedding / tokenizer config, not here; this file only exposes the data + readout.
"""
from copy import deepcopy

import torchmetrics
from temporaldata import Data


# cm/s; running speed is ~0 at rest with bouts to ~30-60 cm/s. Tune std to your pool.
RUNNING_SPEED_READOUT = {
    "readout": {
        "readout_id": "running_speed",
        "normalize_mean": 0.0,
        "normalize_std": 10.0,
        "metrics": [{"metric": torchmetrics.R2Score()}],
        # restrict eval to locomotion bouts if you add a `running_bouts` Interval upstream:
        # "eval_interval": "running_bouts",
    }
}


class _OpenScopeReadoutMixin:
    """Attaches the running-speed readout to every recording. Compose with whatever local
    brainset base your torch_brain version exposes (see _wiring below)."""

    READOUT_CONFIG = RUNNING_SPEED_READOUT

    def get_recording_hook(self, data: Data):
        data.config = deepcopy(self.READOUT_CONFIG)
        return super().get_recording_hook(data)


# --- wiring -----------------------------------------------------------------------------
# A locally-prepared brainset has no `brainsets.datasets.AllenOpenScopeNeuropixels` class,
# so build the dataset from the processed dir. Pick whichever your torch_brain version has:
#
#   from torch_brain.dataset import Dataset            # generic processed-dir loader
#   class PoyoOpenScopeDataset(_OpenScopeReadoutMixin, Dataset):
#       def __init__(self, root, transform=None, **kw):
#           super().__init__(root=root, brainset="allen_openscope_neuropixels",
#                            recording_ids=TRAIN_RECORDING_IDS, transform=transform, **kw)
#
# Then nest it next to the primate sets exactly like poyo_1.py:
#
#   from torch_brain.dataset import NestedSpikingDataset
#   ds = NestedSpikingDataset(datasets={"openscope": PoyoOpenScopeDataset(root)}, ...)
#
# HOLDOUTS (the scientific splits — set these here, NOT in the brainset .h5):
#   TRAIN_RECORDING_IDS  = pretrain pool (most sessions / most animals)
#   VALID/TEST split on HELD-OUT ANIMALS (subject-level, no leakage) and a HELD-OUT
#   PARADIGM (e.g. keep all of 000253 global/local out of pretraining, fine-tune on it) —
#   that's the "does the FM help on a new predictive-processing experiment" eval.
TRAIN_RECORDING_IDS = [
    # fill from your processed dir, e.g. "<sub>_<ses>" ids emitted by the pipeline.
    # keep entire held-out animals / 000253 out for the transfer + efficacy evals.
]
