---
name: roomve-projects
description: Work on a project of Roomve Workspace (workspace.roomve.it) through the Roomve MCP connector - find the person's projects, read what is in a project's shared folder, bring its files into the account's space for Blender or the image tools, and put results (game assets, renders, textures, documents) back into the project. Use it BEFORE the first call of list_projects, project_files, project_read, project_write, project_pull or project_push, whenever the person says "the project", "our game", "put it in the project", "the shared folder", "the assets folder", or names a project or its repos, and whenever one of those tools answers with an error. It explains where a project's files and code live, how the paths work, how copies between project and space behave, what is never reachable through Roomve (GitHub), and how to behave in a folder other people use.
---

# Projects of Roomve Workspace

A person can belong to organizations on Roomve Workspace. An organization has **projects**. A project is two
things:

| Part | Where it lives | How you reach it |
|---|---|---|
| A **shared folder**, 10 GB, any kind of file (documents, game assets, references) | Roomve Workspace | The `project_*` tools of this connector |
| The **GitHub repos** that belong to the project (for example a server and a client) | GitHub | **Not through Roomve.** Only their names and URLs are given |

Read **roomve-mcp** first for the account's space, which is a different place: private to the account, where
Blender and the image tools work. A project folder is shared with other people.

## Start with list_projects

`list_projects` answers with the organizations and, for each project: name, **id**, space used, link to the
project page, description, and one line per repo (`repo: owner/name (branch, private) URL`).

- Every other tool takes `project`: the **id**, or the exact name (case does not matter). If two projects have
  the same name the answer lists their ids: use the id.
- The person sees only the projects they may open, and so do you. "No project called …" lists what exists.
- If the answer is "No projects", the person has none yet or none was shared with them: say so, do not guess.

## The repos are names, not access

The repo lines tell you **which repos are part of the project**. Roomve never reads GitHub for you and never
gives a token.

- To read code, issues or pull requests use **your own access to GitHub**: a GitHub connector in a chat, `git`
  and `gh` in a shell. Use the URL from `list_projects`.
- If you have no access to GitHub in this conversation, say so. Never present guesses about the code as if you
  had read it.
- Code goes to the repo, big files (models, textures, audio, builds) go to the project folder. That split is the
  reason the folder exists.

## Paths in a project

Paths start from the root of the project's folder: `Assets/models/chair.glb`, `Documents/gdd.md`. An empty path
is the root. No `..`.

`project_files(project, path)` lists one folder (not its subfolders): folders end with `/` and say how many
items they hold. Look before you write: many projects have `Documents` and `Assets`, but each team arranges its
folder as it likes. **Follow the structure that is there** instead of inventing a new one.

## Reading

`project_read(project, path)`:

| The file is | You get |
|---|---|
| Text (markdown, notes, JSON, source, CSV…) up to 1 MB | Its text, cut at `max_chars` (default 30 000) with a note when cut |
| A picture (png, jpg, webp, gif, bmp, tif, tga) | A downscaled preview to look at |
| Anything else (a model, a `.blend`, audio, an archive) | Its kind and size only: copy it with `project_pull` to work on it |

## From the project to the space: project_pull

Blender and the image tools read only the account's space. `project_pull(project, path)` copies a file, or a
folder with everything inside, from the project into the space. The project is not changed.

- Without `to`, the copy keeps the project's folders under `projects/<project-name>/`:
  `Assets/textures/wood/oak.png` of project "MMORPG" becomes `projects/mmorpg/Assets/textures/wood/oak.png`.
  The answer prints the real paths: use those in `bpy.data.images.load(...)`, `reference_images`, `edit_image`.
- With `to="ref"`, a file lands in `ref/<name>` and a folder in `ref/<folder name>/…`.
- Up to 200 files per call: for more, copy a subfolder at a time.
- Names that start with a dot are not copied (the answer says how many were left out).
- The copy counts in the **account's** storage. `The storage space of the account is full` means the space, not
  the project: free it with `delete_files` (ask first).

## From the space to the project: project_push

`project_push(project, paths, to)` copies files or folders of the space into the project's folder, where the
other people find them. The files stay in the space too.

- `to` is the destination **folder** in the project (`Assets/models`); missing folders are created. A file keeps
  its name; a folder keeps its name and everything inside it.
- Up to 50 paths and 200 files per call.
- **An existing file is not replaced** unless `replace=true`: without it the new file gets a number
  (`cube (1).glb`) and the answer says so. With `replace=true` the old file goes to the project's trash, where
  the people of the project can still restore it.
- `project_write(project, path, content)` saves a text file directly (notes, a document, JSON, up to 1 MB),
  with the same `replace` rule. For anything binary use `project_push`.

A typical asset job:

1. `list_projects`, then `project_files` on the folders involved, to learn the structure and the naming.
2. `project_read` the documents that say what is wanted (a design document, a style guide).
3. `project_pull` what the work needs as input (references, an existing model).
4. Generate or model in the space (see **roomve-images**, **roomve-blender**), look at the result.
5. `project_push` the finished files to the right folder, and tell the person the paths and the project link.

## A folder other people use

- Put files where the project's structure says. If it is not clear, ask once.
- Ask before `replace=true` on something you did not write in this conversation, and before reorganizing.
- You cannot delete or move files in a project: that is done on the website (the project page, tab File). If
  something must go, tell the person which paths.
- Do not push intermediate files (previews, test renders, `.blend1`). Push what the project needs.
- Say what you put where: the other people were not in this conversation.

## What each answer means and what to do

| The answer says | Do this |
|---|---|
| `No project called … among the ones this person can open: …` | Use one of the listed names or ids. |
| `Several projects are called …: use the id.` | Pass the id from the answer. |
| `No such project, file or folder.` | `project_files` on the parent folder for the real names. |
| `That path is a folder` | `project_files` to list it, `project_pull` to copy it. |
| `That path is a file, not a folder.` | Use the folder above it. |
| `The shared folder of the project is full` | The project's 10 GB are used. Tell the person: files are deleted on the website. Do not retry. |
| `The storage space of the account is full` | The account's space, not the project: `delete_files` (ask first), then again. |
| `More than 200 files …` | Copy a subfolder at a time. |
| `A folder with that name is already there` | Choose another file name. |
| `Invalid path or name (…)` | No `..`, no empty names; paths start from the project root. |
| `Roomve Workspace, or the storage behind it, is not answering` | Wait a minute and call again once. |
| `Roomve Workspace is not connected to this server` | The project tools are off on this server. Say so and stop. |
