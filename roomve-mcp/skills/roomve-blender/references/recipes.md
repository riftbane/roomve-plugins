# Recipes for the Roomve Blender (5.2, headless)

Every block below was run on the Blender of the service (`scripts/test_recipes.py` runs them all, in this order,
before a release). They assume what `blender_python` gives: `bpy`, `bmesh`, `mathutils`, `math`, `os`, `sys`, `np`
and `roomve` already imported, the account's space as working directory, a session that keeps its state.

Copy the helpers you need into the call that uses them: after a restart of the session they are gone.

## 1. Helpers worth defining first

```python
from mathutils import Vector

scene = bpy.context.scene


def get_object(name, make_data=None):
    """The object called `name`; created with make_data() and linked to the scene if it does not exist yet.
    Running the same code twice gives one object, not two."""
    o = bpy.data.objects.get(name)
    if o is None:
        o = bpy.data.objects.new(name, make_data() if make_data else None)
        bpy.context.scene.collection.objects.link(o)
    return o


def only(o):
    """Make `o` the only selected object and the active one: most bpy.ops work on that."""
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for x in bpy.context.selected_objects:
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    return o


def aim(o, target=(0, 0, 0)):
    """Rotate a camera or a light so that it looks at `target` (they look along their -Z axis)."""
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()


def principled(m):
    """The Principled BSDF node of a material (found by type: node names change with the language)."""
    return next(n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")


def material(name, color=(0.8, 0.8, 0.8, 1.0), metallic=0.0, roughness=0.5):
    """A material with that name (reused if it exists) and the three values that matter most."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = principled(m)
    b.inputs["Base Color"].default_value = color
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    return m


def triangles(o):
    """Triangle count of an object with its modifiers applied."""
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    ev.to_mesh_clear()
    return n
```

## 2. Empty the scene

```python
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)   # frees meshes, materials and images nothing uses any more
result = len(bpy.data.objects)
```

## 3. Model: primitives, mesh from data, bmesh

```python
# A primitive: the new object is the active one right after the call. Rotations are in radians.
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.5, depth=0.06, location=(0, 0, 0.75))
top = bpy.context.active_object
top.name = "TableTop"

# A mesh from coordinates: vertices, edges (usually empty) and faces as index tuples.
me = bpy.data.meshes.new("Wedge")
me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 0.5), (0, 1, 0.5)],
               [], [(0, 1, 2, 3), (0, 4, 5, 3), (0, 1, 4), (3, 5, 2), (1, 2, 5, 4)])
me.update()
wedge = get_object("Wedge", lambda: me)
wedge.location = (2, 0, 0)

# bmesh: build or edit geometry without edit mode and without a selection.
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=0.08)
bmesh.ops.scale(bm, vec=(1, 1, 9), verts=bm.verts)
bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.008, segments=2, affect="EDGES")
leg_mesh = bpy.data.meshes.new("Leg")
bm.to_mesh(leg_mesh)
bm.free()
for i, (x, y) in enumerate([(0.3, 0.3), (-0.3, 0.3), (0.3, -0.3), (-0.3, -0.3)]):
    leg = get_object(f"Leg{i}", lambda: leg_mesh)     # four objects, one shared mesh
    leg.location = (x, y, 0.36)
    leg.parent = top
    leg.matrix_parent_inverse = top.matrix_world.inverted()   # keep the leg where it is when parenting

result = [o.name for o in scene.objects]
```

To change an existing mesh: `bm = bmesh.new(); bm.from_mesh(o.data); …; bm.to_mesh(o.data); bm.free();
o.data.update()`.

## 4. Edit-mode operators (they work without a window, with the right context)

```python
o = only(bpy.data.objects["Wedge"])
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.subdivide(number_cuts=2)
bpy.ops.mesh.remove_doubles(threshold=0.0001)       # "merge by distance"
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")              # always go back: object operators need object mode
result = len(o.data.vertices)
```

Loop cut, knife, sculpt and paint strokes need a 3D viewport and a mouse: they do not work here. Use bmesh
(`bmesh.ops.subdivide_edges`, `bmesh.ops.bisect_plane`) or modifiers.

