---
name: roomve-images
description: Get the image the person wants from Roomve MCP's generate_image and edit_image at the first try. The generator is general purpose - illustrations, photos, icons, logos, posters, UI mockups, characters, sprites, concept art, textures - not only material for 3D work. Covers which model supports which sizes and aspect ratios (the usual cause of rejected calls), how reference images, edits and transparent backgrounds work, how files are named, how to write prompts that give a consistent set, what to do when a generation is blocked or fails, and how to use an image in Blender or a Blender render as a reference. Use it BEFORE calling generate_image or edit_image and whenever one of them returns an error.
---

# Images in Roomve MCP

`generate_image` and `edit_image` call Google Gemini image models ("Nano Banana"). They are free to use for
anything the person asks: a birthday card, a logo, a product photo, a game sprite, a storyboard, a texture. Read
**roomve-mcp** first for the storage space and the files.

## Parameters that are rejected if they do not match the model

| `model` | Sizes (`image_size`) | Aspect ratios | Notes |
|---|---|---|---|
| `gemini-3.1-flash-image` (default) | `512`, `1K`, `2K`, `4K` | all 14 | Good and quick. The only one with `512`. |
| `gemini-nano-banana-2.1` | `1K`, `2K`, `4K` | all 14 | Newer; cheaper per image than the default at the same size. |
| `gemini-3.1-flash-lite-image` | `1K` only | the 10 standard ones | Fastest and cheapest. |
| `gemini-3-pro-image` | `1K`, `2K`, `4K` | the 10 standard ones | Best quality, slowest, about twice the cost. `thinking` has no effect. |

- Standard ratios: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`.
  Extreme ones, only on the first two models: `1:4`, `4:1`, `1:8`, `8:1` (banners, strips).
- `1K` is about 1024 px on the long side, `2K` about 2048, `4K` about 4096. `512` is for drafts and small icons.
- Leave `model` out unless there is a reason: the default fits most requests.
- `count` 1–4 gives variants of the same prompt in one call. Each one costs.
- `thinking="high"` helps with complex compositions and with text inside the image; it is slower.

Work cheap first: one `512` or `1K` draft to check the idea, then the final size. Every answer reports what the
call cost.

## Where the image goes, and what it is called

- The file is saved in the account's space, in `images/` unless you pass `folder`.
- The name is a slug of the prompt, or `filename` if you pass one (without extension).
- **The extension is decided by the server** from what the model returned: often `.jpg`, `.png` when the
  background is transparent. Never assume `images/name.png`: use the path printed in the answer.
- An existing file is never replaced: the new one gets `-2`, `-3`… With `count` > 1 the names end in `-1`, `-2`…
- The answer shows a downscaled preview. The full file is at the path and at the link in the answer.

## Writing the prompt

Describe the picture, do not list keywords. A good prompt names, in this order:

1. **Subject** and what it is doing.
2. **Style and medium**: flat vector, watercolour, pixel art 32×32, isometric 3D render, studio product photo,
   35 mm film photo, pencil sketch, anime cel shading…
3. **Composition**: framing (close-up, full body, top-down), where the subject sits, what is in the background.
4. **Colours and light**: palette, time of day, soft or hard light, mood.
5. **Text to draw**, in quotes, with where it goes and what kind of lettering: `the word "APERTO" in bold white
   capitals on the sign`.

Say what must not be there only when it matters ("no text", "no people"). For several images of one set, repeat
the same style sentence word for word and pass a finished image of the set in `reference_images`.

## Reference images and edits

- `reference_images` are **paths of the space**: generated images, files the person uploaded, or Blender
  renders. Up to 14. Say in the prompt what each one is for ("the character of the first image, in the pose of
  the second").
- Readable formats: PNG, JPEG, WEBP (GIF, BMP and TIFF are converted). Not EXR or HDR. Up to 25 megapixels and
  40 MB each.
- `edit_image(image=…, prompt=…)` changes an existing image and saves the result as a **new file**: the source
  stays. Say what to change and what to keep: `make the jacket red, keep the face, the pose and the background
  identical`. Without `aspect_ratio` the result keeps the shape of the source.
- For small fixes edit the last result instead of generating again: it keeps what was already right.
- A file of the person's computer must be brought into the space first (see **roomve-mcp**, "Getting files").

## Transparent background

`transparent_background=true` returns a PNG with alpha. The model paints the subject on flat magenta and the
server removes the magenta. So:

- It works for things with a clear outline: icons, logos, stickers, sprites, objects, characters.
- It works badly for smoke, glows, glass, hair against light, soft shadows on the ground. Ask for a plain
  background instead and say so.
- Do not ask for a pink, magenta or purple subject: it would be cut out with the background.
- If the answer says the model did not paint the magenta background, call again once; if it fails again, generate
  without transparency.

## When a call fails

| The answer says | Do this |
|---|---|
| `image_size … not supported by …` or `aspect_ratio … not supported by …` | Pick a combination from the table above. |
| `reference image not found or not readable: …` | `list_files` for the real path and extension. |
| `… is not an image Gemini can read` | Convert the file to PNG or JPEG (in Blender: load it and save it as PNG), then pass that. |
| `the reference images are too heavy: use fewer` | Pass fewer references. |
| `prompt blocked by Gemini (…)` or `image blocked by Gemini (…)` | Rephrase: the same prompt gives the same refusal. Say plainly to the person that the model refused, and why if a reason is given. |
| `no image was generated` | Call again once with a more concrete prompt. |
| `Gemini is not available or the rate limit was reached` | Wait a minute, call again once. |
| `the call to Gemini timed out` | Call again; it may have been billed. |
| `The storage space of the account is full` | Free space (see **roomve-mcp**). |

Do not repeat a failing call unchanged more than once, and do not generate many variants to hide a prompt that
is not working: fix the prompt.

## Images and Blender, both ways

- **Image → Blender.** A generated image is a file of the same space Blender works in:
  `bpy.data.images.load("images/oak.jpg")` (use the real path from the answer). For a texture ask for
  `seamless tileable texture, top-down, even flat lighting, no shadows, no perspective`. For a decal or a label
  use `transparent_background`. See recipe 6 of **roomve-blender** for the material.
- **Concept → model.** Generate a reference sheet first (`front view and side view of the same object, side by
  side, orthographic, plain white background, no perspective`), look at it, then model. It settles proportions
  before any geometry exists.
- **Blender → image.** `blender_view` does not save files. To use a render as a reference, save it from code
  (`roomve.view(views=("persp",), size=1024, out_dir="renders", prefix="chair")` or a real render), then pass
  `renders/chair_persp.png` in `reference_images`: "render this object as a product photo on a marble table".
