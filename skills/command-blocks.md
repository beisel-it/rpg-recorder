# Command Blocks for Role Skills

We define a small vocabulary of helper commands (presented as literal blocks) so agents can stay in the same mental context while still executing precise actions. Replace `<project-shortcode>` and `<todo-id>` with concrete identifiers when you run the action.

```
select_project <project-shortcode>
```
- Load `metadata.json` and record the path map for this session.

```
list_stage <stage>
```
- List filenames in `projects/<slug>/tasks/<stage>` and `projects/<slug>/tasks/<stage>/working`. Stage may be `refinement`, `research`, `code`, `deployment`, `docs`, `done`, or `todo`.

```
claim_task <todo-id>
```
- Move the task into the stage's `working/` folder and set `Status: in progress` so other agents know you own it.

```
release_task <todo-id>
```
- Move the task back to the stage root and update `Status` to `ready for <next stage>` or `needs refinement`. If you are handing it back, document the blocking reason.
```

```
create_repo <slug>
```
- Create the private GitHub repo (see `repo-instructions.md`) and note `repo` in `metadata.json`.

```
take_task <todo-id>
```
- Bookmark the file in your personal task log (metadata or notes) for follow-up, recording start time + agent name.
```

```
add_status <todo-id> <status-line>
```
- Append or update a `Status:` line inside the task file describing the current condition (e.g. `in progress`, `requires review`, `blocked by ...`).

```
add_comment <todo-id> <comment>
```
- Append a comment section to the task file (e.g. under `## Comments`) so future stages can read your rationale.

```
load_context <project-shortcode>
```
- Reads `metadata.json` plus any recent notes/logs to seed the working context before selecting a task.

```
finish_task <todo-id>
```
- Tag the task as `Status: done`, move it to `tasks/done/working`, finalize docs, and optionally copy the final summary to the project overview.
```

Each command is listed as a `block` so the agent can copy/paste it verbatim and stay in context. Avoid embedding arbitrary shell instructions; the commands are sufficient to describe the workflow steps.