## 5. Modifiers, booleans, smooth shading

```python
o = only(bpy.data.objects["TableTop"])

# Boolean: cut a hole with another object, apply, remove the cutter.
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.4, location=(0, 0, 0.75))
cutter = bpy.context.active_object
cutter.name = "Cutter"
only(o)
cut = o.modifiers.new("Hole", "BOOLEAN")
cut.operation, cut.object, cut.solver = "DIFFERENCE", cutter, "EXACT"    # solvers: EXACT, FLOAT, MANIFOLD
bpy.ops.object.modifier_apply(modifier=cut.name)        # needs o active, in object mode
bpy.data.objects.remove(cutter, do_unlink=True)

# Rounded edges that shade well: bevel, smooth shading, and weighted normals so that the large flat faces
# stay flat (without it, smooth shading leaves dark stains on big n-gons such as this top with a hole).
bev = o.modifiers.new("Bevel", "BEVEL")
bev.width, bev.segments = 0.01, 3
bpy.ops.object.shade_smooth()
wn = o.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
wn.keep_sharp = True
# Alternative for organic shapes: bpy.ops.object.shade_auto_smooth(angle=math.radians(40)) keeps only the edges
# sharper than the angle (it adds a "Smooth by Angle" modifier). mesh.use_auto_smooth does not exist any more.

# Others that are set the same way: SUBSURF (levels, render_levels), MIRROR (use_axis[0] = True),
# SOLIDIFY (thickness), DECIMATE (ratio), TRIANGULATE, WELD (merge_threshold), DISPLACE, SCREW.
sub = bpy.data.objects["Wedge"].modifiers.new("Subdivision", "SUBSURF")
sub.levels = sub.render_levels = 1                      # each level multiplies the faces by 4: stay at 1–3
result = {"table_top_triangles": triangles(o), "wedge_triangles": triangles(bpy.data.objects["Wedge"])}
```

## 6. Materials: colour, image texture, bump, emission, glass, transparency

```python
wood = material("Wood", color=(0.45, 0.26, 0.12, 1.0), roughness=0.6)
steel = material("Steel", color=(0.6, 0.6, 0.62, 1.0), metallic=1.0, roughness=0.25)

top = bpy.data.objects["TableTop"]
top.data.materials.clear()
top.data.materials.append(wood)
bpy.data.objects["Leg0"].data.materials.clear()         # the four legs share this mesh
bpy.data.objects["Leg0"].data.materials.append(steel)

# An image of the space as colour, and the same image as bump. Image paths are relative to the space.
if os.path.exists("images/wood.png"):
    tree = wood.node_tree
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load("images/wood.png", check_existing=True)
    tree.links.new(tex.outputs["Color"], principled(wood).inputs["Base Color"])
    bump = tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2
    tree.links.new(tex.outputs["Color"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], principled(wood).inputs["Normal"])
    # For maps that are data, not colour (roughness, normal, height): image.colorspace_settings.name = "Non-Color"

glow = material("Glow", color=(1, 1, 1, 1))
principled(glow).inputs["Emission Color"].default_value = (1.0, 0.5, 0.1, 1.0)
principled(glow).inputs["Emission Strength"].default_value = 8.0

glass = material("Glass", color=(1, 1, 1, 1), roughness=0.0)
principled(glass).inputs["Transmission Weight"].default_value = 1.0
principled(glass).inputs["IOR"].default_value = 1.45

ghost = material("Ghost", color=(0.2, 0.6, 1.0, 1.0))
principled(ghost).inputs["Alpha"].default_value = 0.4
ghost.surface_render_method = "BLENDED"                 # EEVEE: BLENDED or DITHERED (Cycles needs nothing)
result = [m.name for m in bpy.data.materials]
```

A mesh needs UVs for an image texture: primitives have them; for your own meshes see recipe 9.

## 7. Camera, light, world (a new scene has none of them)

