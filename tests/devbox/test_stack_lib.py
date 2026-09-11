# -*- coding: utf-8 -*-
"""stack-lib.sh 纯函数单测：bash -c source 后驱动；docker 依赖腿在 T9 冒烟验证。"""
import os
import re
import subprocess
import textwrap
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
LIB = REPO / "devbox" / "stack" / "stack-lib.sh"

COMPOSE_TMPL = """\
name: cadence

volumes:
  x-data: { external: true }

services:
  devbox:
    image: cadence-devbox:dev
  mysql:
    image: mysql:8.4
"""

RABBIT_FRAGMENT = """\
  rabbitmq:
    image: rabbitmq:3.13-management
    profiles: ["mq"]
    ports:
      - "127.0.0.1:5672:5672"
"""


def sh(script, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                       env=env, cwd=str(REPO), timeout=60)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def make_stack(tmp_path, compose=COMPOSE_TMPL, env_profiles=None):
    stack = tmp_path / "stack"
    (stack / "catalog/redis/conf").mkdir(parents=True)
    (stack / "catalog/rabbitmq").mkdir(parents=True)
    (stack / "catalog/mysql").mkdir(parents=True)
    (stack / "compose.yaml").write_text(textwrap.dedent(compose), encoding="utf-8")
    (stack / "catalog/mysql/profile").write_text("default\n")
    (stack / "catalog/redis/profile").write_text("default\n")
    (stack / "catalog/rabbitmq/profile").write_text("mq\n")
    (stack / "catalog/redis/conn.txt").write_text(
        "redis://redis:6379/0\nspring.data.redis.host: redis\n", encoding="utf-8")
    (stack / "catalog/rabbitmq/conn.txt").write_text(
        "amqp://guest:guest@rabbitmq:5672/\n", encoding="utf-8")
    # RABBIT_FRAGMENT 首行自带 2 空格缩进（与真实 catalog 的 heredoc 产物一致）——不可 dedent
    (stack / "catalog/rabbitmq/service.fragment.yaml").write_text(
        RABBIT_FRAGMENT, encoding="utf-8")
    if env_profiles is not None:
        (stack / ".env").write_text(f"COMPOSE_PROFILES={env_profiles}\n", encoding="utf-8")
    env = {"CADENCE_STACK_DIR": str(stack),
           "CADENCE_STACK_CATALOG_DIR": str(stack / "catalog")}
    return stack, env


SRC = f'source "{LIB}"; '


def test_profiles_add():
    rc, out, _ = sh(SRC + 'stack_profiles_add "" mq')
    assert rc == 0 and out == "mq"
    rc, out, _ = sh(SRC + 'stack_profiles_add "mq" mq')
    assert out == "mq"                                   # 幂等
    rc, out, _ = sh(SRC + 'stack_profiles_add "mq" storage')
    assert out == "mq,storage"


def test_profiles_remove():
    rc, out, _ = sh(SRC + 'stack_profiles_remove "mq,storage" mq')
    assert out == "storage"
    rc, out, _ = sh(SRC + 'stack_profiles_remove "mq" mq')
    assert out == ""


def test_read_write_profiles(tmp_path):
    stack, env = make_stack(tmp_path)                     # 无 .env
    rc, out, _ = sh(SRC + "stack_read_profiles", env)
    assert out == ""
    rc, out, _ = sh(SRC + 'stack_write_profiles mq && stack_read_profiles', env)
    assert out == "mq"
    rc, out, _ = sh(SRC + 'stack_write_profiles "mq,storage" && stack_read_profiles', env)
    assert out == "mq,storage"                            # 覆盖而非追加


def test_resolve_profile(tmp_path):
    stack, env = make_stack(tmp_path)
    rc, out, _ = sh(SRC + "stack_resolve_profile rabbitmq", env)
    assert out == "mq"                                    # 服务名→profile
    rc, out, _ = sh(SRC + "stack_resolve_profile mq", env)
    assert out == "mq"                                    # 直接传 profile 名
    rc, out, err = sh(SRC + "stack_resolve_profile mysql", env)
    assert rc != 0 and "默认" in err


def test_services_of_profile(tmp_path):
    stack, env = make_stack(tmp_path)
    rc, out, _ = sh(SRC + "stack_services_of_profile mq", env)
    assert out == "rabbitmq"
    rc, out, _ = sh(SRC + "stack_services_of_profile default", env)
    assert sorted(out.split()) == ["mysql", "redis"]


