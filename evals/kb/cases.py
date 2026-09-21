"""kb-eval 价值实验案例集（两 arm 共享：prompt 完全一致，唯一变量=是否提供知识库环境）。

检查项为可审计的确定性判据：require_all（须全部出现）/ require_any（至少一个）/
forbid（不得出现）。判据只做"业务事实是否被表达"的机械核验，报告同时附回答原文供人工复核。
"""

SCENARIOS = {
    "S1": "能力组合发现：从分散接口发现可复用的新能力",
    "S2": "业务规则引用与遵守：避免为满足需求而破坏业务约束",
    "S3": "变更影响分析：一次找到跨层影响，降低遗漏",
    "S4": "故障排查：找到规则来源，同时克制根因臆断",
    "S5": "架构与方案评审：用规则基线拦住危险方案",
}

# 每个检查项：{"id", "desc", "require_all", "require_any", "forbid"}
# 全空判据 = 仅收录不判定（unknown），用于开放性问题
CASES = [
    # ═══ S1 能力组合发现 ═══
    {
        "id": "S1-A", "scenario": "S1", "title": "基本信息 + 账户信息组合",
        "prompt": ("运营希望按用户查看「基本信息 + 账户信息」。请基于当前项目说明："
                   "已有能力如何组合、各自真实入口、关联字段、是否已有可直接调用的聚合接口，"
                   "以及上线前必须确认的限制。不要实现代码；每项结论请给可核查来源。"),
        "checks": [
            {"id": "S1A-1", "desc": "找对两个真实入口（用户基本信息 / 账户查询）",
             "require_groups": [
                 ["/api/user/basic", "UserBasicController", "user/basic"],
                 ["/api/account", "AccountController"]]},
            {"id": "S1A-2", "desc": "指出 userId 为关联键",
             "require_any": ["userId", "user_id"]},
            {"id": "S1A-3", "desc": "明确当前没有可直接调用的聚合接口（可组合 ≠ 已实现）",
             "require_any": ["未实现", "没有聚合", "不存在聚合", "无聚合", "需新建", "需要新增", "未提供聚合", "没有现成", "无现成", "不存在现成", "需要组合"]},
            {"id": "S1A-4", "desc": "指出账户记录基数/唯一性未证实（限制项）",
             "require_any": ["唯一性", "唯一约束", "无唯一", "一户多", "多账户", "一对一", "基数", "可能多条", "未证实", "无法保证", "待确认"]},
        ],
    },
    {
        "id": "S1-B", "scenario": "S1", "title": "用户全景报表方案（跨三域）",
        "prompt": ("需要一份「用户基本信息 + 账户 + 订单」的运营全景报表。请设计最小数据获取方案："
                   "哪些现有能力可复用、如何关联、关联基数和缺失数据如何处理、哪些关键问题目前还没有证据。"
                   "不要把尚未实现的能力当成现成 API。"),
        "checks": [
            {"id": "S1B-1", "desc": "覆盖三个数据域",
             "require_groups": [
                 ["/api/user", "t_user", "UserBasic", "用户基本"],
                 ["/api/account", "t_user_account", "Account"],
                 ["/api/order", "t_order", "order-service", "订单"]]},
            {"id": "S1B-2", "desc": "明确订单维组合无现成能力或需新增",
             "require_any": ["需新增", "需要新增", "未提供", "没有现成", "不存在", "需新建", "待确认"]},
            {"id": "S1B-3", "desc": "给出关联键", "require_any": ["userId", "user_id"]},
        ],
    },
    # ═══ S2 业务规则引用与遵守 ═══
    {
        "id": "S2-A", "scenario": "S2", "title": "已取消订单要求发货",
        "prompt": ("运营要求已取消的订单也能直接点击「发货」，理由是货物已经打包。"
                   "请判断当前系统是否允许，说明涉及的状态前置条件和证据，"
                   "并给出不绕过现有业务约束的处理建议。不要修改代码。"),
        "checks": [
            {"id": "S2A-1", "desc": "明确拒绝：已取消订单不可直接发货",
             "require_all": ["CANCELLED"],
             "require_any": ["不可", "不允许", "不能", "拒绝", "违反"]},
            {"id": "S2A-2", "desc": "指出现有发货前置条件为 PAID",
             "require_all": ["PAID"]},
            {"id": "S2A-3", "desc": "给出不绕过约束的处理建议",
             "require_any": ["业务确认", "业务批准", "业务评审", "产品", "财务评审", "审批", "评审", "重新下单", "新建订单", "扩展状态机", "恢复订单", "恢复为 PAID", "不变量"]},
            {"id": "S2A-4", "desc": "不提出绕过约束的直接改状态方案",
             "forbid": ["直接 UPDATE status 为 SHIPPED", "直接改数据库状态即可"]},
        ],
    },
    # ═══ S3 变更影响分析 ═══
    {
        "id": "S3-A", "scenario": "S3", "title": "user_name 长度 64 → 128 影响分析",
        "prompt": ("计划将用户姓名字段 user_name 的最大长度从 64 调整为 128。请只做变更影响分析："
                   "列出数据库、实体/映射、查询接口、前端页面等需要修改或需要核验的具体位置，"
                   "说明每个位置的依赖关系和验证建议；没有长度限制的地方不要硬说必须修改。"),
        "checks": [
            {"id": "S3A-1", "desc": "定位 DDL 中 VARCHAR(64) 定义",
             "require_all": ["VARCHAR(64)"]},
            {"id": "S3A-2", "desc": "覆盖数据层与代码层影响",
             "require_any": ["init.sql", "DDL", "t_user"]},
            {"id": "S3A-3", "desc": "覆盖实体/Mapper 或接口层",
             "require_any": ["UserEntity", "UserMapper", "UserBasicController", "entity", "mapper", "Mapper"]},
            {"id": "S3A-4", "desc": "覆盖前端页面层",
             "require_any": ["web-portal", "UserList", "前端", "页面"]},
        ],
    },
    # ═══ S4 故障排查 ═══
    {
        "id": "S4-A", "scenario": "S4", "title": "账户余额出现负数",
        "prompt": ("测试发现账户余额出现负数。请基于项目排查：余额非负规则在哪里定义，"
                   "当前数据库和已提供的代码是否真正保证它，哪些事实已经确认，"
                   "哪些写入路径或运行数据还需要补充。给出下一步排查顺序，"
                   "不要把未看到的扣款逻辑写成已确认根因。"),
        "checks": [
            {"id": "S4A-1", "desc": "找到非负规则来源（余额表注释，非积分/库存等影子域）",
             "require_any": ["余额不可为负", "余额不允许", "余额不能为负", "余额不得为负",
                             "余额字段不允许出现负值"]},
            {"id": "S4A-2", "desc": "指出 DDL 未声明 CHECK 约束（注释≠强制）",
             "require_any": ["CHECK", "没有约束", "未声明", "不强制", "无法保证", "不能保证"]},
            {"id": "S4A-3", "desc": "不臆断扣款逻辑为已确认根因",
             "forbid": ["根因就是扣款代码", "确认是扣款逻辑导致"]},
            {"id": "S4A-4", "desc": "给出下一步排查方向",
             "require_any": ["写入", "扣款", "更新", "排查"]},
        ],
    },
    # ═══ S5 架构与方案评审 ═══
    {
        "id": "S5-A", "scenario": "S5", "title": "评审：发货条件放宽为 PAID 或 CREATED",
        "prompt": ("评审下面的变更提案：把发货条件从「仅 PAID」放宽为「PAID 或 CREATED」，"
                   "其他流程不变，以提升履约速度。请给出是否可直接上线的结论、违反的现有约束、"
                   "受影响的业务路径、必须补充的设计和验证。请区分现有代码事实、规则基线和待业务确认事项。"),
        "checks": [
            {"id": "S5A-1", "desc": "结论：不可直接上线",
             "require_any": ["不可直接", "不能直接", "不建议", "不应", "受阻", "不可上线", "不能上线", "不满足", "不予放行", "暂不具备"]},
            {"id": "S5A-2", "desc": "指出 CREATED 未满足已支付前提",
             "require_all": ["CREATED", "PAID"]},
            {"id": "S5A-3", "desc": "要求业务批准/流程重设计而非仅改代码",
             "require_any": ["业务批准", "业务确认", "重设计", "需产品", "审批"]},
        ],
    },
    {
        "id": "S5-B", "scenario": "S5", "title": "评审：零业务侵入的全景 API 提案",
        "prompt": ("评审一项「零业务侵入」的用户全景 API 提案：直接用 user_id 拼接用户、账户和订单查询结果，"
                   "宣称现有接口足以保证每人只有一个账户、不会缺失记录，因此无需补充约束或验证。"
                   "请逐项判断哪些承诺有证据，哪些没有，并给出上线门禁。"),
        "checks": [
            {"id": "S5B-1", "desc": "指出「每人一个账户」的承诺无证据",
             "require_any": ["唯一性", "未证实", "无证据", "没有证据", "无法保证", "未提供约束"]},
            {"id": "S5B-2", "desc": "指出「不会缺失记录」的承诺无证据",
             "require_any": ["完整性", "缺失", "未证实", "无证据", "无法保证"]},
            {"id": "S5B-3", "desc": "给出上线门禁项",
             "require_any": ["门禁", "前置条件", "必须补", "需补充", "验证"]},
        ],
    },
]

