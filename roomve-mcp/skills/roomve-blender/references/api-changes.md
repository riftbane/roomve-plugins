# Blender 5.2 for people who learned an older Blender

Most Blender Python found around was written for 2.8–4.x. These are the differences that break it on the 5.2 of
the service. Every row was checked on Blender 5.2.3: the middle column is the error the old code gives.

## Rendering

| Old code | What happens on 5.2 | Write this |
|---|---|---|
| `scene.render.engine = 'BLENDER_EEVEE_NEXT'` | `enum "BLENDER_EEVEE_NEXT" not found` | `'BLENDER_EEVEE'`. The three engines are `'BLENDER_EEVEE'`, `'BLENDER_WORKBENCH'`, `'CYCLES'`. |
| Rendering right after starting | `Cannot render, no camera` | A new session is an empty scene: no camera, no light, `scene.world is None`. Create them (recipe 7). |
| Cycles with its defaults | No error, but 4096 samples at 1920×1080: minutes to hours on CPU | Always set `scene.cycles.samples` (32–128) and the resolution. |
| `scene.eevee.use_bloom`, `use_ssr`, `use_gtao`, `use_soft_shadows` | `'SceneEEVEE' object has no attribute …` | Removed. What exists: `taa_render_samples`, `use_raytracing`, `use_shadows`, `shadow_ray_count`. |
| `image_settings.file_format = 'FFMPEG'` | `enum "FFMPEG" not found` | `image_settings.media_type = 'VIDEO'` first (recipe 13). |
| `scene.node_tree` (compositor), `scene.use_nodes = True` | `'Scene' object has no attribute 'node_tree'` | `scene.compositing_node_group = bpy.data.node_groups.new("Comp", "CompositorNodeTree")`; its output is a `NodeGroupOutput` with an Image socket in `tree.interface`. |
| `view_settings.look = 'High Contrast'` | `enum … not found` | With the default view transform AgX the looks are `'None'`, `'AgX - Punchy'`, `'AgX - High Contrast'`, … View transforms: `'AgX'` (default), `'Standard'`, `'Filmic'`, `'Khronos PBR Neutral'`, `'Raw'`. |
| Sky texture `sky_type = 'NISHITA'` | `enum "NISHITA" not found` | `'MULTIPLE_SCATTERING'` (default), `'SINGLE_SCATTERING'`, `'PREETHAM'`, `'HOSEK_WILKIE'`. |

## Materials and nodes

| Old code | What happens on 5.2 | Write this |
|---|---|---|
| `mat.use_nodes = True` | Works, with `DeprecationWarning: 'Material.use_nodes' is expected to be removed in Blender 6.0` | Nothing: a new material and a new world already have a node tree (Principled BSDF + output; Background + output). |
| `bsdf.inputs['Specular']`, `['Subsurface']`, `['Transmission']`, `['Clearcoat']`, `['Sheen']`, `['Emission']` | `KeyError: … key "Specular" not found` | `'Specular IOR Level'`, `'Subsurface Weight'`, `'Transmission Weight'`, `'Coat Weight'`, `'Sheen Weight'`, `'Emission Color'` (+ `'Emission Strength'`). |
| `mat.shadow_method`, `mat.blend_method = 'BLEND'` | `shadow_method`: no such attribute | `mat.surface_render_method = 'BLENDED'` or `'DITHERED'`. |
| `nodes['Principled BSDF']` | Works on a new material in English, breaks on imported or renamed nodes | Find nodes by type: `next(n for n in tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')`. |
| `tree.inputs.new(...)`, `tree.outputs.new(...)` on a node group | `'GeometryNodeTree' object has no attribute 'inputs'` | `tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")`. |

The inputs of the Principled BSDF in 5.2: Base Color, Metallic, Roughness, IOR, Alpha, Normal, Weight, Diffuse
Roughness, Subsurface Weight / Radius / Scale / IOR / Anisotropy, Specular IOR Level, Specular Tint, Anisotropic,
Anisotropic Rotation, Tangent, Transmission Weight, Coat Weight / Roughness / IOR / Tint / Normal, Sheen Weight /
Roughness / Tint, Emission Color, Emission Strength, Thin Film Thickness, Thin Film IOR, Thin Wall.

## Meshes

