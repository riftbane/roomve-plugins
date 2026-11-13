---
name: roomve-blender
description: Write Blender Python that works at the first try in the headless Blender 5.2 of Roomve MCP (the blender_python tool). Covers the API that changed since Blender 2.8-4.x (EEVEE engine id, Principled BSDF inputs, auto smooth, OBJ/STL/PLY exporters, layered actions and f-curves, bone collections, compositor, video output), what an empty headless scene lacks (camera, light, world), safe Cycles settings on CPU within the time and memory limits, and tested recipes for modeling, modifiers, materials, lighting, rendering, UV, rigging, animation, geometry nodes, import and export, and PBR textures - baking materials to base color, roughness, metallic, normal and AO maps, high-to-low poly bakes, extracting the textures of a model, deriving maps from a picture. Use it BEFORE writing code for blender_python, when a Blender job fails or times out, and when planning a render, a bake or an export.
---

# Blender in Roomve MCP

The instance behind `blender_python` is **Blender 5.2 LTS, headless, on CPU** (Python 3.13, numpy). Free Python,
whole `bpy` API. Read **roomve-mcp** first for the session, the queue and the files; this skill is about the code.

- `references/recipes.md` — working code for the common jobs, run on this Blender before each release. Read the
  recipe before writing that kind of code; copy the helpers of recipe 1.
- `references/api-changes.md` — every difference from older Blender that breaks old code, with the error it gives
  and what to write instead. Read it when an error mentions a missing attribute, operator or enum value.

## What the code starts with

- Already imported: `bpy`, `bmesh`, `mathutils`, `math`, `os`, `sys`, `np`, `roomve`.
- Working directory = the account's space. Use relative paths: `renders/shot.png`, `exports/chair.glb`,
  `images/wood.png`.
- Value back to you: assign `result = …` or end the code with an expression. `print()` comes back too.
- A new session is an **empty scene**: no cube, no camera, no light, and `scene.world` is `None`.
- Units are metres, rotations radians, Z is up, 24 fps.
- No window: operators that need a 3D viewport and a mouse (loop cut, knife, sculpt and paint strokes) do not
  work. Everything else does, including edit-mode operators, with the right active object and mode.

## Write code that survives the session

1. **Small steps.** One call per logical step (model a part, add materials, light, render). A 40-line call that
   fails costs little; a 400-line one fails at line 300 with half the scene built.
2. **Look after each step.** `blender_view(views=["persp","front"])` costs a few seconds and catches wrong
   proportions before they are buried under ten more steps.
3. **Names, not variables.** `chair = bpy.data.objects["Chair"]` at the top of each call. Variables of earlier
   calls disappear when the session restarts (the answer then starts with a `Note:`).
4. **Code that can run twice.** Look things up before creating them (`get_object`, `material` in recipe 1). After
   a failure, send only what is missing: what ran before the failing line is already in the scene.
5. **Set the active object yourself** before a `bpy.ops` call (`only(o)` in recipe 1) and go back to object mode
   after edit-mode work. Prefer data access and bmesh to operators when both do the job.
6. **Check instead of assuming**: `roomve.scene_summary()` lists objects, sizes, materials and render settings;
   `[i.name for i in node.inputs]` lists the sockets of a node; `dir(bpy.ops.wm)` lists operators.

## The mistakes that cause most failed calls

| Mistake | Right on Blender 5.2 |
|---|---|
| `'BLENDER_EEVEE_NEXT'` | `'BLENDER_EEVEE'` |
| Rendering in a new session | Create camera, light and world first (recipe 7), or use `blender_view` |
| Cycles with default samples (4096) | `scene.cycles.samples = 64` and a resolution you chose |
| `mesh.use_auto_smooth`, `mesh.calc_normals()` | `bpy.ops.object.shade_auto_smooth(angle=…)`; normals need no call |
| `inputs['Specular']`, `['Emission']`, `['Transmission']`, `['Subsurface']`, `['Clearcoat']` | `'Specular IOR Level'`, `'Emission Color'`, `'Transmission Weight'`, `'Subsurface Weight'`, `'Coat Weight'` |
| `bpy.ops.export_scene.obj`, `export_mesh.stl` | `bpy.ops.wm.obj_export`, `bpy.ops.wm.stl_export` |
| `action.fcurves` | `anim_utils.action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves` |
| `file_format = 'FFMPEG'` | `image_settings.media_type = 'VIDEO'` first |
| `bpy.context.active_object.…` when nothing is active | `bpy.data.objects["Name"]`, then make it active |
| `scene.render.filepath = "shot.png"` (no folder) | `"renders/shot.png"`: a render path needs a folder in it |
| Writing to a folder that does not exist | `os.makedirs("exports", exist_ok=True)` |

