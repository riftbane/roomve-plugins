---
name: roomve-projects
description: Work on a project of Roomve Workspace (workspace.roomve.it) through the Roomve MCP connector - its shared folder (read files, bring them into the account's space for Blender or the image tools, put results back), its tasks, comments and roadmap epics, and its wiki (also published as a website on the person's domain), and its own static website. Use it BEFORE the first call of list_projects, project_*, task_*, epic_* or wiki_* tools, whenever the person says "the project", "our game", "the shared folder", "the tasks", "the roadmap", "the wiki", "the lore", names a project or its repos, and whenever one of those tools answers with an error. It explains where files and code live, the paths, the copies, tasks and epics, wiki pages with their images, what is never reachable (GitHub), and how to behave where other people work.
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

## Tasks, comments and the roadmap

A project also has **tasks** (its to-do list, like the issues of a repo: a title, a Markdown description, a state,
an assignee, a due day, labels, a conversation of comments) and **epics** (the roadmap: groups of tasks with a goal
and start and end days). You act **as the person**: what you write appears with their name, their permissions apply.

| Tool | What it does |
|---|---|
| `project_tasks(project, status, assignee, epic, label, search)` | The tasks (open ones by default; `status="all"`), the epics with days and progress, the labels and the people (`@username`). Every task and epic has an **id** |
| `task_read(project, task_id)` | One task whole: description, links, attached files, GitHub issues/PRs, comments first to last |
| `task_create(project, title, description, status, assignee, due_date, epic, labels)` | A new task |
| `task_update(project, task_id, …)` | Changes only the fields given. `status="done"` closes it |
| `task_comment(project, task_id, body)` | A comment at the end of the conversation |
| `task_delete`, `epic_delete` | Remove one (ask first). An epic's tasks stay, outside any epic |
| `epic_create`, `epic_update` | An epic: title, description, colour, `start_date`, `due_date` |

- States: `todo` (to do), `doing` (in progress), `done`. Days are `YYYY-MM-DD`.
- `assignee`: a username, a name or `me`; only people who can open the project. `epic`: an id or the exact title.
  `labels`: names of labels that already exist (they are created on the website). In `task_update` an empty
  string removes the assignee, the due day or the epic, and `labels=[]` removes all labels.
- `description` in `task_update` and `epic_update` **replaces** the old one: read it with `task_read` (or
  `project_tasks(epic=…)`) and send back the whole text changed. Checklists are `- [ ] step` / `- [x] step`.
- **`@username` in a comment reaches that person's inbox** on the website. Name someone only when they should
  look; never name the person themselves to get attention. The answer says whose inbox it reached.
- Look with `project_tasks` before creating, so as not to repeat a task that exists. Group work in an epic only if
  the person asks or one fits clearly.
- Reading comments here does not mark them read for the person: they still see them as new on the website.
- Attachments, labels and linked issues/PRs are shown but changed only on the website. Task ids are for you:
  when telling the person about a task, give its title and its link.

### Moving, renaming, deleting, uploading

| Tool | What it does |
|---|---|
| `project_move(project, paths, to, create, on_conflict)` | Move files or folders into a folder of the project (`create` makes it) |
| `project_rename(project, path, name, on_conflict)` | Rename one file or folder where it is |
| `project_delete(project, paths)` | Move them to the **project's trash** (restorable from the website); ask first: other people work there |
| `project_upload_url(project, path, replace)` | A curl command to upload ONE file from the person's computer straight into the project (once, for an hour, within 2 minutes) |

`on_conflict`: `fail` (default; the answer shows a free name), `rename`, `replace` (the old file goes to the trash).
For a file made in the account's space (Blender, images) use `project_push`, not the upload link.

## The wiki

A project has a **wiki** (on the website, tab Wiki; it used to be called "Storia"): the lore and the world of the
game, the rules, anything the team writes down. Pages form a tree, at most 4 levels deep.

