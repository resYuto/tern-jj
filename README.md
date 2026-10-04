# tern-jj

English | [日本語](README.ja.md)

A Luau plugin development environment for adding Jujutsu support to Tern.
Currently, it renders `jj status` and `jj st` output as native cards.
It does not perform Jujutsu operations or replace Tern's existing Git UI.

## Requirements

- macOS, a desktop session, and access to a Tern account
- Tern installed at `/Applications/Tern.app`
- `mise`, `jj`, and Python 3 (for the smoke check)

Verified with Tern 0.4.1, jj 0.45.1, and luau-lsp 1.70.1.
If Tern is installed elsewhere, override its path, for example:
`TERN=/path/to/tern mise run dev`.

## Getting started

```sh
mise trust
mise install github:JohnnyMorganz/luau-lsp@1.70.1
mise run setup
mise run check
mise run dev
```

Tern executes Luau directly; no compilation or bundling is required.
`check` performs static type checking, and `dev` launches Tern.
Run `jj status` in the opened pane to display a "Jujutsu status" card.
The card colors additions green, modifications/renames yellow, and deletions red.
Change IDs use the accent color, commit IDs use the info color, and a clean
working copy uses green. Colors follow the active Tern theme; unrecognized lines stay unchanged.
Errors, empty output, and output exceeding 5,000 lines remain in Raw view.
Status commands with additional arguments, `jj log`, `jj diff`, and other
commands are not captured by this lens and retain their normal output.

## Editing and verification

- `host.luau`: host-side lens implementation; saving reloads it automatically.
- `plugin.toml`: declares the entry point and command patterns to capture.
- `mise run reload`: manually reloads the development daemon's plugins; requires `dev` to be running.
- `mise run smoke`: uses a temporary jj repository and an independent Tern window
  to verify clean output, added/modified/deleted/renamed file colors, change/commit
  ID colors, and error output outside a repository. Stops the test window and daemon on exit.
- Screenshot: `.dev/shots/live/jj-status.png`
- Rendered element snapshot: `.dev/status-tree.json`
- Development logs: `.dev/logs/`
- Smoke check logs: `.dev/smoke-process.log` and `.dev/smoke-logs/`

For VS Code, install the recommended **Luau Language Server** extension.
`.vscode/settings.json` disables the Roblox environment and loads Tern's type definitions.
Run `mise run types` to regenerate `tern.d.luau` from the installed Tern.
This generated file is not tracked; regenerate it after updating Tern.
`types/luau.d.luau` declares the nominal `userdata` base type missing from the
standard environment so that Tern's `extern` types can be checked.
It does not bypass type checking with `any`.

## Isolation from the normal environment

Development environment variables are scoped to the `mise` tasks, not exported
when mise activates this directory. Running `tern plugin install` from the repository
therefore targets normal Tern. In an already-open shell, let the next mise prompt
hook refresh the environment, or run `eval "$(mise hook-env -s zsh)"` for zsh.

The tasks use:

- Settings, plugin links, and plugin data: `.dev/config/`
- Session daemon socket: `.dev/daemon.sock`
- Window control socket: `.dev/control.sock`
- zsh startup configuration: `dev/zsh/` (does not load personal rc files or aliases)

`dev/settings.json` is copied to `.dev/config/settings.json` only on first setup.
Existing development settings are not overwritten. Automatic updates are disabled
in the development profile.
The repository root is linked as the plugin package.
`tern-sdk/` is retained unchanged as the distributed SDK and examples.

The development zsh profile uses the official shell integration cached by Tern.
The plugin injects `JJ_PAGER=cat` when Tern spawns a new shell to prevent interactive
pagers from aborting lens capture. Personal shell and Jujutsu configuration files
are not modified.

## Loading in production (normal Tern)

Use `install` rather than `link` to deploy a copy in production.
This prevents edits saved during development from immediately affecting your
normal Tern session.
luau-lsp, Python, and the development zsh configuration are not required to run
the plugin in production.

### Initial installation

The subshell clears any inherited configuration, socket, and window overrides
(for example, from a development Tern pane).
It does not change the parent shell's environment variables.

```sh
(
  unset TERN_CONFIG_DIR TERN_DAEMON_SOCKET TERN_WINDOW_KEY TERN_WINDOW_SOCKET
  /Applications/Tern.app/Contents/MacOS/tern plugin install github.com/resYuto/tern-jj &&
  /Applications/Tern.app/Contents/MacOS/tern plugin list
)
```

GitHub installation requires `plugin.toml` and its entry point at the repository
root. No local checkout is needed.

On macOS, the installation directory is normally
`~/Library/Application Support/Tern/plugins/jj/`.
If the normal daemon is running, installation automatically reloads its plugins.
If you see `no daemon running; changes apply at next start`, start normal Tern.
In that case, `ready` in `list` only indicates a valid manifest; it does not
confirm that the Lua code has run.

If you previously used `link` in the normal environment, run `tern plugin unlink jj`
in a subshell with the same environment overrides cleared before installing.
Even `install --force` cannot replace a linked package.

### Verifying loading and rendering

In normal Tern, confirm that Jujutsu is Ready under Preferences › Plugins,
that the plugin is enabled, and that Settings › Terminal › Native command output
is enabled. Open a new pane with shell integration active after loading the plugin,
change to a jj repository and run:

```sh
jj status
```

A "Jujutsu status" card confirms that the host-side plugin loaded and the lens works.
The Raw toggle shows the original output. The plugin sets `JJ_PAGER=cat` for all jj
commands in new panes, replacing any inherited value. Existing panes are unchanged;
open a new pane after installing or reloading the plugin. Shell startup files or
explicit command-local assignments can override the injected value.

### Updating

Editing local source does not update the installed copy.
After publishing the checked changes to GitHub, explicitly replace it:

```sh
(
  unset TERN_CONFIG_DIR TERN_DAEMON_SOCKET TERN_WINDOW_KEY TERN_WINDOW_SOCKET
  /Applications/Tern.app/Contents/MacOS/tern plugin install github.com/resYuto/tern-jj --force &&
  /Applications/Tern.app/Contents/MacOS/tern plugin list
)
```

### Disabling or removing

Temporarily disable the plugin under Preferences › Plugins.
To remove the installed copy, run the following. The development source is retained.

```sh
(
  unset TERN_CONFIG_DIR TERN_DAEMON_SOCKET TERN_WINDOW_KEY TERN_WINDOW_SOCKET
  /Applications/Tern.app/Contents/MacOS/tern plugin remove jj
)
```

If you deployed with `link`, use `unlink jj` instead of `remove`.

## Official documentation

- [Getting Started](https://docs.stencil.so/tern/guides/getting-started.html)
- [Command Lenses](https://docs.stencil.so/tern/guides/lenses.html)
- [Debugging / control endpoint](https://docs.stencil.so/tern/guides/debugging.html)
- [Plugin CLI](https://docs.stencil.so/tern/reference/cli.html)
