"""deny 双分类 gate（oracle 拍板点 1 / eval-trajectory-scoring R2）。

受管区块内 deny（拦截规则属 cadence-managed:permission-gate 区块）不判
FAIL，转改道率子度量：N 步内改用 preferred 工具=PASS；改道失败或放弃才
FAIL。区块外 deny 或 is_error → FAIL（harness 配置错误归类）。归属判定读
结果 JSON 携带的 settings_snapshot（fixture .claude/settings.json 受管区块）。
"""
GATE_BEGIN = "@@cadence-managed:permission-gate:v1:start@@"
GATE_END = "@@cadence-managed:permission-gate:v1:end@@"
DEFAULT_WINDOW = 8
DEFAULT_PREFERRED = "codegraph|ast-grep"


def managed_deny_entries(settings_snapshot: dict) -> set:
    perms = (settings_snapshot or {}).get("permissions")
    if not isinstance(perms, dict) or not isinstance(perms.get("deny"), list):
        return set()
    deny = perms["deny"]
    entries = set()
    inside = False
    for item in deny:
        if item == GATE_BEGIN:
            inside = True
            continue
        if item == GATE_END:
            inside = False
            continue
        if inside and isinstance(item, str) and not item.startswith("❌"):
            entries.add(item)
    return entries


def _matches_entry(entry: str, tool: str, args_digest: str = "") -> bool:
    """条目匹配：裸名（Grep）精确匹配工具名；带参条目（Bash(grep:*)）在工具名
    相等之外加验参数前缀（命令头首词 == 限定符前缀），防 Bash(ls:*) 误吞 grep 拒绝。"""
    if "(" in entry and entry.endswith(")"):
        bare, qual = entry[:-1].split("(", 1)
        prefix = qual.split(":", 1)[0].strip()
        return bare.strip() == tool and bool(args_digest) \
            and args_digest.split(" ")[0] == prefix
    return entry == tool


def classify_denials(traj, settings_snapshot):
    managed_entries = managed_deny_entries(settings_snapshot)
    digest_by_index = {c.index: c.args_digest for c in traj.tool_calls}
    managed, unmanaged = [], []
    for denial in traj.denials:
        digest = digest_by_index.get(denial.at_index, "")
        if any(_matches_entry(e, denial.tool, digest) for e in managed_entries):
            managed.append(denial)
        else:
            unmanaged.append(denial)
    return {"managed": managed, "unmanaged": unmanaged}


def reroute_ok(traj, denial, window=DEFAULT_WINDOW, preferred_pattern=DEFAULT_PREFERRED):
    """拦截后 window 步内出现 preferred 工具调用即改道成功。"""
    import re
    rx = re.compile(preferred_pattern)
    for call in traj.tool_calls:
        if denial.at_index < call.index <= denial.at_index + window:
            if rx.search(call.tool) or rx.search(call.args_digest):
                return True
    return False


def apply_deny_gate(traj, probe):
    out = {"managed": 0, "unmanaged": 0, "abandoned": 0, "rerouted": 0,
           "silent_errors": 0}
    classified = classify_denials(traj, traj.settings_snapshot)
    out["unmanaged"] = len(classified["unmanaged"])
    managed_idx = {d.at_index for d in classified["managed"]}
    for denial in classified["managed"]:
        out["managed"] += 1
        if reroute_ok(traj, denial):
            out["rerouted"] += 1
        else:
            out["abandoned"] += 1
    out["silent_errors"] = sum(
        1 for c in traj.tool_calls if c.is_error and c.index not in managed_idx)
    return out