| Tool | What it does |
|---|---|
| `wiki_pages(project, search)` | The tree of pages with their ids; with `search`, the pages that contain those words |
| `wiki_read(project, page_id)` | A page: its **version**, its place in the tree, its text in Markdown, its images |
| `wiki_create(project, title, text, parent)` | A new page, under `parent` (id or exact title) or at the top |
| `wiki_update(project, page_id, version, title, text, parent, position)` | Change title, text or place |
| `wiki_delete(project, page_id)` | Remove a page without sub-pages (ask first) |

- The text is Markdown: `#`/`##` headings (they make the page's outline on the website), bold, italic, lists,
  quotes, and `[[Title of another page]]` to link a page (a link to a page that does not exist yet shows in red).
- **Images** (often maps with places, areas and writings drawn on them) appear in the text as a line
  `{{image <id>}}`, and below it `wiki_read` lists what is drawn on each, with x and y from 0 (left/top) to 1.
  Use them to describe the world consistently. Images are added and drawn on **only on the website**.
- `text` in `wiki_update` **replaces** the whole text: start from `wiki_read`, change what is needed and keep
  each `{{image …}}` line where the image belongs. Leaving one out is refused unless `remove_images=true` (only
  if the person asked to take that image off the page).
- `version` is required to change title or text. If someone saved the page after you read it, nothing is
  changed and the answer says so: read it again and redo the change on the new text.
- Moving: `parent` (empty string = the top) and `position` (0 = first among its siblings).
- Look with `wiki_pages` before creating a page: write in the page that exists, or under the right parent.
  Keep the names, places and facts already in the wiki; when something you write contradicts it, say so.

### Publishing the wiki

The wiki can go online as a **read-only website on the person's own domain** (Roomve gives no domain). Everyone who
can open the project may do it.

| Tool | What it does |
|---|---|
| `wiki_publication(project)` | Online or not, where, who may read it, which pages the next copy holds, the domain and the DNS records it still needs, the copies kept |
| `wiki_publish(project, action, …)` | `publish` a new fixed copy, `unpublish`, `restore` a kept copy (`snapshot_id`), or `settings`: `visibility` (`public` / `link`), `new_link`, `title`, `branch`, `exclude`, `indexable` |
| `wiki_domain(project, action, name)` | `link` a domain of the person, `check` its DNS now, `unlink` it |

- What is online is a **fixed copy**: changes to the wiki do not show until the next `publish`. Title, branch,
  excluded pages and indexing apply from the next publish; `visibility` and `new_link` apply at once.
- It makes things **public**: ask the person before `publish`, before `visibility=public`, before `restore`, and
  before `unlink`. Spoilers: a page in `exclude` leaves with its sub-pages.
- The domain: you cannot change the person's DNS. After `link`, tell them exactly the records the answer lists: a
  **CNAME to site.roomve.it** for a sub-domain (wiki.example.com, the advised choice), or the **A/AAAA** records for
  a bare domain, plus the **TXT** `_roomve.<domain>`. Then `check` (it is also checked every 15 minutes by itself).
  Once active, HTTPS comes a few minutes later.

### The site of a project

A project can put its **website** online on the person's own domain: the static files of a folder of the project
(default `Sito/`, or its `frontend/` sub-folder): `index.html`, pages, styles, scripts, images. With a
`Sito/backend/package.json` the site also has a **Node.js 24 backend**: it answers on `/api` of the domain, listens on
`PORT`, has its own SQLite file at `DATABASE_PATH` (copied every day to `Sito/backup/`), gets the secrets as environment
variables, reaches the Internet but not the server; npm installs its dependencies at each deploy.
`Sito/roomve-site.json` can say `{"backend": {"main": "server.js", "path": "/api"}}`. Everyone who can open the project
may do it.

| Tool | What it does |
|---|---|
| `site_status(project)` | Online or not, where, which folder the next version takes, the domain and its DNS records, the versions kept |
| `site_deploy(project, action, …)` | `deploy` the files now, `unpublish`, `restore` a kept version (`deploy_id`), or `settings`: `folder`, `spa` (single-page app: unknown addresses open index.html) |
| `site_domain(project, action, name)` | `link` a domain of the person, `check` its DNS now, `unlink` it |
| `site_backend(project, action, …)` | The backend: `logs`, `restart`, `stop`, `backup` its database now, `set_secret` / `delete_secret` (name, value) |

- Put the files in the folder first (`project_write`, `project_push`); `index.html` is required. Files whose name
  starts with a dot (`.env`, `.git`) never go online, nor `backend/` and `backup/` at the top of the folder.
- Online goes a **fixed copy**: changing the files does not change the site until the next `deploy`.
- It makes things **public**: ask the person before `deploy`, before `restore` and before `unlink`.
- The domain works as for the wiki: tell the person the records the answer lists (CNAME to site.roomve.it for a
  sub-domain such as www.example.com, or A/AAAA for a bare domain, plus the TXT `_roomve.<domain>`), then `check`.

### Distributing the releases

The GitHub releases of a linked repo can be **served by Roomve Workspace** to programs and download pages: the client
never sees GitHub (private repos too). Channels `release` and `prerelease` come from GitHub's pre-release flag (drafts
never); mappers say which file is for which platform; access is public or limited (tokens made on the website).

