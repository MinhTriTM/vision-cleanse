"""VisionCleanse: clean near-duplicates and split leakage from CV datasets.

MVP scope: ring 1 (exact hash), ring 2 (pHash/dHash), split-priority
resolution, label-conflict reporting, quarantine + dry-run, and
YOLO/COCO annotation sync. Deep-feature rings arrive later.
"""

from .core import clean

__version__ = "0.1.0"
__all__ = ["clean", "__version__"]
