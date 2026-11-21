---
name: roomve-mcp
description: How to use the Roomve MCP connector (mcp.roomve.it) without wasted calls - image generation with Gemini and a personal headless Blender driven by free Python, sharing one storage space per account. Use it BEFORE the first Roomve tool call of a conversation (generate_image, edit_image, blender_python, blender_view, blender_job, blender_control, status, list_files, get_file, create_upload_url, delete_files, list_generations) and whenever a Roomve tool answers with an error, "still running", a queue message, a timeout, an out-of-memory stop, a full-storage message or a note that the session was restarted. It explains the session model, the one-at-a-time queue, paths and files, how to move files in and out, and what to do for each error.
---

# Roomve MCP: how to work with it

Roomve MCP gives the account behind the connector two generators and one storage space.

| Generator | Tools | What it is |
|---|---|---|
| Images | `generate_image`, `edit_image` | Google Gemini image models. Any subject and style: illustrations, photos, icons, logos, concept art, UI mockups, sprites, textures. Not limited to 3D work. |
| Blender | `blender_python`, `blender_view`, `blender_job`, `blender_control` | A private headless Blender 5.2. You send Python, it runs with the whole `bpy` API. No rules, no fixed pipeline. Models, PBR materials and their texture maps, rigs, animation, renders, import and export. |
| Space | `list_files`, `get_file`, `create_upload_url`, `delete_files`, `list_generations`, `status` | One private folder per account with a quota. Both generators read and write there. |
| Projects | `list_projects`, `project_files`, `project_read`, `project_write`, `project_pull`, `project_push`, `project_move`, `project_rename`, `project_delete`, `project_upload_url` | The projects of Roomve Workspace the person belongs to: a shared folder per project (assets, documents) and the names of its GitHub repos. Files move between a project and the space with `project_pull` and `project_push`. |
| Tasks | `project_tasks`, `task_read`, `task_create`, `task_update`, `task_comment`, `task_delete`, `epic_create`, `epic_update`, `epic_delete` | The to-do list of a project (tasks with comments) and its roadmap (epics), written as the person. See **roomve-projects**. |
| Wiki | `wiki_pages`, `wiki_read`, `wiki_create`, `wiki_update`, `wiki_delete`, `wiki_publication`, `wiki_publish`, `wiki_domain` | The wiki of a project (lore, world, rules): pages in Markdown with images and maps, and its publication as a website on the person's domain. See **roomve-projects**. |
| Site | `site_status`, `site_deploy`, `site_domain`, `site_backend` | The website of a project (static files, and a Node.js backend with SQLite), from a folder of the project, on the person's domain. See **roomve-projects**. |
| Releases | `dist_status`, `dist_configure` | The GitHub releases of a linked repo served to programs (channels, platforms, access). See **roomve-projects**. |

Before writing Blender code read the skill **roomve-blender**. Before generating images read **roomve-images**.
Before touching a project of Roomve Workspace read **roomve-projects**.

## The five facts that prevent most errors

1. **One folder, relative paths.** Generated images land in `images/`. Blender runs with the account's folder as
   working directory. So `images/wood.png` is the same file for `edit_image`, for `reference_images`, and for
   `bpy.data.images.load("images/wood.png")`. Never use absolute paths, `..`, or names that start with a dot.
2. **The Blender session is a console that stays open.** Scene, variables, imports and functions persist between
   calls. Build in small steps and look at the result (`blender_view`) between steps.
3. **The session can restart, and then only the scene comes back.** After about 15 minutes idle, a crash, a
   timeout or an out-of-memory stop, the next call starts a new Blender and reopens the last saved scene. Python
   variables and functions are gone. The answer starts with `Note: A new Blender process was started…` when this
   happened. So: fetch objects by name (`bpy.data.objects["Chair"]`), not from variables of earlier calls, and
   define a helper again in the call that uses it.
4. **A failed call may have done half its work.** Code runs top to bottom until the exception: objects created
   before the failing line exist. Do not resend the whole script: fix and send only what is missing, or write code
   that can run twice (look an object up by name before creating it).
5. **One Blender execution at a time per account.** A second call waits for the first. Never send the same work
   twice because the first call is slow.

## Long work: wait, do not resubmit

`blender_python` and `blender_view` wait up to `wait_seconds` (default 180). If the work is not finished they
answer:

```
Job #42 is still running after 180 s. Nothing is lost: call blender_job(job_id=42) to wait for the result.
```

Then call `blender_job(job_id=42)`, again and again if needed. The job keeps running on the server whatever the
client does, and its result is kept. A job that says `waiting for its turn` is queued behind another execution of
the same account (maybe from another chat of the same person): wait for it the same way.

- Each execution has a time limit, `timeout_seconds` (default 600, see `status` for the maximum). Past it Blender
  is stopped and the scene goes back to the last automatic save. For a heavy render pass a longer
  `timeout_seconds` up front instead of discovering the limit.
- To stop something that is running: `blender_control(action="cancel")`. To start over from an empty scene:
  `blender_control(action="reset")` (the files in the space are kept; the saved scene and the queue are dropped).
