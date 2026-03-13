"""
tests/test_deployment.py — File-check tests for RPGREC-002f (deployment).

No Discord, no GPU, no network required.
"""

import configparser
import os
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SERVICE_FILE = REPO_ROOT / "deploy" / "rpg-recorder.service"
DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "deploy.sh"


# ---------------------------------------------------------------------------
# systemd service file checks
# ---------------------------------------------------------------------------

def _read_service() -> configparser.ConfigParser:
    """Parse the .service file with configparser (INI-compatible)."""
    cfg = configparser.ConfigParser(strict=False)
    cfg.read(SERVICE_FILE)
    return cfg


def test_service_file_exists():
    assert SERVICE_FILE.exists(), f"Missing: {SERVICE_FILE}"


def test_service_has_unit_section():
    cfg = _read_service()
    assert cfg.has_section("Unit"), "[Unit] section missing"


def test_service_has_service_section():
    cfg = _read_service()
    assert cfg.has_section("Service"), "[Service] section missing"


def test_service_has_install_section():
    cfg = _read_service()
    assert cfg.has_section("Install"), "[Install] section missing"


def test_service_restart_on_failure():
    cfg = _read_service()
    assert cfg.get("Service", "Restart") == "on-failure", "Restart must be 'on-failure'"


def test_service_restart_sec():
    cfg = _read_service()
    val = cfg.get("Service", "RestartSec")
    # Accept bare integer or integer with 's' suffix
    assert val.rstrip("s") == "5", f"RestartSec must be 5 (got {val!r})"


def test_service_exec_start_contains_python():
    cfg = _read_service()
    # Use raw=True so systemd specifiers like %h are not treated as interpolation
    exec_start = cfg.get("Service", "ExecStart", raw=True)
    assert "python" in exec_start.lower(), "ExecStart must reference python"


def test_service_exec_start_contains_bot_module():
    cfg = _read_service()
    exec_start = cfg.get("Service", "ExecStart", raw=True)
    assert "-m bot" in exec_start, "ExecStart must run '-m bot'"


def test_service_is_user_service():
    """WantedBy=default.target marks this as a user service (not system)."""
    cfg = _read_service()
    wanted_by = cfg.get("Install", "WantedBy")
    assert wanted_by == "default.target", (
        f"User services must use WantedBy=default.target (got {wanted_by!r})"
    )


def test_service_has_environment_dirs():
    """Service must declare SESSIONS_DIR and LOG_DIR environment variables."""
    text = SERVICE_FILE.read_text()
    assert "SESSIONS_DIR" in text, "SESSIONS_DIR environment variable missing from service file"
    assert "LOG_DIR" in text, "LOG_DIR environment variable missing from service file"


def test_service_stdout_is_journal():
    cfg = _read_service()
    assert cfg.get("Service", "StandardOutput") == "journal"


def test_service_stderr_is_journal():
    cfg = _read_service()
    assert cfg.get("Service", "StandardError") == "journal"


# ---------------------------------------------------------------------------
# deploy script checks
# ---------------------------------------------------------------------------

def test_deploy_script_exists():
    assert DEPLOY_SCRIPT.exists(), f"Missing: {DEPLOY_SCRIPT}"


def test_deploy_script_is_executable():
    mode = os.stat(DEPLOY_SCRIPT).st_mode
    assert mode & stat.S_IXUSR, "scripts/deploy.sh must be executable (chmod +x)"


def test_deploy_script_contains_git_pull():
    text = DEPLOY_SCRIPT.read_text()
    assert "git" in text and "pull" in text, "deploy.sh must run 'git pull'"


def test_deploy_script_contains_pip_install():
    text = DEPLOY_SCRIPT.read_text()
    assert "pip install" in text and "requirements.txt" in text, (
        "deploy.sh must run 'pip install -r requirements.txt'"
    )


def test_deploy_script_contains_systemctl_restart():
    text = DEPLOY_SCRIPT.read_text()
    assert "systemctl" in text and "--user" in text and "restart" in text, (
        "deploy.sh must run 'systemctl --user restart'"
    )