```python
cam = get_object("Camera", lambda: bpy.data.cameras.new("Camera"))
cam.location = (2.2, -2.4, 1.6)
cam.data.lens = 50
aim(cam, (0, 0, 0.5))
scene.camera = cam                                      # without this: "Cannot render, no camera"

sun = get_object("Sun", lambda: bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0                                   # sun: W/m² (2–5 is daylight); point, spot, area: W
sun.data.angle = math.radians(3)                        # larger angle = softer shadows
sun.location = (4, -3, 6)
aim(sun, (0, 0, 0))

fill = get_object("Fill", lambda: bpy.data.lights.new("Fill", "AREA"))
fill.data.energy, fill.data.size = 150, 2.0
fill.location = (-3, -2, 2.5)
aim(fill, (0, 0, 0.5))

if scene.world is None:                                 # scene.world is None in a new session
    scene.world = bpy.data.worlds.new("World")
bg = next(n for n in scene.world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.75, 0.8, 0.9, 1.0)
bg.inputs["Strength"].default_value = 0.6               # the world lights the shadows: 0 gives black shadows

# A floor, so that the object casts a shadow and does not float in a void.
floor = get_object("Floor", lambda: bpy.data.meshes.new("Floor"))
if not floor.data.polygons:
    floor.data.from_pydata([(-10, -10, 0), (10, -10, 0), (10, 10, 0), (-10, 10, 0)], [], [(0, 1, 2, 3)])
    floor.data.update()
    floor.data.materials.append(material("FloorGrey", color=(0.55, 0.55, 0.55, 1.0), roughness=0.9))
result = {"camera": scene.camera.name, "lights": [o.name for o in scene.objects if o.type == "LIGHT"]}
```

To frame what is selected instead of placing the camera by hand: select the objects, then
`bpy.ops.view3d.camera_to_view_selected()` (it moves `scene.camera`; it needs one to exist).

## 8. Render a still

```python
scene.render.engine = "CYCLES"                  # 'CYCLES', 'BLENDER_EEVEE' or 'BLENDER_WORKBENCH'
scene.cycles.samples = 64                       # the default is 4096: ALWAYS set it. 32–128 is plenty with denoising
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.resolution_percentage = 100
scene.render.film_transparent = False           # True: transparent background (use color_mode 'RGBA')
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.view_settings.view_transform = "AgX"      # default; "Standard" keeps flat colours exactly as set
scene.render.filepath = "renders/table.png"     # relative to the space; the folder is created
bpy.ops.render.render(write_still=True)         # the answer shows a preview of the file
result = os.path.getsize("renders/table.png")
```

Quick looks do not need any of this: `blender_view`, or in code
`roomve.view(views=("persp", "front"), size=768, out_dir="renders", prefix="table")`, which returns the paths.

### Alternative lighting: an HDRI that ships with Blender

Reflections on metal and glass look much better with an environment than with a flat colour. Eight come with
Blender, no download needed: `city`, `courtyard`, `forest`, `interior`, `night`, `studio`, `sunrise`, `sunset`. The
environment is also what the camera sees behind the object: set `scene.render.film_transparent = True` to leave it
out of the picture.

```python
hdri = os.path.join(bpy.utils.resource_path("LOCAL"), "datafiles", "studiolights", "world", "studio.exr")
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
tree = world.node_tree
bg = next(n for n in tree.nodes if n.bl_idname == "ShaderNodeBackground")
env = tree.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(hdri, check_existing=True)
tree.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0
result = env.image.name
```

## 9. UV unwrap and bake to an image

```python
o = only(bpy.data.objects["Wedge"])
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")

m = material("WedgeBaked")
o.data.materials.clear()
o.data.materials.append(m)
target = bpy.data.images.new("wedge_ao", 512, 512)
node = m.node_tree.nodes.new("ShaderNodeTexImage")
node.image = target
m.node_tree.nodes.active = node                 # the bake writes into the ACTIVE image node of each material

scene.render.engine = "CYCLES"                  # baking is Cycles only
scene.cycles.samples = 16
bpy.ops.object.bake(type="AO")                  # also: 'DIFFUSE', 'ROUGHNESS', 'NORMAL', 'EMIT', 'COMBINED'
os.makedirs("textures", exist_ok=True)
target.filepath_raw = os.path.abspath("textures/wedge_ao.png")
target.file_format = "PNG"
target.save()
result = os.path.exists("textures/wedge_ao.png")
```