| Old code | What happens on 5.2 | Write this |
|---|---|---|
| `mesh.use_auto_smooth = True`, `mesh.auto_smooth_angle` | `'Mesh' object has no attribute 'use_auto_smooth'` | `bpy.ops.object.shade_auto_smooth(angle=math.radians(30))` on the active object (adds a "Smooth by Angle" modifier), or `mesh.shade_smooth()`. |
| `mesh.calc_normals()` | no such attribute | Nothing: normals are computed when needed. Read `mesh.vertex_normals`, `mesh.polygon_normals`, `mesh.corner_normals`. |
| `bpy.ops.mesh.merge_by_distance()` | operator could not be found | `bpy.ops.mesh.remove_doubles(threshold=0.0001)` in edit mode, or a `WELD` modifier. |
| `bpy.ops.object.decimate(...)` | operator could not be found | A `DECIMATE` modifier (`ratio`), then `bpy.ops.object.modifier_apply`. |
| Boolean `solver = 'FAST'` | `enum "FAST" not found` | `'EXACT'` (default), `'FLOAT'`, `'MANIFOLD'`. |
| `bpy.ops.mesh.loopcut_slide(...)`, knife, sculpt and paint strokes | `{'CANCELLED'}` or a context error: they need a 3D viewport and a mouse | bmesh (`bmesh.ops.subdivide_edges`, `bmesh.ops.bisect_plane`) or modifiers. |

Still fine: `mesh.from_pydata`, `mesh.update()`, `mesh.validate()`, `mesh.uv_layers.new()`,
`mesh.color_attributes`, `mesh.calc_loop_triangles()`, `polygon.use_smooth`, `bpy.ops.object.shade_smooth()`,
edit-mode operators (subdivide, bevel, inset, extrude, smart UV project, recalculate normals) and the transform
operators.

## Import and export

| Old code | What happens on 5.2 | Write this |
|---|---|---|
| `bpy.ops.export_scene.obj`, `bpy.ops.import_scene.obj` | operator could not be found | `bpy.ops.wm.obj_export(filepath=…, export_selected_objects=True)`, `bpy.ops.wm.obj_import(filepath=…)` |
| `bpy.ops.export_mesh.stl`, `bpy.ops.import_mesh.stl` | operator could not be found | `bpy.ops.wm.stl_export`, `bpy.ops.wm.stl_import` |
| `bpy.ops.export_mesh.ply`, `bpy.ops.import_mesh.ply` | operator could not be found | `bpy.ops.wm.ply_export`, `bpy.ops.wm.ply_import` |
| `bpy.ops.wm.collada_export` / `_import` (`.dae`) | operator could not be found | Collada was removed. Use glTF, FBX, OBJ or USD. |

Unchanged: `bpy.ops.export_scene.gltf`, `bpy.ops.import_scene.gltf`, `bpy.ops.export_scene.fbx`,
`bpy.ops.import_scene.fbx`, `bpy.ops.wm.usd_export` / `usd_import`, `bpy.ops.wm.alembic_export` / `alembic_import`,
`bpy.ops.import_curve.svg`.

## Animation and rigs

| Old code | What happens on 5.2 | Write this |
|---|---|---|
| `action.fcurves` | `'Action' object has no attribute 'fcurves'` | Actions have layers and slots: `from bpy_extras import anim_utils`; `bag = anim_utils.action_get_channelbag_for_slot(action, obj.animation_data.action_slot)`; `bag.fcurves`. Inserting keys is unchanged (`obj.keyframe_insert("location", frame=1)`). |
| `bone.layers[i] = True`, `armature.layers` | `'Bone' object has no attribute 'layers'` | Bone collections: `coll = armature.collections.new("Deform")`; `coll.assign(bone)`. |
| `pose.bone_groups` | no such attribute | Bone collections, and `bone.color` for colours. |
| `bpy.ops.object.gpencil_add()` | operator could not be found | `bpy.ops.object.grease_pencil_add(type='EMPTY')` (the object type is `GREASEPENCIL`). |

## Things that are not errors but surprise

- The scene of a new session is **empty**: no cube, no camera, no light, no world.
- `bpy.context.active_object` is `None` when nothing is active (after deleting the active object, after a
  restart). Fetch objects by name.
- A relative path given to an operator or to `scene.render.filepath` is relative to the account's space. `//` at
  the start of a path means "next to the .blend file" and only has a meaning once the scene was saved.
- **A render path needs a folder in it.** `scene.render.filepath = "renders/shot.png"` works and creates the
  folder; a bare `"shot.png"` fails with `Render error (No such file or directory) cannot save`.
- `bpy.ops.wm.save_as_mainfile` needs the folder to exist; the glTF exporter and the renderer create it.
- `pip install --user` puts packages where this Blender does not look: use `--target` (recipe 16).
- Add-ons that ship with Blender but are off: `import addon_utils; addon_utils.enable("rigify")` (also
  `node_wrangler`). The glTF, FBX, SVG and BVH importers and exporters are on.
