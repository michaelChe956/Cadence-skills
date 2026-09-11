#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cadence-box.yaml → 五端 CLI 认证/模型配置渲染器。

事实基线：eval/docker/container.py::_copy_auth（夜测五端「能用」最小集，2026-09-11 本机结构实证）。
仅依赖 stdlib + PyYAML。渲染采用「临时目录全量渲染后逐文件 os.replace 原子替换」。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path

import yaml

AGENT_KEYS = ("claude", "codex", "pi", "kimi", "omp")
MODEL_REQUIRED = ("claude", "codex", "omp")     # pi/kimi 可省略 model，默认取 provider.models[0].id
DEFAULT_API = "openai-completions"              # providers.<id>.api 缺省（pi/omp）；claude 侧透传 base_url
DEFAULT_WIRE_API = "responses"                  # providers.<id>.wire_api 缺省（codex）
RENDER_TMP_DIRNAME = ".cadence-render-tmp"
LINES_KEY = "__lines__"


# ---------------- 解析 ----------------

def _key_lines(text: str) -> dict:
    """键路径 → YAML 行号（供报错定位；flow 映射同样覆盖）。"""
    lines: dict = {}

    def walk(node, prefix):
        if not isinstance(node, yaml.MappingNode):
            return
        for k, v in node.value:
            if isinstance(k, yaml.ScalarNode):
                path = f"{prefix}.{k.value}" if prefix else str(k.value)
                lines[path] = k.start_mark.line + 1
                walk(v, path)

    try:
        walk(yaml.compose(text), "")
    except yaml.YAMLError:
        pass
    return lines


