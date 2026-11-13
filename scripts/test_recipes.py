"""Runs every ```python block of the Blender skill inside Blender, in order, in one session.

    blender -b --factory-startup -noaudio --python scripts/test_recipes.py -- <work dir> <file.md> [<file.md> ...]

The blocks see what the blender_python tool gives them: bpy, bmesh, mathutils, math, os, sys, np and roomve
already imported, the work dir as working directory, state that stays between blocks. A block that raises, or
that uses a deprecated API, fails the run. Blocks fenced as ```py are examples that are not meant to run alone
and are skipped. Blocks that call roomve.* run only where the module of the service can be imported (its
image, where it is in /srv/bridge, or the folder named by ROOMVE_BRIDGE); elsewhere, as in the public CI, they are reported as skipped.
"""
import os
import re
import sys
import time
import traceback
import types
import warnings

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
work, files = argv[0], [os.path.abspath(f) for f in argv[1:]]     # before the chdir below
os.makedirs(work, exist_ok=True)
os.chdir(work)
bpy.ops.wm.read_factory_settings(use_empty=True)     # as a new session of the service: an empty scene
os.chdir(work)

# An image in the space, as generate_image would leave it.
os.makedirs("images", exist_ok=True)
img = bpy.data.images.new("wood", 64, 64)
img.pixels = [v for _ in range(64 * 64) for v in (0.45, 0.27, 0.13, 1.0)]
img.filepath_raw = os.path.abspath("images/wood.png")
img.file_format = "PNG"
img.save()
bpy.data.images.remove(img)

import math  # noqa: E402

import bmesh  # noqa: E402
import mathutils  # noqa: E402
import numpy  # noqa: E402

# Blender's Python does not read PYTHONPATH: the folder of the service's helper module is added by hand.
for folder in (os.environ.get("ROOMVE_BRIDGE"), "/srv/bridge"):
    if folder and os.path.isdir(folder) and folder not in sys.path:
        sys.path.insert(0, folder)
try:
    import roomve  # the helper module of the service, when the test runs in its image
    roomve.WORKDIR = os.getcwd()
    HAVE_ROOMVE = True
except ImportError:
    roomve = types.SimpleNamespace()
    HAVE_ROOMVE = False

NS = {"__name__": "__main__", "bpy": bpy, "bmesh": bmesh, "mathutils": mathutils, "math": math, "os": os, "sys": sys,
      "np": numpy, "roomve": roomve}
warnings.simplefilter("error", DeprecationWarning)

failed = 0
total = 0
skipped = 0
for path in files:
    text = open(path, encoding="utf-8").read()
    heading = ""
    pos = 0
    for m in re.finditer(r"^(#{1,4} [^\n]+)$|^```python\n(.*?)^```", text, re.M | re.S):
        if m.group(1):
            heading = m.group(1).lstrip("# ")
            continue
        code = m.group(2)
        if not HAVE_ROOMVE and re.search(r"\broomve\.", code):
            # Blocks that call the helpers of the service only run where its module is (the service's image).
            skipped += 1
            print("SKIP  %-62s (needs the roomve module of the service)" % heading[:62], flush=True)
            continue
        total += 1
        line = text.count("\n", 0, m.start()) + 2
        NS.pop("result", None)
        start = time.time()
        try:
            exec(compile("\n" * (line - 1) + code, path, "exec"), NS)
            print("PASS  %-62s %5.1f s  result=%r" % (heading[:62], time.time() - start, NS.get("result")), flush=True)
        except BaseException:  # noqa: BLE001
            failed += 1
            print("FAIL  %s (%s:%d)" % (heading, os.path.basename(path), line), flush=True)
            traceback.print_exc()
        os.chdir(work)

print("%d blocks, %d failed, %d skipped" % (total, failed, skipped), flush=True)
sys.exit(1 if failed or not total else 0)