| Tool | What it does |
|---|---|
| `dist_status(project)` | Per linked repo: the URLs (`…/release/latest.json`, `…/prerelease/latest.json`, `…/versions.json`), access, mappers, the newest versions with their files mapped or not |
| `dist_configure(project, repo, …)` | Turn it on/off (made if missing), name, `access`, `prerelease_access`, `mappers` (the whole list), `pin_release` / `pin_prerelease` |

- A program asks `latest.json?platform=windows&arch=x64` and gets `{version, file, url, size, sha256}`; the file is at
  `…/<version>/<file>`, with `Authorization: Bearer rwd_…` when the access is limited.
- Public access makes the files downloadable by anyone: ask the person first. On a public repo limited access hides
  nothing (GitHub gives the files anyway): say so.
- The organization's GitHub token must see the repo with **Contents: read**.

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
| `No such task in this project` / `No such epic …` | It was deleted or the id is wrong: `project_tasks` for the ids. |
| `… is not one of the people who can open the project` | Use a username from the list in the answer. |
| `No label called …` | Use an existing label, or leave labels out; labels are created on the website. |
| `Roomve Workspace refused it (field …): …` | The message (in Italian) says what is wrong with that field: fix it and call again. |
| `Limit of the project reached` | Tell the person; do not retry. |
| `This person may not do that` | Deleting is for who wrote it or who has full access: tell the person. |
| `No such page in this wiki` / `No wiki page …` | `wiki_pages` for the ids and titles. |
| `… saved this page after you read it` | `wiki_read` again, redo the change on the new text with the new version. |
| `The new text leaves out {{image …}}` | Put the image lines back; `remove_images=true` only if the person asked. |
| `The page has sub-pages` | Move or delete the sub-pages first (ask). |
| `Roomve Workspace refused it: …` (publish, domain) | The message says why: nothing to publish, branch gone, domain taken or invalid, a publish already running. Fix that, do not just retry. |
| `Too large to publish` | The copy's images are too large: leave out pages or images (ask the person). |
| `… manca index.html` / `… non c'è la cartella …` (site) | Put an index.html in the site's folder (or create the folder), then deploy again. |
| `… npm …` / `Il backend si è fermato appena partito …` with a log | Nothing changed online. Read the log, fix the backend's files, deploy again. |
| `… still waiting for its DNS` | The records are not there yet (or are wrong: the answer shows what was found). Records can take hours to spread. |
| `… token GitHub … non legge le release …` | The organization's GitHub token lacks Contents: read on that repo: the owner fixes it in the organization's settings. |
| `Roomve Workspace is not connected to this server` | The project tools are off on this server. Say so and stop. |