## 10. Import and export

```python
os.makedirs("exports", exist_ok=True)           # not every exporter creates the folder
only(bpy.data.objects["TableTop"])
for child in bpy.data.objects["TableTop"].children:
    child.select_set(True)

bpy.ops.export_scene.gltf(filepath="exports/table.glb", export_format="GLB", use_selection=True,
                          export_apply=True)    # export_apply: with modifiers applied
bpy.ops.export_scene.fbx(filepath="exports/table.fbx", use_selection=True)
bpy.ops.wm.obj_export(filepath="exports/table.obj", export_selected_objects=True)
bpy.ops.wm.stl_export(filepath="exports/table.stl", export_selected_objects=True)
bpy.ops.wm.usd_export(filepath="exports/table.usdc", selected_objects_only=True)

# Import: the imported objects are the selected ones afterwards.
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath="exports/table.glb")
imported = [o for o in bpy.data.objects if o not in before]
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)
# Other importers: bpy.ops.import_scene.fbx, bpy.ops.wm.obj_import, bpy.ops.wm.stl_import,
# bpy.ops.wm.ply_import, bpy.ops.wm.usd_import, bpy.ops.wm.alembic_import, bpy.ops.import_curve.svg
result = sorted(os.listdir("exports"))
```

## 11. Save the work as a .blend

```python
bpy.ops.wm.save_as_mainfile(filepath="table.blend")     # in the space; pass copy=True to keep the current file name
result = bpy.data.filepath
```

## 12. Armature, automatic weights, pose keyframes, f-curves

```python
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.1, depth=2, location=(4, 0, 1))
arm_mesh = bpy.context.active_object
arm_mesh.name = "Tentacle"
only(arm_mesh)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.subdivide(number_cuts=6)           # bending needs geometry along the length
bpy.ops.object.mode_set(mode="OBJECT")

rig = get_object("Rig", lambda: bpy.data.armatures.new("Rig"))
rig.location = (4, 0, 0)
only(rig)
bpy.ops.object.mode_set(mode="EDIT")            # bones are created in edit mode, as edit_bones
prev = None
for i in range(3):
    b = rig.data.edit_bones.new(f"Seg{i}")
    b.head, b.tail = (0, 0, i * 0.66), (0, 0, (i + 1) * 0.66)
    if prev:
        b.parent, b.use_connect = prev, True
    prev = b
bpy.ops.object.mode_set(mode="OBJECT")

arm_mesh.select_set(True)                       # children selected, the armature active
bpy.ops.object.parent_set(type="ARMATURE_AUTO") # automatic weights

scene.frame_start, scene.frame_end = 1, 48
scene.render.fps = 24
tip = rig.pose.bones["Seg2"]
tip.rotation_mode = "XYZ"
for frame, angle in ((1, -0.6), (24, 0.6), (48, -0.6)):
    tip.rotation_euler.x = angle
    tip.keyframe_insert("rotation_euler", frame=frame)

# Reading or editing the curves: actions are layered in Blender 5.x, action.fcurves does not exist.
from bpy_extras import anim_utils
action = rig.animation_data.action
bag = anim_utils.action_get_channelbag_for_slot(action, rig.animation_data.action_slot)
for fc in bag.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "BEZIER"
result = [(fc.data_path, fc.array_index, len(fc.keyframe_points)) for fc in bag.fcurves]
```

Bone layers and bone groups are gone: use `rig.data.collections.new("Deform").assign(rig.data.bones["Seg0"])`.
Shape keys: `o.shape_key_add(name="Basis")`, then `key = o.shape_key_add(name="Smile")` and move
`key.data[i].co`.

## 13. Render an animation to a video

