# -*- coding: utf-8 -*-
"""render-auth.py 单测：合法配置五端目标文件断言 / 校验错误文案 / 原子性 / pi 剔 packages / kimi 5 文件 / git 身份。"""
import importlib.util
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import tomllib
import yaml

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "devbox" / "render-auth.py"

VALID = """\
git:
  name: 张三
  email: zhangsan@corp.com
providers:
  relay1:
    base_url: http://relay1.internal:9527/v1
    api_key: sk-live-secret-do-not-print
    models:
      - { id: glm-5.3, ctx: 200k }
      - { id: glm-5.3-flash, ctx: 200k }
agents:
  claude: { provider: relay1, model: glm-5.3 }
  codex:  { provider: relay1, model: glm-5.3 }
  pi:     { provider: relay1 }
  kimi:   { provider: relay1 }
  omp:    { provider: relay1, model: glm-5.3 }
"""


def _load_module():
    spec = importlib.util.spec_from_file_location("render_auth", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cfg(tmp_path, body=VALID):
    f = tmp_path / "cadence-box.yaml"
    f.write_text(textwrap.dedent(body), encoding="utf-8")
    return _load_module().parse_config(f)


# ---------- 校验 ----------

def test_validate_ok(tmp_path):
    mod = _load_module()
    assert mod.validate(_cfg(tmp_path)) == []


def test_validate_missing_provider_ref(tmp_path):
    body = VALID.replace("claude: { provider: relay1,", "claude: { provider: ghost,")
    errs = _load_module().validate(_cfg(tmp_path, body))
    assert any("agents.claude.provider" in e and "ghost" in e for e in errs)


def test_validate_missing_api_key_no_echo(tmp_path):
    body = VALID.replace("api_key: sk-live-secret-do-not-print", "api_key: \"\"")
    errs = _load_module().validate(_cfg(tmp_path, body))
    assert any("api_key" in e for e in errs)
    assert not any("sk-live-secret" in e for e in errs)   # 不回显 key 值
    assert any("行" in e for e in errs)                    # 指明行号


def test_validate_missing_git_and_agents(tmp_path):
    body = "providers:\n  r1: { base_url: http://x/v1, api_key: k, models: [{id: m}] }\n"
    errs = _load_module().validate(_cfg(tmp_path, body))
    assert any("git" in e for e in errs)
    assert any("agents.claude" in e for e in errs)


# ---------- 渲染：五端目标文件内容 ----------

def _render(tmp_path, body=VALID):
    mod = _load_module()
    cfg = _cfg(tmp_path, body)
    mod.render_all(cfg, tmp_path / "home")
    return tmp_path / "home"


def test_render_claude(tmp_path):
    home = _render(tmp_path)
    s = json.loads((home / ".claude/settings.json").read_text())
    assert s["env"]["ANTHROPIC_AUTH_TOKEN"] == "sk-live-secret-do-not-print"
    assert s["env"]["ANTHROPIC_BASE_URL"] == "http://relay1.internal:9527/v1"
    assert s["env"]["ANTHROPIC_MODEL"] == "glm-5.3"
    assert json.loads((home / ".claude/.credentials.json").read_text()) == {}


def test_render_codex(tmp_path):
    home = _render(tmp_path)
    t = tomllib.loads((home / ".codex/config.toml").read_text())
    assert t["model"] == "glm-5.3"
    assert t["model_provider"] == "cadence"
    assert t["model_providers"]["cadence"]["base_url"] == "http://relay1.internal:9527/v1"
    assert t["model_providers"]["cadence"]["wire_api"] == "responses"
    a = json.loads((home / ".codex/auth.json").read_text())
    assert a["OPENAI_API_KEY"] == "sk-live-secret-do-not-print"
    m = json.loads((home / ".codex/models.json").read_text())
    assert m["models"][0]["slug"] == "glm-5.3"
    assert m["models"][0]["context_window"] == 200 * 1024


def test_render_pi_settings_without_packages(tmp_path):
    home = _render(tmp_path)
    m = json.loads((home / ".pi/agent/models.json").read_text())
    p = m["providers"]["relay1"]
    assert p["baseUrl"] == "http://relay1.internal:9527/v1"
    assert p["apiKey"] == "sk-live-secret-do-not-print"
    assert p["api"] == "openai-completions"
    assert json.loads((home / ".pi/agent/auth.json").read_text()) == {}
    s = json.loads((home / ".pi/agent/settings.json").read_text())
    assert "packages" not in s                      # 剔除 packages（防首启拉 275MB）
    assert s["defaultProvider"] == "relay1"
    assert s["defaultModel"] == "glm-5.3"           # pi 未配 model → 取 models[0]


def test_render_kimi_five_files(tmp_path):
    home = _render(tmp_path)
    t = tomllib.loads((home / ".kimi-code/config.toml").read_text())
    assert t["default_model"] == "relay1/glm-5.3"
    assert t["providers"]["relay1"]["base_url"] == "http://relay1.internal:9527/v1"
    assert t["providers"]["relay1"]["type"] == "openai"
    assert t["models"]["relay1/glm-5.3"]["provider"] == "relay1"
    c = json.loads((home / ".kimi-code/credentials/kimi-code.json").read_text())
    assert c["scope"] == "kimi-code" and c["access_token"] == ""
    d = (home / ".kimi-code/device_id").read_text().strip()
    assert len(d) == 36 and d.count("-") == 4       # uuid4 形态
    assert (home / ".kimi-code/region").read_text().strip() == "cn"
    assert (home / ".kimi-code/oauth/kimi-code").exists()


def test_render_omp(tmp_path):
    home = _render(tmp_path)
    m = yaml.safe_load((home / ".omp/agent/models.yml").read_text())
    p = m["providers"]["relay1"]
    assert p["baseUrl"] == "http://relay1.internal:9527/v1"
    assert p["models"][0]["id"] == "glm-5.3"
    c = yaml.safe_load((home / ".omp/agent/config.yml").read_text())
    assert c["modelRoles"]["default"] == "relay1/glm-5.3"
    assert c["setupVersion"] == 2


def test_render_gitconfig(tmp_path):
    home = _render(tmp_path)
    t = (home / ".gitconfig").read_text()
    assert "name = 张三" in t and "email = zhangsan@corp.com" in t
    assert "autocrlf = true" in t and "filemode = false" in t


def test_render_raw_escape(tmp_path):
    body = VALID.replace(
        "claude: { provider: relay1, model: glm-5.3 }",
        'claude: { provider: relay1, model: glm-5.3, raw: { theme: dark, env: { ANTHROPIC_SMALL_FAST_MODEL: glm-5.3-flash } } }')
    home = _render(tmp_path, body)
    s = json.loads((home / ".claude/settings.json").read_text())
    assert s["theme"] == "dark"
    assert s["env"]["ANTHROPIC_SMALL_FAST_MODEL"] == "glm-5.3-flash"


# ---------- 原子性 ----------

def test_render_atomicity(tmp_path, monkeypatch):
    mod = _load_module()
    cfg = _cfg(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    sentinel = home / ".gitconfig"
    sentinel.write_text("旧内容", encoding="utf-8")
    calls = {"n": 0}
    orig = mod._serialize

    def flaky(fmt, payload):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("模拟序列化中途失败")
        return orig(fmt, payload)

    monkeypatch.setattr(mod, "_serialize", flaky)
    with pytest.raises(RuntimeError):
        mod.render_all(cfg, home)
    assert sentinel.read_text() == "旧内容"          # 中途失败：既有目标不被破坏
    assert not (home / ".claude").exists()           # 未发生任何半成品落位
    monkeypatch.setattr(mod, "_serialize", orig)
    mod.render_all(cfg, home)
    assert (home / ".claude/settings.json").exists() # 成功路径：完整替换
    assert sentinel.read_text() != "旧内容"


# ---------- CLI ----------

def test_cli_exit2_on_invalid(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(VALID.replace("api_key: sk-live-secret-do-not-print", "api_key: \"\""), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(bad), "--home", str(tmp_path / "h")],
        capture_output=True, text=True)
    assert r.returncode == 2
    assert "api_key" in r.stderr
    assert "sk-live-secret" not in r.stderr


def test_cli_ok(tmp_path):
    f = tmp_path / "box.yaml"
    f.write_text(VALID, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(f), "--home", str(tmp_path / "h")],
        capture_output=True, text=True)
    assert r.returncode == 0
    assert (tmp_path / "h/.kimi-code/region").exists()
