"""Runs every ```python block of the Blender skill inside Blender, in order, in one session.

    blender -b --factory-startup -noaudio --python scripts/test_recipes.py -- <work dir> <file.md> [<file.md> ...]

The blocks see what the blender_python tool gives them: bpy, bmesh, mathutils, math, os, sys, np and roomve
already imported, the work dir as working directory, state that stays between blocks. A block that raises, or
that uses a deprecated API, fails the run. Blocks fenced as ```py are examples that are not meant to run alone
and are skipped.
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
work, files = argv[0], argv[1:]
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

try:
    import roomve  # the helper module of the service, when the test runs in its image
except ImportError:
    roomve = types.SimpleNamespace()

NS = {"__name__": "__main__", "bpy": bpy, "bmesh": bmesh, "mathutils": mathutils, "math": math, "os": os, "sys": sys,
      "np": numpy, "roomve": roomve}
warnings.simplefilter("error", DeprecationWarning)

failed = 0
total = 0
for path in files:
    text = open(path, encoding="utf-8").read()
    heading = ""
    pos = 0
    for m in re.finditer(r"^(#{1,4} [^\n]+)$|^```python\n(.*?)^```", text, re.M | re.S):
        if m.group(1):
            heading = m.group(1).lstrip("# ")
            continue
        total += 1
        code = m.group(2)
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

print("%d blocks, %d failed" % (total, failed), flush=True)
sys.exit(1 if failed or not total else 0)
