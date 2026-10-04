"""Exercise the real Tern/Luau runtime and jj CLI; requires a desktop session."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
TERN = os.environ.get("TERN", "/Applications/Tern.app/Contents/MacOS/tern")
ARTIFACTS = ROOT / ".dev"
ARTIFACTS.mkdir(exist_ok=True)

with tempfile.TemporaryDirectory(prefix="tern-jj-", dir="/tmp") as temporary:
    work = Path(temporary)
    repo = work / "repo"
    config = work / "config"
    config.mkdir()
    (config / "settings.json").write_bytes((ROOT / "dev/settings.json").read_bytes())
    env = dict(os.environ, TERN_CONFIG_DIR=str(config),
               TERN_DAEMON_SOCKET=str(work / "daemon.sock"),
               STENCIL_LOG_DIR=str(ARTIFACTS / "smoke-logs"),
               ZDOTDIR=str(ROOT / "dev/zsh"))
    env.pop("JJ_PAGER", None)
    subprocess.run(["jj", "git", "init", "--no-colocate", str(repo)], check=True, env=env)
    package = work / "package"
    package.mkdir()
    for name in ("plugin.toml", "host.luau"):
        (package / name).write_bytes((ROOT / name).read_bytes())
    subprocess.run([TERN, "plugin", "install", str(package)], check=True, env=env)
    control = str(work / "control.sock")

    def ctl(command):
        result = subprocess.run([TERN, "ctl", "--control", control, command],
                                env=env, text=True, capture_output=True, timeout=40)
        reply = json.loads(result.stdout)
        assert result.returncode == 0 and reply["ok"], reply
        return reply

    with (ARTIFACTS / "smoke-process.log").open("w") as log:
        daemon = subprocess.Popen([TERN, "daemon"], env=env, stdout=log, stderr=log)
        window = None
        try:
            deadline = time.monotonic() + 30
            while not Path(env["TERN_DAEMON_SOCKET"]).exists():
                assert daemon.poll() is None, "Daemon exited; see .dev/smoke-process.log"
                assert time.monotonic() < deadline, "Daemon did not open its socket"
                time.sleep(0.1)
            window = subprocess.Popen([TERN, "--control", control, "--out",
                                       str(ARTIFACTS / "shots"), str(repo)],
                                      env=env, stdout=log, stderr=log)
            deadline = time.monotonic() + 30
            while not Path(control).exists():
                assert window.poll() is None, "Tern exited; see .dev/smoke-process.log"
                assert time.monotonic() < deadline, "Tern did not open its control endpoint"
                time.sleep(0.1)
            ctl("ready")
            catalog = subprocess.run([TERN, "plugin", "reload", "--json"], env=env,
                                     check=True, text=True, capture_output=True)
            plugins = json.loads(catalog.stdout)
            assert not plugins["problems"], plugins
            assert any(p["id"] == "jj" and p["status"] == "ready" for p in plugins["plugins"]), plugins

            ctl('run "test \\"$JJ_PAGER\\" = cat"')
            ctl("ready")
            state = ctl("state")
            assert state["focused"]["last"]["status"] == 0, "New shell did not receive JJ_PAGER=cat"

            ctl('run "jj status"')
            ctl('plugins expect "Jujutsu status"')
            ctl('plugins expect "The working copy has no changes."')
            print("PASS: clean repository renders a native status card")

            for name in ("modified.txt", "deleted.txt", "before.txt"):
                (repo / name).write_text("original\n", encoding="utf-8")
            subprocess.run(["jj", "new"], cwd=repo, env=env, check=True)
            (repo / "modified.txt").write_text("modified\n", encoding="utf-8")
            (repo / "deleted.txt").unlink()
            (repo / "before.txt").rename(repo / "after.txt")

            (repo / "changed file.txt").write_text("Jujutsu smoke check\n", encoding="utf-8")
            ctl('run "jj st"')
            ctl('plugins expect "A changed file.txt"')
            tree = ctl("tree .sf-block[data-role='lens.plugin.jj.status']")
            (ARTIFACTS / "status-tree.json").write_text(json.dumps(tree, indent=2), encoding="utf-8")
            for token, expected in (
                ("success", "A changed file.txt"),
                ("warning", "M modified.txt"),
                ("warning", "R {before.txt => after.txt}"),
                ("error", "D deleted.txt"),
            ):
                styled = ctl(f"tree .sf-block[data-role='lens.plugin.jj.status'] .sf-t-{token}")
                assert any(node.get("text") == expected for node in styled["nodes"]), styled
            status_output = subprocess.run(["jj", "status", "--color=never"], cwd=repo,
                                           env=env, check=True, text=True, capture_output=True).stdout
            for line in status_output.splitlines():
                if line.startswith("Working copy") and "(@)" in line or line.startswith("Parent commit (@-)"):
                    change, commit = line.split(":", 1)[1].split()[:2]
                    for token, expected in (("accent", change), ("info", commit)):
                        styled = ctl(f"tree .sf-block[data-role='lens.plugin.jj.status'] .sf-t-{token}")
                        assert any(node.get("text") == expected for node in styled["nodes"]), styled
            ctl("shot jj-status")
            print("PASS: added, modified, deleted, renamed files and commit IDs render styled text")

            ctl("tab new")
            ctl("ready")
            ctl("run " + json.dumps("cd " + shlex.quote(str(work))))
            ctl('run "jj status"')
            ctl("ready")
            state = ctl("state")
            assert state["focused"]["last"]["status"] != 0, state["focused"]
            capture = subprocess.run([TERN, "capture", str(state["focused"]["id"]), "--surfaces"],
                                     env=env, check=True, text=True, capture_output=True)
            assert "Error: There is no jj repo" in capture.stdout, capture.stdout
            error_view = ctl("tree .sf-block[data-role='lens.plugin.jj.status']")
            assert all("Jujutsu status" not in node.get("text", "") for node in error_view["nodes"]), error_view
            print("PASS: non-repository error remains visible as raw output")
        finally:
            if window is not None and window.poll() is None:
                window.terminate()
                window.wait(timeout=15)
            if daemon.poll() is None:
                daemon.terminate()
                daemon.wait(timeout=15)
