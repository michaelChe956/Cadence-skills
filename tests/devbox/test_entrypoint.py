# -*- coding: utf-8 -*-
"""entrypoint.sh 主线行为：失败路径（auth 缺字段 exit 2）/ 全链路 / 软失败 / 模板同步保护。"""
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENTRY = REPO / "devbox" / "entrypoint.sh"
SCRIPT = REPO / "devbox" / "render-auth.py"

VALID = """\
git:
  name: 张三
  email: zhangsan@corp.com
providers:
  relay1:
    base_url: http://relay1.internal:9527/v1
    api_key: sk-live-secret
    models:
      - { id: glm-5.3, ctx: 200k }
agents:
  claude: { provider: relay1, model: glm-5.3 }
  codex:  { provider: relay1, model: glm-5.3 }
  pi:     { provider: relay1 }
  kimi:   { provider: relay1 }
  omp:    { provider: relay1, model: glm-5.3 }
"""


def _env(home, stack, auth_file, offline=False):
    env = {**os.environ, "HOME": str(home),
           "CADENCE_STACK_DIR": str(stack),
           "CADENCE_STACK_TEMPLATE_DIR": str(stack.parent / "template"),
           "CADENCE_RENDER_AUTH": str(SCRIPT),
           "CADENCE_AUTH_FILE": str(auth_file)}
    if offline:  # 让 skills 安装的三个镜像全部快速失败——验证软失败不阻断
        env["https_proxy"] = env["http_proxy"] = "http://127.0.0.1:1"
        env["HTTPS_PROXY"] = env["HTTP_PROXY"] = "http://127.0.0.1:1"
    return env


def _make(tmp_path, auth_body=VALID, with_changes=False):
    home = tmp_path / "home"
    stack = tmp_path / "mount" / "stack"
    tmpl = tmp_path / "mount" / "template"
    (stack).mkdir(parents=True)
    # 预置假 .git 标记：boot_skills 走 git pull 快速失败→软失败路径，使本测试离线确定性
    (home / ".agents/Cadence-skills/.git").mkdir(parents=True)
    (tmpl / "catalog/mysql/conf").mkdir(parents=True)
    (tmpl / "compose.yaml").write_text("name: cadence\nservices: {}\n", encoding="utf-8")
    (tmpl / "catalog/mysql/profile").write_text("default\n", encoding="utf-8")
    (tmpl / "docker-compose.no-sock.yml").write_text("services: {}\n", encoding="utf-8")
    auth = tmp_path / "auth.yaml"
    auth.write_text(auth_body, encoding="utf-8")
    if with_changes:
        (stack / "CHANGES.md").write_text("- 2026-09-11 add kafka\n", encoding="utf-8")
        (stack / "compose.yaml").write_text("# 用户改过版\n", encoding="utf-8")
    return home, stack, auth


def _run(env, argv=("sleep", "0")):
    return subprocess.run(["bash", str(ENTRY), *argv], env=env,
                          capture_output=True, text=True, timeout=300)


def test_exit2_on_missing_api_key(tmp_path):
    home, stack, auth = _make(tmp_path, auth_body=VALID.replace("api_key: sk-live-secret", 'api_key: ""'))
    r = _run(_env(home, stack, auth))
    assert r.returncode == 2
    assert "鉴权" in r.stderr
    assert not (home / ".claude").exists()      # 拒启：不落任何渲染产物


def test_full_boot_order_and_outputs(tmp_path):
    home, stack, auth = _make(tmp_path)
    r = _run(_env(home, stack, auth))
    assert r.returncode == 0, r.stderr
    # 步骤 1：git 对齐 + 轮询 env（bashrc 幂等块）+ 卷内源配置刷新
    gc = (home / ".gitconfig").read_text()
    assert "autocrlf = true" in gc and "filemode = false" in gc
    assert "cadence-entrypoint-env" in (home / ".bashrc").read_text()
    assert "aliyun" in (home / ".m2/settings.xml").read_text()
    assert (home / ".gradle/init.gradle").exists()
    # 步骤 2：五端渲染
    assert (home / ".claude/settings.json").exists()
    assert (home / ".kimi-code/region").read_text().strip() == "cn"
    # 步骤 3：stack 模板同步（无 CHANGES.md）
    assert "services" in (stack / "compose.yaml").read_text()
    assert (stack / "catalog/mysql/profile").exists()
    assert (stack / "docker-compose.no-sock.yml").exists()
    # 步骤 5：exec "$@"（entrypoint 自身日志走 stderr；skills 输出不参与断言）
    assert "就绪" in r.stderr


def test_skills_softfail_does_not_block(tmp_path):
    home, stack, auth = _make(tmp_path)
    r = _run(_env(home, stack, auth, offline=True))
    assert r.returncode == 0, r.stderr
    log = (home / ".cadence/logs/entrypoint.log").read_text()
    assert "警告" in log and "重试" in log
    assert (home / ".claude/settings.json").exists()   # 主链路不受影响


def test_stack_sync_preserves_user_version(tmp_path):
    home, stack, auth = _make(tmp_path, with_changes=True)
    r = _run(_env(home, stack, auth))
    assert r.returncode == 0, r.stderr
    assert (stack / "compose.yaml").read_text() == "# 用户改过版\n"   # CHANGES.md 存在→不覆盖
    assert "保留" in r.stderr or "保留" in (home / ".cadence/logs/entrypoint.log").read_text()