def test_conn_print(tmp_path):
    stack, env = make_stack(tmp_path)
    rc, out, _ = sh(SRC + "stack_conn_print redis", env)
    assert "redis://redis:6379/0" in out and "spring.data.redis.host: redis" in out
    rc, out, err = sh(SRC + "stack_conn_print nosuch", env)
    assert rc != 0 and "nosuch" in err


def test_enable_writes_env_and_changes(tmp_path):
    stack, env = make_stack(tmp_path)
    rc, out, err = sh(SRC + "stack_enable rabbitmq", env)   # 无 docker → 拉起腿告警但不失败
    assert rc == 0 and "COMPOSE_PROFILES=mq" in out
    assert (stack / ".env").read_text().strip() == "COMPOSE_PROFILES=mq"
    last = (stack / "CHANGES.md").read_text().strip().splitlines()[-1]
    assert re.fullmatch(r"-\s\d{4}-\d{2}-\d{2}\s+enable\s+rabbitmq", last)


def test_disable_removes_profile(tmp_path):
    stack, env = make_stack(tmp_path, env_profiles="mq,storage")
    rc, out, err = sh(SRC + "stack_disable mq", env)
    assert rc == 0
    assert (stack / ".env").read_text().strip() == "COMPOSE_PROFILES=storage"
    last = (stack / "CHANGES.md").read_text().strip().splitlines()[-1]
    assert re.fullmatch(r"-\s\d{4}-\d{2}-\d{2}\s+disable\s+mq", last)


def test_add_service_appends_and_logs(tmp_path):
    stack, env = make_stack(tmp_path)
    rc, out, err = sh(SRC + 'stack_add_service mymq rabbitmq', env)
    assert rc == 0, err
    doc = yaml.safe_load((stack / "compose.yaml").read_text())
    assert "mymq" in doc["services"]
    assert doc["services"]["mymq"]["image"] == "rabbitmq:3.13-management"
    assert doc["services"]["mymq"]["profiles"] == ["mq"]
    last = (stack / "CHANGES.md").read_text().strip().splitlines()[-1]
    assert re.fullmatch(r"-\s\d{4}-\d{2}-\d{2}\s+add\s+mymq", last)
    assert (stack / "data/mymq").is_dir()
    # 幂等拒绝
    rc, out, err = sh(SRC + 'stack_add_service mymq rabbitmq', env)
    assert rc != 0 and "已存在" in err


def test_rm_service_block_and_changes(tmp_path):
    stack, env = make_stack(tmp_path)
    sh(SRC + "stack_add_service mymq rabbitmq", env)
    rc, out, err = sh(SRC + "stack_rm_service mymq", env)
    assert rc == 0, err
    doc = yaml.safe_load((stack / "compose.yaml").read_text())
    assert "mymq" not in doc["services"] and "mysql" in doc["services"]
    last = (stack / "CHANGES.md").read_text().strip().splitlines()[-1]
    assert re.fullmatch(r"-\s\d{4}-\d{2}-\d{2}\s+rm\s+mymq", last)


def test_rm_purge_confirmation(tmp_path):
    stack, env = make_stack(tmp_path)
    sh(SRC + "stack_add_service mymq rabbitmq", env)
    # 回答 n：取消，服务保留
    rc, out, err = sh(SRC + 'printf "n\\n" | stack_rm_service mymq --purge', env)
    assert rc != 0 and "取消" in err
    assert yaml.safe_load((stack / "compose.yaml").read_text())["services"]["mymq"]
    # 回答 y：删块+删 ./data/<name>（外部卷删除走 docker，T9 验）
    rc, out, err = sh(SRC + 'printf "y\\n" | stack_rm_service mymq --purge', env)
    assert rc == 0, err
    assert not (stack / "data/mymq").exists()