def parse_config(path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"cadence-box.yaml 不存在：{path}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"无法读取 {path}：{e}")
    try:
        cfg = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise SystemExit(f"cadence-box.yaml 不是合法 YAML：{e}")
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        raise SystemExit("cadence-box.yaml 顶层必须是映射（git/providers/agents）")
    cfg[LINES_KEY] = _key_lines(text)
    return cfg


# ---------------- 校验 ----------------

def validate(cfg: dict) -> list:
    errs: list = []
    lines = cfg.get(LINES_KEY, {})

    def err(path, msg):
        ln = lines.get(path)
        loc = f"第 {ln} 行附近：" if ln else ""
        errs.append(f"cadence-box.yaml {loc}{path}：{msg}")

    git = cfg.get("git")
    if not isinstance(git, dict):
        err("git", "缺少 git 段（name/email）")
    else:
        if not str(git.get("name") or "").strip():
            err("git.name", "git.name 为空（容器内提交身份必需）")
        if not str(git.get("email") or "").strip():
            err("git.email", "git.email 为空（容器内提交身份必需）")

    providers = cfg.get("providers")
    if not isinstance(providers, dict) or not providers:
        err("providers", "至少需要定义一个 provider（base_url/api_key/models）")
    else:
        for pname, pv in providers.items():
            if not isinstance(pv, dict):
                err(f"providers.{pname}", "必须是映射")
                continue
            bu = str(pv.get("base_url") or "").strip()
            if not bu:
                err(f"providers.{pname}.base_url", "缺少 base_url")
            elif not bu.startswith(("http://", "https://")):
                err(f"providers.{pname}.base_url", "base_url 必须以 http:// 或 https:// 开头")
            if not str(pv.get("api_key") or "").strip():
                err(f"providers.{pname}.api_key", "缺少 api_key（出于安全不回显其值）")
            for i, m in enumerate(pv.get("models") or []):
                if not isinstance(m, dict) or not str(m.get("id") or "").strip():
                    err(f"providers.{pname}.models[{i}]", "缺少模型 id")

    agents = cfg.get("agents")
    if not isinstance(agents, dict):
        err("agents", "缺少 agents 段（claude/codex/pi/kimi/omp 五端必配）")
        agents = {}
    for a in AGENT_KEYS:
        spec = agents.get(a)
        if not isinstance(spec, dict):
            err(f"agents.{a}", "缺少 agents.%s（五端必配）" % a)
            continue
        pname = spec.get("provider")
        if not str(pname or "").strip():
            err(f"agents.{a}.provider", "缺少 provider")
        elif not isinstance(providers, dict) or pname not in providers:
            err(f"agents.{a}.provider", f"指向未定义的 provider「{pname}」")
        elif a in MODEL_REQUIRED and not str(spec.get("model") or "").strip():
            err(f"agents.{a}.model", f"agents.{a} 必须指定 model")
        elif a not in MODEL_REQUIRED and not spec.get("model"):
            pv = providers.get(pname) or {}
            if not (isinstance(pv.get("models"), list) and pv["models"]):
                err(f"agents.{a}.model",
                    f"未指定 model 且 provider「{pname}」的 models 为空，无法取默认模型")
    return errs


# ---------------- 工具 ----------------

def _ctx_to_int(ctx) -> int:
    s = str(ctx).strip().lower()
    mult = 1
    if s.endswith(("k", "m", "g")):
        mult = {"k": 1024, "m": 1024 * 1024, "g": 1024 ** 3}[s[-1]]
        s = s[:-1]
    if not s.isdigit():
        raise ValueError(f"无法解析模型上下文长度：{ctx}")
    return int(s) * mult


def _deep_merge(base: dict, extra: dict) -> dict:
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


_TOML_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


def _toml_key(k: str) -> str:
    return k if _TOML_KEY.match(k) else json.dumps(str(k), ensure_ascii=False)


def _toml_val(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_val(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def _toml_dump(data: dict) -> str:
    out: list = []

    def emit(d, prefix):
        tables = []
        for k, v in d.items():
            if isinstance(v, dict) and v:
                tables.append((k, v))
            elif isinstance(v, dict):
                out.append(f"{_toml_key(k)} = {{}}")
            else:
                out.append(f"{_toml_key(k)} = {_toml_val(v)}")
        for k, v in tables:
            sect = f"{prefix}.{_toml_key(k)}" if prefix else _toml_key(k)
            out.append("")
            out.append(f"[{sect}]")
            emit(v, sect)

    emit(data, "")
    return "\n".join(out).strip("\n") + "\n"


def _serialize(fmt: str, payload) -> str:
    if fmt == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if fmt == "yaml":
        return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, default_flow_style=False)
    if fmt == "toml":
        return _toml_dump(payload)
    return payload  # text


def _provider(cfg, agent):
    name = cfg["agents"][agent]["provider"]
    return name, cfg["providers"][name]


def _model_list(pv: dict) -> list:
    return pv.get("models") or []


def _model_of(cfg, agent) -> str:
    m = cfg["agents"][agent].get("model")
    if m:
        return str(m)
    ms = _model_list(_provider(cfg, agent)[1])
    if not ms:
        raise ValueError(f"agents.{agent} 未指定 model 且 provider 无 models，无法取默认模型")
    return str(ms[0]["id"])


def _raw(cfg, agent) -> dict:
    return cfg["agents"][agent].get("raw") or {}

# ---------------- 各端渲染目标 ----------------

def _targets_claude(cfg) -> dict:
    _, pv = _provider(cfg, "claude")
    model = _model_of(cfg, "claude")
    settings = _deep_merge({
        "env": {
            "ANTHROPIC_AUTH_TOKEN": pv["api_key"],
            "ANTHROPIC_BASE_URL": pv["base_url"],
            "ANTHROPIC_MODEL": model,
            "ANTHROPIC_REASONING_MODEL": model,
        },
        "tui": "default",
        "theme": "auto",
    }, _raw(cfg, "claude"))
    return {
        ".claude/settings.json": ("json", settings),
        ".claude/.credentials.json": ("json", {}),   # token 模式不消费；保持 _copy_auth 清单形态
    }


def _targets_codex(cfg) -> dict:
    _, pv = _provider(cfg, "codex")
    model = _model_of(cfg, "codex")
    toml = _deep_merge({
        "model_provider": "cadence",
        "model": model,
        "model_catalog_json": "~/.codex/models.json",
        "model_reasoning_effort": "high",
        "disable_response_storage": True,
        "model_providers": {
            "cadence": {
                "name": "cadence",
                "base_url": pv["base_url"],
                "wire_api": pv.get("wire_api", DEFAULT_WIRE_API),
                "requires_openai_auth": True,
            }
        },
    }, _raw(cfg, "codex"))
    models = _deep_merge({"models": [{
        "slug": m["id"],
        "display_name": m.get("name", m["id"]),
        "description": "cadence-box provider model",
        "context_window": _ctx_to_int(m.get("ctx", 128000)),
        "max_context_window": _ctx_to_int(m.get("ctx", 128000)),
        "supported_in_api": True,
        "visibility": "list",
        "priority": 0,
    } for m in _model_list(pv)]}, _raw(cfg, "codex"))
    return {
        ".codex/config.toml": ("toml", toml),
        ".codex/auth.json": ("json", {"OPENAI_API_KEY": pv["api_key"]}),
        ".codex/models.json": ("json", models),
    }


def _targets_pi(cfg) -> dict:
    name, pv = _provider(cfg, "pi")
    models = _deep_merge({"providers": {name: {
        "baseUrl": pv["base_url"],
        "api": pv.get("api", DEFAULT_API),
        "apiKey": pv["api_key"],
        "models": [{
            "id": m["id"],
            "name": m.get("name", m["id"]),
            "contextWindow": _ctx_to_int(m.get("ctx", 128000)),
            "maxTokens": m.get("max_tokens", 131072),
        } for m in _model_list(pv)],
    }}}, _raw(cfg, "pi"))
    settings = _deep_merge({
        "defaultProvider": name,
        "defaultModel": _model_of(cfg, "pi"),
        "defaultThinkingLevel": "high",
        # 注意：绝不写 packages 键——_copy_auth 实证须剔除（防首启拉 275MB 扩展包）
    }, _raw(cfg, "pi"))
    return {
        ".pi/agent/models.json": ("json", models),
        ".pi/agent/auth.json": ("json", {}),          # 实证为空对象
        ".pi/agent/settings.json": ("json", settings),
    }


def _targets_kimi(cfg) -> dict:
    name, pv = _provider(cfg, "kimi")
    model = _model_of(cfg, "kimi")
    toml = _deep_merge({
        "default_model": f"{name}/{model}",
        "providers": {name: {
            "type": "openai",
            "base_url": pv["base_url"],
            "api_key": pv["api_key"],
        }},
        "models": {f"{name}/{model}": {
            "provider": name,
            "model": model,
            "max_context_size": (_ctx_to_int(_model_list(pv)[0].get("ctx", 262144))
                                 if _model_list(pv) else 262144),
            "display_name": model,
        }},
    }, _raw(cfg, "kimi"))
    return {
        ".kimi-code/config.toml": ("toml", toml),
        ".kimi-code/credentials/kimi-code.json": ("json", {
            "access_token": "", "refresh_token": "", "expires_at": 0,
            "scope": "kimi-code", "token_type": "Bearer", "expires_in": 0,
        }),                                            # 空占位 token 结构（本机实证）
        ".kimi-code/device_id": ("text", str(uuid.uuid4()) + "\n"),
        ".kimi-code/region": ("text", "cn\n"),
        ".kimi-code/oauth/kimi-code": ("text", ""),   # 空文件（本机实证）
    }


def _targets_omp(cfg) -> dict:
    name, pv = _provider(cfg, "omp")
    model = _model_of(cfg, "omp")
    models_yml = _deep_merge({"providers": {name: {
        "baseUrl": pv["base_url"],
        "api": pv.get("api", DEFAULT_API),
        "apiKey": pv["api_key"],
        "models": [{
            "id": m["id"],
            "name": m.get("name", m["id"]),
            "contextWindow": _ctx_to_int(m.get("ctx", 128000)),
            "maxTokens": m.get("max_tokens", 131072),
            "reasoning": False,
            "input": ["text"],
        } for m in _model_list(pv)],
    }}}, _raw(cfg, "omp"))
    config_yml = _deep_merge({
        "setupVersion": 2,
        "defaultThinkingLevel": "high",
        "modelRoles": {r: f"{name}/{model}"
                      for r in ("default", "smol", "slow", "vision", "plan")},
    }, _raw(cfg, "omp"))
    return {
        ".omp/agent/models.yml": ("yaml", models_yml),
        ".omp/agent/config.yml": ("yaml", config_yml),
    }


def _targets_git(cfg) -> dict:
    g = cfg["git"]
    return {".gitconfig": ("text", (
        "# 由 cadence render-auth 生成；core 对齐值与 entrypoint 步骤 1 一致（设计 4.5）\n"
        "[user]\n"
        f"\tname = {g['name']}\n"
        f"\temail = {g['email']}\n"
        "[core]\n"
        "\tautocrlf = true\n"
        "\tfilemode = false\n"
    ))}


def _build_targets(cfg) -> dict:
    targets: dict = {}
    for fn in (_targets_claude, _targets_codex, _targets_pi,
               _targets_kimi, _targets_omp, _targets_git):
        targets.update(fn(cfg))
    return targets


# ---------------- 渲染主流程 ----------------

def render_all(cfg: dict, home) -> None:
    errs = validate(cfg)
    if errs:
        raise ValueError("；".join(errs))
    home = Path(home)
    tmp_root = home / RENDER_TMP_DIRNAME
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True)
    targets = _build_targets(cfg)
    # 阶段一：全量渲染到临时目录（任一失败即抛出，不触碰正式位置）
    for rel, (fmt, payload) in targets.items():
        dst = tmp_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(_serialize(fmt, payload), encoding="utf-8")
    # 阶段二：逐文件原子替换（os.replace 同文件系统内原子）
    for rel in targets:
        final = home / rel
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_root / rel, final)
    shutil.rmtree(tmp_root)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="cadence-box.yaml → 五端认证/模型配置渲染器")
    ap.add_argument("--config", required=True, help="cadence-box.yaml 路径（容器内 /cadence/auth.yaml）")
    ap.add_argument("--home", required=True, help="目标用户主目录")
    args = ap.parse_args(argv)
    cfg = parse_config(args.config)
    errs = validate(cfg)
    if errs:
        for e in errs:
            print(f"[render-auth] {e}", file=sys.stderr)
        return 2
    render_all(cfg, Path(args.home))
    print("[render-auth] 五端配置渲染完成：claude/codex/pi/kimi/omp + .gitconfig", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