```python
scene.render.engine = "BLENDER_WORKBENCH"       # flat and fast: fine for motion checks. Cycles: frames × seconds per frame
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.frame_start, scene.frame_end = 1, 24
settings = scene.render.image_settings
settings.media_type = "VIDEO"                   # first this: file_format then becomes 'FFMPEG'
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.filepath = "renders/tentacle.mp4"
bpy.ops.render.render(animation=True)
settings.media_type = "IMAGE"                   # back to stills for the next render
settings.file_format = "PNG"
result = os.path.getsize("renders/tentacle.mp4")
```

For a long Cycles animation render a few frames per call (`scene.frame_start`/`frame_end`) to numbered PNG files
(`scene.render.filepath = "renders/frames/f_"`), so no call hits the time limit and nothing is lost on a stop.

## 14. Geometry nodes

```python
tree = bpy.data.node_groups.new("Scatter", "GeometryNodeTree")
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")   # not tree.inputs
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
n_in = tree.nodes.new("NodeGroupInput")
n_out = tree.nodes.new("NodeGroupOutput")
points = tree.nodes.new("GeometryNodeDistributePointsOnFaces")
points.inputs["Density"].default_value = 40.0
cube = tree.nodes.new("GeometryNodeMeshCube")
cube.inputs["Size"].default_value = (0.05, 0.05, 0.2)
place = tree.nodes.new("GeometryNodeInstanceOnPoints")
realize = tree.nodes.new("GeometryNodeRealizeInstances")
link = tree.links.new
link(n_in.outputs["Geometry"], points.inputs["Mesh"])
link(points.outputs["Points"], place.inputs["Points"])
link(cube.outputs["Mesh"], place.inputs["Instance"])
link(place.outputs["Instances"], realize.inputs["Geometry"])
link(realize.outputs["Geometry"], n_out.inputs["Geometry"])

bpy.ops.mesh.primitive_plane_add(size=2, location=(-4, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
mod = ground.modifiers.new("Scatter", "NODES")
mod.node_group = tree
result = triangles(ground)                      # the evaluated object is the scattered cubes
```

Socket names differ between nodes and versions: print `[s.name for s in node.inputs]` before linking a node you
have not used in this session.

## 15. Text, curves, collections

```python
bpy.ops.object.text_add(location=(0, 3, 0))
label = bpy.context.active_object
label.name = "Label"
label.data.body = "Roomve"
label.data.extrude = 0.05
label.data.align_x = "CENTER"
bpy.ops.object.convert(target="MESH")           # text to mesh, e.g. before exporting

curve = bpy.data.curves.new("Pipe", "CURVE")
curve.dimensions = "3D"
spline = curve.splines.new("POLY")
spline.points.add(2)                            # a new spline has one point already
for p, co in zip(spline.points, [(0, 0, 0), (1, 0, 0.5), (2, 0, 0)]):
    p.co = (*co, 1.0)                           # x, y, z, w
curve.bevel_depth = 0.03                        # gives the curve a round section: a pipe
pipe = get_object("Pipe", lambda: curve)
pipe.location = (0, -3, 0)

props = bpy.data.collections.get("Props") or bpy.data.collections.new("Props")
if props.name not in scene.collection.children:
    scene.collection.children.link(props)
for o in (label, pipe):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    props.objects.link(o)
result = [o.name for o in props.objects]
```

## 16. A Python package that Blender does not have

```python
import subprocess
target = os.path.abspath("pylibs")              # inside the space: it survives restarts of the session
subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                "--target", target, "tomli-w"], check=True)
if target not in sys.path:
    sys.path.insert(0, target)                  # do this again after a restart of the session
import tomli_w
result = tomli_w.__name__
```

`pip install --user` installs where this Blender does not look: use `--target`.

## 17. Convert an image file (EXR, HDR, TIFF… to PNG)

```python
src = os.path.join(bpy.utils.resource_path("LOCAL"), "datafiles", "studiolights", "world", "sunset.exr")
img = bpy.data.images.load(src, check_existing=True)
os.makedirs("images", exist_ok=True)
img.save_render(os.path.abspath("images/sunset.png"))   # through the scene's colour management, as a render would be
result = os.path.getsize("images/sunset.png")
```

`generate_image` and `edit_image` read PNG, JPEG and WEBP references: convert anything else this way first.