def test_app_run_stop_logs_port(tmp_path):
    stack, env = make_stack(tmp_path)
    run_dir = tmp_path / "run" / "app"          # == $CADENCE_STACK_DIR/../run/app
    # run：后台进程 pid 落盘且存活
    rc, out, err = sh(SRC + "app_run demo sleep 5", env)
    assert rc == 0 and "pid" in out, err
    assert (run_dir / "demo.pid").is_file()
    rc, out, _ = sh(SRC + 'kill -0 "$(cat %s)"' % (run_dir / "demo.pid"), env)
    assert rc == 0
    # 幂等：运行中再 run
    rc, out, _ = sh(SRC + "app_run demo sleep 5", env)
    assert "已在运行" in out
    # logs：nohup 输出重定向到日志文件
    sh(SRC + 'app_run demo2 bash -c "echo hello-app"; sleep 1', env)
    rc, out, err = sh(SRC + "app_logs demo2", env)
    assert rc == 0 and "hello-app" in out
    # port：未监听→超时失败（1s 加速）；监听→就绪
    rc, out, err = sh(SRC + "app_port demo2 59999 1", env)
    assert rc != 0 and "未就绪" in err
    sh(SRC + "app_run demo3 python3 -m http.server 59998 --bind 127.0.0.1", env)
    rc, out, err = sh(SRC + "app_port demo3 59998 10", env)
    assert rc == 0 and "已就绪" in out
    # stop：停掉+清理 pid；再停报错
    rc, out, _ = sh(SRC + "app_stop demo3", env)
    assert rc == 0 and "已停止" in out and not (run_dir / "demo3.pid").exists()
    rc, out, err = sh(SRC + "app_stop demo3", env)
    assert rc != 0 and "未在运行" in err


# ---------- docker shim：status/restart/logs/rm 的 label 直连腿（双运行时兼容） ----------

DOCKER_SHIM = """\\
#!/usr/bin/env bash
# 伪造 docker：所有调用落 $(dirname $0)/docker-shim.log；ps 按 service label 分支输出
LOG="$(dirname "$0")/docker-shim.log"
printf '%s\\n' "$*" >>"$LOG"
cmd="$1"; shift
if [ "$cmd" = ps ]; then
  svc="" fmt=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --format) fmt="$2"; shift 2 ;;
      label=com.docker.compose.service=*) svc="${1##*=}"; shift ;;
      *) shift ;;
    esac
  done
  case "$fmt" in
    *Status*|*Ports*)
      case "$svc" in
        mysql) printf 'Up 2 hours (healthy)|127.0.0.1:3306:3306->3306/tcp\\n' ;;
        redis) printf 'Up 2 hours (healthy)|127.0.0.1:6379:6379/tcp\\n' ;;
        minio) printf 'Up 3 hours (healthy)\\n' ;;
      esac ;;
    *Label*) printf 'mysql\\nredis\\nminio\\n' ;;
    *)  # -aq 无 --format：输出容器 ID
      case "$svc" in
        mysql) printf 'cid-mysql-111\\n' ;;
        redis) printf 'cid-redis-222\\n' ;;
      esac ;;
  esac
  exit 0
fi
case "$cmd" in
  restart) printf '<shim> restarted %s\\n' "$1" ;;
  rm)      printf '<shim> removed %s\\n' "$2" ;;
  logs)    printf '<shim> logs of %s: mysql-ready-conn\\n' "${!#}" ;;
esac
"""


def make_docker_shim(tmp_path):
    bin_dir = tmp_path / "shim-bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "docker").write_text(DOCKER_SHIM, encoding="utf-8")
    (bin_dir / "docker").chmod(0o755)
    return bin_dir


def with_shim(env, bin_dir):
    return {**env, "PATH": f"{bin_dir}:{os.environ['PATH']}"}


def shim_log(bin_dir):
    return (bin_dir / "docker-shim.log").read_text(encoding="utf-8")


def add_minio_catalog(stack):
    (stack / "catalog/minio").mkdir()
    (stack / "catalog/minio/profile").write_text("storage\\n", encoding="utf-8")


def test_compose_project_name_fallback_chain(tmp_path):
    # 1) compose.yaml 顶层 name 优先（高于环境变量）
    _, env = make_stack(tmp_path, compose="name: yaml-proj\n\nservices:\n  mysql:\n    image: mysql:8.4\n")
    rc, out, _ = sh(SRC + "compose_project_name", {**env, "CADENCE_COMPOSE_PROJECT": "env-proj"})
    assert rc == 0 and out == "yaml-proj"
    # 2) 无顶层 name → 环境变量 CADENCE_COMPOSE_PROJECT
    _, env = make_stack(tmp_path / "s2", compose="services:\n  mysql:\n    image: mysql:8.4\n")
    rc, out, _ = sh(SRC + "compose_project_name", {**env, "CADENCE_COMPOSE_PROJECT": "env-proj"})
    assert rc == 0 and out == "env-proj"
    # 3) 都无 → cadence
    rc, out, _ = sh(SRC + "compose_project_name", {**env, "CADENCE_COMPOSE_PROJECT": ""})
    assert rc == 0 and out == "cadence"