When a call fails, the answer carries the traceback and often a `Hint:` line with the exact replacement. Trust
the hint over memory of older Blender versions.

## Budget: time and memory

The instance has a few CPU cores, a memory limit and a time limit per execution (`status` gives the numbers).
Measured on it:

| Work | Time |
|---|---|
| Starting a new session | about 5 s |
| `blender_view`, one 512–768 px view | 3–6 s |
| Cycles, 1280×720, 64 samples, simple scene with a floor | 40–90 s |
| Cycles bake of ambient occlusion, 512 px, 16 samples | about 3 s |
| `roomve.bake_pbr`, five maps at 1024 px | about 25 s |
| Workbench, 24 frames at 640×360 to MP4 | about 10 s |
| EEVEE, first render of a session | about 90 s (shaders compile on the CPU), then fast |

- Cycles time grows with pixels × samples. Double the resolution = four times the time. With denoising on, 32–128
  samples are enough for almost everything. Glass, volumes, many lights and emissive-only lighting need more.
- For a draft, render at `resolution_percentage = 50` first, look, then render the final one.
- A render that may take minutes: pass `timeout_seconds` large enough, and expect a `still running` answer to
  follow with `blender_job`.
- Animations in Cycles: frames × time per frame. Render a range of frames per call to numbered PNG files.
- Memory: each subdivision level multiplies faces by four; an 8K texture takes 256 MB; instances made real copy
  their mesh. Past the limit the instance is stopped and the scene goes back to the last automatic save. Check
  counts with `triangles(o)` (recipe 1) before adding levels.
- EEVEE is worth its start-up time only for many frames. For single images use Cycles; for motion checks
  Workbench.

## PBR materials and texture maps

Materials are the Principled BSDF, so they are PBR from the start. Three helpers of the `roomve` module do the
fiddly parts (recipes 18–20, `help(roomve.bake_pbr)` for every option):

| Need | Call |
|---|---|
| Texture maps of an object's materials (base color, roughness, metallic, normal, AO, emission, alpha), procedural nodes included | `roomve.bake_pbr("Chair", size=1024)` → `{"maps": {"base_color": "textures/Chair_base_color.png", …}}` |
| The same, and the object ready for a game engine (one baked material, one UV layout) | `roomve.bake_pbr("Chair", apply=True)`, then export GLB |
| The packed occlusion-roughness-metallic map | `orm=True` |
| A high-poly sculpt's detail on a low-poly model | `roomve.bake_pbr("Low", maps=("base_color", "normal"), source="High", apply=True)` |
| The textures a model already carries (after importing a GLB or FBX) | `roomve.extract_textures()` |
| Height, normal, roughness and AO from one picture (a generated texture) | `roomve.maps_from_image("images/oak.jpg")` |

Do not write a bake by hand unless these do not fit: a hand-written bake fails in ways that give no error (black
maps from changing an image's colour space after baking, black base color on metals, textures baked onto
overlapping UVs). Maps that hold numbers, not colours (roughness, metallic, normal, AO, height), must be loaded
with `image.colorspace_settings.name = "Non-Color"`. Look at the baked maps in the answer before using them.

## Delivering the result

- Save renders in `renders/`, models in `exports/`, and a `.blend` of the finished scene in the space.
- For a game or a web viewer export `.glb` (`export_format="GLB"`, `export_apply=True`): one file with meshes,
  materials and textures. Say the triangle count and the size of the model.
- Report honestly what you checked: which views you looked at, and what you did not verify.