- `status` tells the limits that apply now (memory and CPU of the instance, time limit, storage used).

## Looking at what you made

- `blender_view(views=["persp","front"])` renders quick views with its own camera and light and shows them. It
  changes nothing in the scene and saves nothing in the space. Use it after every modeling or material step.
- `blender_python` shows a preview of the image files the code wrote (up to four), so a render saved by the code
  is visible in the answer without another call.
- Previews are downscaled. The real file is the one in the space.

## Getting files to the person, and from the person

Results list every file written, with a download link (valid 7 days).

**A file attached to the chat is not in the space.** The tools receive text only: the service never sees an
attachment (a `.blend`, a model, a picture), and you cannot pass its content through a tool. To work on a file
it must be put in the space in one of these ways:

- **You have a shell (Claude Code):** save a file into the project with
  `curl -fsSL "<url>" -o path/in/project.glb`. Bring a local file in with `create_upload_url(path="uploads/ref.png")`
  and run the `curl -T` command it returns (the link lasts 15 minutes).
- **You have no shell (a chat):** give the person the link, or tell them the file is on the website
  (`https://mcp.roomve.it`, page File). To bring a file in, ask the person to upload it from that page (drag it
  in, up to 500 MB), then find it with `list_files`. Do not pretend to run curl.
- **The chat has a code sandbox that holds the attachment:** the same `curl -T` works only if the sandbox is
  allowed to reach `mcp.roomve.it`, which is off unless the person or their organization enabled it. Try once;
  if the connection is refused, ask for the upload from the website.
- **The file is at a link** the person gives (a share link of a cloud drive, a public URL): Blender can fetch it,
  with `urllib.request.urlretrieve(url, "uploads/model.blend")` in `blender_python` (create `uploads/` first).
- Once it is there, a `.blend` opens with `bpy.ops.wm.open_mainfile(filepath="uploads/model.blend")`, other
  models with the importers: see **roomve-blender**, "Working on a .blend the person already has".
- Never rebuild a file from a preview and never paste file contents back through a tool: always move the file
  itself.
- `get_file(path)` gives a fresh link for any file of the space, and a preview if it is an image.

The space has a quota. `delete_files` frees room; ask the person before deleting things they may still want.

## What each answer means and what to do

| The answer says | Do this |
|---|---|
| `Job #N is still running after …` | `blender_job(job_id=N)`. Do not resubmit. |
| `Job #N is waiting for its turn …` | Same. If the running job is unwanted: `blender_control(action="cancel")`. |
| `Note: A new Blender process was started and the scene saved at … was reopened` | Normal after idle time. Variables are gone: look objects up by name, define helpers again. Check the scene with `blender_view` or `roomve.scene_summary()` if work since that save may be missing. |
| `Note: … The scene belongs to the file X, but what is open now is the automatic save of the session` | The scene is intact. To save it use `bpy.ops.wm.save_as_mainfile(filepath="X")`; `save_mainfile()` fails until then. |
| `Job #N FAILED` with a traceback | Read the last line and the `Hint:` lines under it: they name the fix for known Blender 5.2 mistakes. Fix only the failing part (fact 4). |
| `The execution went over its time limit` | The work was too heavy for the limit: fewer samples, lower resolution, fewer frames per call, or a longer `timeout_seconds`. The scene is back at the last automatic save. |
| `Blender ran out of memory and was stopped` | Lighter scene: lower subdivision levels, smaller textures, fewer instances made real. The scene is back at the last automatic save. |
| `The storage space of the account is full` | `list_files`, then `delete_files` for what is not needed (ask first), or tell the person to free space on the website. |
| `All N Blender instances are working for other accounts` | The service is full. Tell the person and try again in a few minutes. |
| `Invalid path` | Use a path relative to the space: no leading `/`, no `..`, no names starting with a dot. |
| `No such file or folder` | `list_files` to see the real names. |
| `image_size … not supported by …` / `aspect_ratio … not supported by …` | The model does not have that size or ratio: see the table in **roomve-images**. |
| `prompt blocked by Gemini` / `image blocked by Gemini` | Rephrase the request; sending the same prompt again gives the same refusal. |
| `Gemini is not available or the rate limit was reached` | Wait a minute and call again once. |
| `This account is not available. Connect again from the website.` | Only the person can fix it (the connector must be authorized again, or the account was disabled). Say so and stop. |

## Habits that keep a long task on track

- Give `blender_python` a short `title` ("Model the chair legs"): the person sees it in the history on the site.
- Keep outputs in folders by kind: `images/`, `renders/`, `exports/`, `textures/`, `uploads/`. Create a folder
  before writing in it with `os.makedirs("renders", exist_ok=True)`.
- Save a `.blend` of finished work in the space (`bpy.ops.wm.save_as_mainfile(filepath="chair.blend")`, always
  with the path): the automatic save of the session is a safety net, not a deliverable.
- `list_generations` recalls what was made earlier, with the paths of the files, when a conversation resumes.
