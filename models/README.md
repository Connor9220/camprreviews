# campr test models

FreeCAD documents used to test CAM pull requests. campr-bot lists them (from `models.json`) to every
review, and copies them into the job before opening them, so a review never changes these originals.
Anyone is welcome to use them for their own testing.

| Folder | What it tests |
|---|---|
| `twp-block/` | Work planes and 3+2 machining: a block with four work planes (top, a 30 degree facet, a compound facet, the front face) and 16 operations, on a 5-axis AC-trunnion machine. `twp_test_block_model.py` rebuilds the model. |
| `class-tray/` | Multi-pass Profile with a start point, Lead In/Out and dressups, with (B) and without (A) a work plane. |
| `pocket-island/` | Pocket patterns and finishing, Profile multi-pass and ramps, MillFace; plus a file saved before PR #30402 for migration tests. |
| `avoid-faces/` | Planar Surface with Avoid Faces, and a plain pocket floor. |

To add a model: put it in a folder here and add an entry to `models.json` (name, files, a description of
what is in it, and tags naming the operations and features it exercises).