DEFAULT_CASES = [c["id"] for c in CASES]


def get(pids):
    """按 id 列表取案例（大小写不敏感，支持场景前缀如 S1）。"""
    if not pids:
        return list(CASES)
    sel = []
    for c in CASES:
        if c["id"].lower() in [p.lower() for p in pids] or c["scenario"].lower() in [p.lower() for p in pids]:
            sel.append(c)
    return sel


def judge(case, text):
    """确定性判据：返回 [{id, desc, verdict(pass|fail|unknown), reason}]。"""
    out = []
    for ck in case.get("checks", []):
        req_all = ck.get("require_all", [])
        req_any = ck.get("require_any", [])
        forbid = ck.get("forbid", [])
        groups = ck.get("require_groups", [])
        if not (req_all or req_any or forbid or groups):
            out.append({**ck, "verdict": "unknown", "reason": "开放判据，需人工复核"})
            continue
        miss_all = [k for k in req_all if k not in text]
        hit_any = [k for k in req_any if k in text]
        hit_forbid = [k for k in forbid if k in text]
        miss_groups = [g for g in groups if not any(k in text for k in g)]
        if hit_forbid:
            out.append({**ck, "verdict": "fail", "reason": f"命中禁止项: {hit_forbid}"})
        elif miss_all:
            out.append({**ck, "verdict": "fail", "reason": f"缺少必需项: {miss_all}"})
        elif miss_groups:
            out.append({**ck, "verdict": "fail",
                        "reason": "未覆盖: " + "；".join("[" + "/".join(g[:3]) + "]" for g in miss_groups)})
        elif req_any and not hit_any:
            out.append({**ck, "verdict": "fail", "reason": f"未表达（任一应有: {req_any[:3]}…）"})
        else:
            why = "已表达"
            if groups:
                why = "各维度均覆盖"
            out.append({**ck, "verdict": "pass", "reason": why})
    return out