def test_status_lists_all_services_with_healthy(tmp_path):
    stack, env = make_stack(tmp_path)
    add_minio_catalog(stack)                        # 四服务：mysql redis rabbitmq minio
    bin_dir = make_docker_shim(tmp_path)
    rc, out, err = sh(SRC + "stack_status", with_shim(env, bin_dir))
    assert rc == 0, err
    for svc in ("mysql", "redis", "rabbitmq", "minio"):
        assert svc in out
    assert "healthy" in out                         # mysql/redis/minio 状态透出
    assert "3306" in out                            # 端口透出
    assert "未启动" in out                          # rabbitmq 无容器
    assert "端口 Up" not in out                     # 无端口服务（minio）不得把状态串误当端口
    log = shim_log(bin_dir)                         # label 直连 docker ps（非 compose 插件）
    assert "--filter label=com.docker.compose.project=cadence" in log
    assert "--filter label=com.docker.compose.service=mysql" in log


def test_restart_by_label_cid(tmp_path):
    _, env = make_stack(tmp_path)
    bin_dir = make_docker_shim(tmp_path)
    rc, out, err = sh(SRC + "stack_restart mysql", with_shim(env, bin_dir))
    assert rc == 0 and "cid-mysql-111" in out, err
    assert "restart cid-mysql-111" in shim_log(bin_dir)


def test_restart_missing_container_chinese_error(tmp_path):
    _, env = make_stack(tmp_path)
    bin_dir = make_docker_shim(tmp_path)
    rc, out, err = sh(SRC + "stack_restart nosuch", with_shim(env, bin_dir))
    assert rc != 0 and "未找到" in err


def test_logs_passthrough_args(tmp_path):
    _, env = make_stack(tmp_path)
    bin_dir = make_docker_shim(tmp_path)
    rc, out, err = sh(SRC + "stack_logs mysql --tail 100 -f", with_shim(env, bin_dir))
    assert rc == 0 and "mysql-ready-conn" in out, err
    assert "--tail 100 -f cid-mysql-111" in shim_log(bin_dir)


def test_rm_removes_container_by_label(tmp_path):
    stack, env = make_stack(tmp_path)
    bin_dir = make_docker_shim(tmp_path)
    rc, out, err = sh(SRC + "stack_rm_service mysql", with_shim(env, bin_dir))
    assert rc == 0, err
    assert "rm -f cid-mysql-111" in shim_log(bin_dir)
    assert "mysql:" not in (stack / "compose.yaml").read_text(encoding="utf-8")


def test_cli_logs_wiring(tmp_path):
    _, env = make_stack(tmp_path)
    bin_dir = make_docker_shim(tmp_path)
    cli = f'"{REPO / "devbox" / "stack" / "stack.sh"}" logs mysql'
    rc, out, err = sh(cli, with_shim(env, bin_dir))
    assert rc == 0 and "mysql-ready-conn" in out, err
    assert "--tail 100 -f cid-mysql-111" in shim_log(bin_dir)



def test_status_no_duplicate_under_pipefail(tmp_path):
    """回归：pipefail 下 extras 去重不得因 grep -q 早退 SIGPIPE 误判（曾致 status 双打印）。

    shim 提供两个均在 catalog 中的容器（mysql 非末行/redis 末行），
    任何 pipefail 组合下每个服务只允许出现一次。
    """
    cat = tmp_path / "catalog"
    for svc in ("mysql", "redis"):
        (cat / svc).mkdir(parents=True)
        (cat / svc / "profile").write_text("default\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "docker"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = \"ps\" ] && echo \"$@\" | grep -q service= ; then\n"
        "  case \"$*\" in\n"
        "    *service=mysql*) printf 'Up 1 hour|127.0.0.1:3306->3306/tcp\\n' ;;\n"
        "    *service=redis*) printf 'Up 1 hour|127.0.0.1:6379->6379/tcp\\n' ;;\n"
        "  esac\n"
        "else\n"
        "  printf 'mysql\\nredis\\n'\n"
        "fi\n"
    )
    shim.chmod(0o755)
    rc, out, err = sh(
        'set -o pipefail; source "%s"; stack_status' % LIB,
        env_extra={
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "CADENCE_STACK_CATALOG_DIR": str(cat),
            "CADENCE_COMPOSE_PROJECT": "cadence",
        },
    )
    assert rc == 0, err
    names = [ln.split()[0] for ln in out.splitlines() if ln.startswith("  ")]
    assert names == ["mysql", "redis"], f"pipefail 下 status 服务重复或缺失：{names}"
