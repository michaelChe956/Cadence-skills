#!/usr/bin/env python3
"""生成 large fixture：standard 全量 + 12 个噪声服务（关键词影子，不改答案）。

设计约束（保证 B1 案例答案不被污染）：
- 类名撞车：UserBasicController/AccountController/AccountService/OrderService/UserMapper
  在 com.demo.legacy.* 同名复用（不同包/端口/表）
- 关键词投影：发货/取消/用户/账户/订单/报表/导出等中文词大量出现
- 禁止污染答案：不加 user_name VARCHAR(64)、不加第二条「余额」规则、
  不加第二个「订单发货」状态机、影子域规则措辞避开 S4A-1 判据词
用法：python3 gen_large.py   （幂等：先删 large/ 再重建）
"""
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
STD = HERE / "standard"
LARGE = HERE / "large"

APP_TMPL = """package com.demo.{pkg};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** {desc} */
@SpringBootApplication
public class {Svc}Application {{
    public static void main(String[] args) {{
        SpringApplication.run({Svc}Application.class, args);
    }}
}}
"""

ENT_TMPL = """package com.demo.{pkg}.entity;

/** {desc}：对应 {table} 表 */
public class {Ent} {{
{fields}
    public {Ent}() {{}}
}}
"""

MAPPER_TMPL = """package com.demo.{pkg}.mapper;

import com.demo.{pkg}.entity.{Ent};
import org.apache.ibatis.annotations.Mapper;

/** {desc} */
@Mapper
public interface {Ent}Mapper {{
    {Ent} selectById(Long id);

    int insert({Ent} entity);
}}
"""

SVC_TMPL = """package com.demo.{pkg}.service;

import com.demo.{pkg}.entity.{Ent};
import com.demo.{pkg}.mapper.{Ent}Mapper;
import org.springframework.stereotype.Service;

/** {desc} */
@Service
public class {Cls} {{
    private final {Ent}Mapper {var}Mapper;

    public {Cls}({Ent}Mapper {var}Mapper) {{
        this.{var}Mapper = {var}Mapper;
    }}
{methods_body}
}}
"""

CTRL_TMPL = """package com.demo.{pkg}.controller;

import com.demo.{pkg}.entity.{Ent};
import com.demo.{pkg}.service.{Cls};
import org.springframework.web.bind.annotation.*;

/** {desc} */
@RestController
@RequestMapping("{base}")
public class {Ctrl} {{
    private final {Cls} {var};

    public {Ctrl}({Cls} {var}) {{
        this.{var} = {var};
    }}
{endpoints_body}
}}
"""

XML_TMPL = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.demo.{pkg}.mapper.{Ent}Mapper">
    <select id="selectById" resultType="com.demo.{pkg}.entity.{Ent}">
        SELECT * FROM {table} WHERE id = #{{id}}
    </select>
    <insert id="insert">INSERT INTO {table} ({cols}) VALUES ({vals})</insert>
</mapper>
"""

YML_TMPL = """server:
  port: {port}
spring:
  application:
    name: {svc}
"""

POM_TMPL = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.demo</groupId>
  <artifactId>{svc}</artifactId>
  <version>1.0.0</version>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.0</version>
  </parent>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.mybatis.spring.boot</groupId>
      <artifactId>mybatis-spring-boot-starter</artifactId>
      <version>2.2.2</version>
    </dependency>
  </dependencies>
</project>
"""

SQL_TMPL = """-- {desc}（noise 模块，历史遗留系统拆分）
CREATE DATABASE IF NOT EXISTS {db};
USE {db};
{tables}
"""

TABLE_TMPL = """CREATE TABLE {table} (
{cols}
) COMMENT='{tcomment}';
"""


def java_fields(fields):
    out = []
    for fname, jtype, fcomment in fields:
        out.append(f"    /** {fcomment} */\n    private {jtype} {fname};\n")
    return "\n".join(out)


def emit_service(root, cfg):
    svc, pkg, port, desc = cfg["svc"], cfg["pkg"], cfg["port"], cfg["desc"]
    base = root / svc / "src/main/java/com/demo" / pkg.replace(".", "/")
    res = root / svc / "src/main/resources"
    (base / "controller").mkdir(parents=True, exist_ok=True)
    (base / "service").mkdir(parents=True, exist_ok=True)
    (base / "mapper").mkdir(parents=True, exist_ok=True)
    (base / "entity").mkdir(parents=True, exist_ok=True)
    (res / "mapper").mkdir(parents=True, exist_ok=True)

    (base / f"{cfg['app']}.java").write_text(
        APP_TMPL.format(pkg=pkg, Svc=cfg["app"], desc=desc), encoding="utf-8")
    (root / svc / "pom.xml").write_text(POM_TMPL.format(svc=svc), encoding="utf-8")
    (res / "application.yml").write_text(YML_TMPL.format(port=port, svc=svc), encoding="utf-8")
    (root / svc / "README.md").write_text(
        f"# {svc}\n\n{desc}。\n\n{cfg.get('readme', '')}\n\n> 历史遗留模块，接口语义以代码注释为准；"
        f"数据库初始化脚本见 `db/noise/{svc}.sql`。涉及{cfg.get('shadow', '相关')}的运营诉求先与本服务负责人对齐。\n",
        encoding="utf-8")

    for ent in cfg["entities"]:
        e, table, tcomment, fields = ent["ent"], ent["table"], ent["tcomment"], ent["fields"]
        (base / "entity" / f"{e}.java").write_text(
            ENT_TMPL.format(pkg=pkg, desc=ent["desc"], table=table,
                            Ent=e, fields=java_fields(fields)), encoding="utf-8")
        cols = ",\n".join(f"  {c} {t} COMMENT '{cc}'" for c, t, cc in fields)
        (root / "db/noise" / f"{svc}.sql").write_text(
            SQL_TMPL.format(desc=desc, db=cfg["db"],
                            tables=TABLE_TMPL.format(table=table, cols=cols, tcomment=tcomment)),
            encoding="utf-8")
        for m in ent.get("mappers", ["default"]):
            mapper_cls = f"{e}Mapper" if m == "default" else m
            (base / "mapper" / f"{mapper_cls}.java").write_text(
                MAPPER_TMPL.format(pkg=pkg, desc=f"{ent['desc']} 数据访问", Ent=e), encoding="utf-8")
        (res / "mapper" / f"{e}Mapper.xml").write_text(
            XML_TMPL.format(pkg=pkg, Ent=e, table=table,
                            cols=", ".join(f[0] for f in fields),
                            vals=", ".join(f"#{{{f[0]}}}" for f in fields)), encoding="utf-8")
        for s in ent.get("services", []):
            var = (e[0].lower() + e[1:])
            (base / "service" / f"{s['cls']}.java").write_text(
                SVC_TMPL.format(pkg=pkg, desc=s["desc"], Ent=e, Cls=s["cls"], var=var,
                                methods_body=s["methods"]),
                encoding="utf-8")
        for c in ent.get("controllers", []):
            var = (c["svc"][0].lower() + c["svc"][1:])
            (base / "controller" / f"{c['ctrl']}.java").write_text(
                CTRL_TMPL.format(pkg=pkg, desc=c["desc"], Ent=e, Cls=c["svc"],
                                 Ctrl=c["ctrl"], base=c["base"], var=var,
                                 endpoints_body=c["endpoints"]),
                encoding="utf-8")
    for extra in cfg.get("extras", []):
        p = base / extra["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(extra["text"], encoding="utf-8")


NOISE = [
    # ── 影子域：类名与核心服务撞车（最强 grep 毒）──
    dict(svc="legacy-user-service", pkg="legacy.user", db="demo_legacy_user", port=8091, app="LegacyUserApplication",
         desc="遗留用户中心（老商城拆分残留），维护会员基础档案",
         shadow="用户基本信息查询",
         readme="老商城时期的用户档案服务。`UserBasicController` 为当时的用户基本信息入口，"
                "已标记 @Deprecated，新业务禁止调用；新入口见 user-service。",
         entities=[dict(ent="UserEntity", table="t_legacy_user_profile",
                        tcomment="遗留用户档案表（只读，停写）",
                        desc="遗留用户档案",
                        fields=[("id", "BIGINT", "主键"), ("nickname", "VARCHAR(128)", "昵称"),
                                ("mobile_no", "VARCHAR(20)", "手机号"), ("reg_channel", "VARCHAR(16)", "注册渠道")],
                        mappers=["UserMapper"],
                        services=[dict(cls="UserBasicService", desc="遗留用户基本信息查询（废弃）",
                                       methods="""
    /** @deprecated 用户基本信息请走 user-service 的 /api/user/basic */
    public {Ent} queryBasic(Long id) {
        return {var}Mapper.selectById(id);
    }""")],
                        controllers=[dict(ctrl="UserBasicController", svc="UserBasicService",
                                          base="/api/legacy/member/basic",
                                          desc="遗留用户基本信息（废弃，勿与新用户中心混淆）",
                                          endpoints="""
    /** 遗留入口：按会员号查档案。新用户基本信息一律走 user-service */
    @GetMapping("/{memberId}")
    public UserEntity basic(@PathVariable Long memberId) {
        return {var}.queryBasic(memberId);
    }""")])]),
    dict(svc="legacy-account-service", pkg="legacy.account", db="demo_legacy_account", port=8092, app="LegacyAccountApplication",
         desc="遗留积分账户服务（老商城），管理会员积分账户",
         shadow="账户查询",
         readme="老积分账户。`AccountController`/`AccountService` 与新账户服务同名但语义不同："
                "本服务只管积分，不管资金余额。",
         entities=[dict(ent="AccountEntity", table="t_legacy_points_account",
                        tcomment="遗留积分账户表；本表积分字段不允许出现负数（硬性业务约束）",
                        desc="遗留积分账户",
                        fields=[("id", "BIGINT", "主键"), ("member_id", "BIGINT", "会员标识"),
                                ("points", "INT", "积分；业务规则：积分不可为负"),
                                ("status", "VARCHAR(16)", "状态 ACTIVE/FROZEN")],
                        mappers=["AccountMapper"],
                        services=[dict(cls="AccountService", desc="遗留积分账户查询（与资金账户无关）",
                                       methods="""
    /** 查会员积分账户。注意：这是积分，不是资金余额 */
    public {Ent} queryAccount(Long memberId) {
        return {var}Mapper.selectById(memberId);
    }""")],
                        controllers=[dict(ctrl="AccountController", svc="AccountService",
                                          base="/api/legacy/points",
                                          desc="遗留积分账户入口（废弃）",
                                          endpoints="""
    /** 积分账户查询。资金类账户请走 account-service */
    @GetMapping("/{memberId}")
    public AccountEntity points(@PathVariable Long memberId) {
        return {var}.queryAccount(memberId);
    }""")])]),
    dict(svc="legacy-trade-service", pkg="legacy.trade", db="demo_legacy_trade", port=8093, app="LegacyTradeApplication",
         desc="遗留预售交易服务（老商城），管理预售单生命周期",
         shadow="订单创建与取消",
         readme="老预售单系统。`OrderService` 与新订单服务同名但实体不同（预售单，非现货订单）。"
                "预售单只有创建/支付/作废三个动作，没有发货概念。",
         entities=[dict(ent="PreSaleEntity", table="t_presale_order",
                        tcomment="预售单表；status: CREATED/PAID/VOIDED，VOIDED 为作废终态（等同取消）",
                        desc="预售单",
                        fields=[("id", "BIGINT", "预售单号"), ("member_id", "BIGINT", "下单会员"),
                                ("status", "VARCHAR(16)", "CREATED/PAID/VOIDED"),
                                ("deposit", "DECIMAL(18,2)", "定金")],
                        mappers=["PreSaleMapper"],
                        services=[dict(cls="OrderService", desc="预售单服务（与新订单服务的现货订单无关）",
                                       methods="""
    /** 作废预售单（VOIDED 为终态，等同取消，不可恢复） */
    public void voidPreSale(Long preSaleId) {
        PreSaleEntity ps = preSaleEntityMapper.selectById(preSaleId);
        if ("PAID".equals(ps.getStatus())) {
            throw new IllegalStateException("已支付预售单不可直接作废，须走退款流程");
        }
    }""")],
                        controllers=[dict(ctrl="PreSaleController", svc="OrderService",
                                          base="/api/legacy/presale",
                                          desc="预售单入口",
                                          endpoints="""
    /** 作废（取消）预售单 */
    @PostMapping("/{preSaleId}/void")
    public void voidPresale(@PathVariable Long preSaleId) {
        {var}.voidPreSale(preSaleId);
    }""")])]),
    # ── 影子域：业务词投影 ──
    dict(svc="logistics-service", pkg="logistics", db="demo_logistics", port=8087, app="LogisticsApplication",
         desc="物流服务：运单管理与发货交接",
         shadow="发货/取消",
         readme="运单（shipment）域。运单发货与订单发货是两件事：订单域管状态机，本域管承运交接。",
         entities=[dict(ent="ShipmentEntity", table="t_shipment",
                        tcomment="运单表；status: CREATED/SIGNED/CANCELLED/DELIVERED",
                        desc="运单",
                        fields=[("id", "BIGINT", "运单号"), ("order_id", "BIGINT", "关联订单"),
                                ("status", "VARCHAR(16)", "CREATED/SIGNED/CANCELLED/DELIVERED"),
                                ("carrier", "VARCHAR(32)", "承运商")],
                        services=[dict(cls="ShipmentService", desc="运单发货交接（承运层，非订单状态机）",
                                       methods="""
    /** 运单发货：已取消的运单（CANCELLED）不可再次发货，仅 SIGNED 状态可交接承运 */
    public void deliver(Long shipmentId) {
        ShipmentEntity s = shipmentMapper.selectById(shipmentId);
        if ("CANCELLED".equals(s.getStatus())) {
            throw new IllegalStateException("已取消运单不可发货");
        }
    }""")],
                        controllers=[dict(ctrl="ShipmentController", svc="ShipmentService",
                                          base="/api/logistics/shipment",
                                          desc="运单发货入口",
                                          endpoints="""
    /** 运单发货交接 */
    @PostMapping("/{shipmentId}/deliver")
    public void deliver(@PathVariable Long shipmentId) {
        {var}.deliver(shipmentId);
    }""")])]),
    dict(svc="member-service", pkg="member", db="demo_member", port=8085, app="MemberApplication",
         desc="会员服务：等级、积分与成长值",
         shadow="用户等级/报表",
         entities=[dict(ent="MemberEntity", table="t_member_profile",
                        tcomment="会员档案表",
                        desc="会员档案",
                        fields=[("member_id", "BIGINT", "会员标识"), ("level", "VARCHAR(16)", "等级"),
                                ("growth", "INT", "成长值")],
                        services=[dict(cls="MemberService", desc="会员等级查询（供运营报表使用）",
                                       methods="""
    public {Ent} queryMember(Long memberId) {
        return {var}Mapper.selectById(memberId);
    }""")],
                        controllers=[dict(ctrl="MemberController", svc="MemberService",
                                          base="/api/member",
                                          desc="会员档案入口",
                                          endpoints="""
    @GetMapping("/profile/{memberId}")
    public MemberEntity profile(@PathVariable Long memberId) {
        return {var}.queryMember(memberId);
    }""")]),
                   dict(ent="PointsEntity", table="t_member_points",
                        tcomment="会员积分表；积分不允许出现负数（业务硬性约束），年末按子回扣落级",
                        desc="会员积分",
                        fields=[("id", "BIGINT", "主键"), ("member_id", "BIGINT", "会员"),
                                ("points", "INT", "积分；不可为负"), ("year", "INT", "年度")])]),
    dict(svc="payment-service", pkg="payment", db="demo_payment", port=8086, app="PaymentApplication",
         desc="支付服务：支付单与退款",
         shadow="订单支付/退款",
         entities=[dict(ent="PaymentEntity", table="t_payment_record",
                        tcomment="支付流水表；status: PENDING/SUCCESS/FAILED/REFUNDED；退款仅限已成功支付的单",
                        desc="支付流水",
                        fields=[("id", "BIGINT", "支付单号"), ("order_id", "BIGINT", "关联订单"),
                                ("status", "VARCHAR(16)", "PENDING/SUCCESS/FAILED/REFUNDED"),
                                ("amount", "DECIMAL(18,2)", "支付金额")],
                        services=[dict(cls="PaymentService", desc="支付与退款（订单支付状态的下游）",
                                       methods="""
    /** 退款：仅 SUCCESS 状态可退，PENDING/FAILED 不可退 */
    public void refund(Long paymentId) {
        PaymentEntity p = paymentMapper.selectById(paymentId);
        if (!"SUCCESS".equals(p.getStatus())) {
            throw new IllegalStateException("仅已成功支付的订单可退款");
        }
    }""")],
                        controllers=[dict(ctrl="PaymentController", svc="PaymentService",
                                          base="/api/payment",
                                          desc="支付入口",
                                          endpoints="""
    @PostMapping("/{paymentId}/refund")
    public void refund(@PathVariable Long paymentId) {
        {var}.refund(paymentId);
    }""")])]),
    dict(svc="inventory-service", pkg="inventory", db="demo_inventory", port=8089, app="InventoryApplication",
         desc="库存服务：SKU 库存与流水",
         shadow="库存扣减",
         entities=[dict(ent="SkuEntity", table="t_sku",
                        tcomment="SKU 表；库存字段不允许出现负数（业务硬性约束）",
                        desc="SKU 库存",
                        fields=[("sku_id", "BIGINT", "SKU 标识"), ("title", "VARCHAR(128)", "商品名"),
                                ("stock", "INT", "可用库存；不可为负")],
                        services=[dict(cls="StockService", desc="库存扣减（下单时占用）",
                                       methods="""
    /** 扣库存：库存不足抛异常；库存不可为负是本域硬约束 */
    public void deduct(Long skuId, int qty) {
        SkuEntity sku = skuMapper.selectById(skuId);
        if (sku.getStock() < qty) {
            throw new IllegalStateException("库存不足");
        }
    }""")],
                        controllers=[dict(ctrl="InventoryController", svc="StockService",
                                          base="/api/inventory",
                                          desc="库存入口",
                                          endpoints="""
    @GetMapping("/sku/{skuId}")
    public SkuEntity sku(@PathVariable Long skuId) {
        return new SkuEntity();
    }""")])]),
    dict(svc="promotion-service", pkg="promotion", db="demo_promotion", port=8088, app="PromotionApplication",
         desc="营销服务：优惠券与活动",
         shadow="订单优惠",
         entities=[dict(ent="CouponEntity", table="t_coupon",
                        tcomment="券实例表；同模板优惠券不可叠加使用（业务硬性约束）",
                        desc="券实例",
                        fields=[("id", "BIGINT", "券号"), ("template_id", "BIGINT", "模板"),
                                ("status", "VARCHAR(16)", "UNUSED/USED/EXPIRED")])]),
    dict(svc="notification-service", pkg="notification", db="demo_notification", port=8090, app="NotificationApplication",
         desc="通知服务：站内信与触达记录",
         shadow="消息触达",
         entities=[dict(ent="NotifyEntity", table="t_notify_record",
                        tcomment="触达记录表",
                        desc="触达记录",
                        fields=[("id", "BIGINT", "主键"), ("user_id", "BIGINT", "接收用户"),
                                ("channel", "VARCHAR(16)", "渠道 SMS/PUSH")])]),
    dict(svc="report-service", pkg="report", db="demo_report", port=8094, app="ReportApplication",
         desc="报表服务：运营日报与导出任务登记",
         shadow="运营报表/导出",
         entities=[dict(ent="ReportEntity", table="t_report_task",
                        tcomment="报表任务表；retention: 报表文件保留 30 天后清理",
                        desc="报表任务",
                        fields=[("id", "BIGINT", "任务号"), ("biz_type", "VARCHAR(32)", "报表类型"),
                                ("file_path", "VARCHAR(256)", "报表文件路径")])]),
    dict(svc="search-service", pkg="search", db="demo_search", port=8095, app="SearchApplication",
         desc="搜索服务：商品与订单检索索引",
         shadow="订单查询",
         entities=[dict(ent="SearchEntity", table="t_search_index",
                        tcomment="检索索引表",
                        desc="检索索引",
                        fields=[("id", "BIGINT", "主键"), ("doc_type", "VARCHAR(16)", "文档类型"),
                                ("payload", "TEXT", "索引负载")])]),
    dict(svc="admin-service", pkg="admin", db="demo_admin", port=8096, app="AdminApplication",
         desc="后台服务：运营操作审计",
         shadow="运营后台操作",
         entities=[dict(ent="OpLogEntity", table="t_admin_op_log",
                        tcomment="运营操作日志表",
                        desc="运营操作日志",
                        fields=[("id", "BIGINT", "主键"), ("op", "VARCHAR(32)", "操作"),
                                ("operator", "VARCHAR(32)", "操作人")])]),
]

NOISE_PAGES = {
    "web-portal/src/views/LegacyOrderPage.vue": """<template>
  <div class="legacy-order">
    <h2>预售单管理（遗留）</h2>
    <!-- 预售单无发货概念；此按钮仅做占位，点击提示不可用 -->
    <button :disabled="true">发货</button>
    <button @click="voidOrder">取消预售单</button>
  </div>
</template>
<script>
// 历史页面：预售单（legacy-trade）运营入口，与新订单页 OrderPage 无关
export default { name: 'LegacyOrderPage', methods: { voidOrder() { /* 调 /api/legacy/presale/{id}/void */ } } }
</script>
""",
    "web-portal/src/views/PointsPage.vue": """<template>
  <div class="points">
    <h2>会员积分账户</h2>
    <!-- 积分账户（legacy-account），不是资金账户；余额概念请看 AccountPage -->
    <p>当前积分：{{ points }}</p>
  </div>
</template>
<script>
export default { name: 'PointsPage', data: () => ({ points: 0 }) }
</script>
""",
    "web-portal/src/views/CouponPage.vue": """<template>
  <div class="coupon">
    <h2>优惠券</h2>
    <!-- 同模板券不可叠加使用（promotion 域规则） -->
    <p>可用券 0 张</p>
  </div>
</template>
<script>
export default { name: 'CouponPage' }
</script>
""",
}

NOISE_API_JS = """
// ── 噪声模块 API（遗留/周边域）──
export function queryLegacyMember(memberId) { return request.get(`/api/legacy/member/basic/${memberId}`) }
export function queryLegacyPoints(memberId) { return request.get(`/api/legacy/points/${memberId}`) }
export function voidPresale(preSaleId) { return request.post(`/api/legacy/presale/${preSaleId}/void`) }
export function deliverShipment(shipmentId) { return request.post(`/api/logistics/shipment/${shipmentId}/deliver`) }
export function refundPayment(paymentId) { return request.post(`/api/payment/${paymentId}/refund`) }
export function queryMemberProfile(memberId) { return request.get(`/api/member/profile/${memberId}`) }
"""


def main():
    if LARGE.exists():
        shutil.rmtree(LARGE)
    shutil.copytree(STD, LARGE, symlinks=True)
    (LARGE / "db/noise").mkdir(parents=True, exist_ok=True)
    for cfg in NOISE:
        emit_service(LARGE, cfg)
    for rel, text in NOISE_PAGES.items():
        (LARGE / rel).write_text(text, encoding="utf-8")
    api = LARGE / "web-portal/src/api/index.js"
    api.write_text(api.read_text(encoding="utf-8") + NOISE_API_JS, encoding="utf-8")
    files = [p for p in LARGE.rglob("*") if p.is_file()]
    java = [p for p in files if p.suffix == ".java"]
    print(f"large fixture: {len(files)} 文件（java {len(java)}），"
          f"服务目录 {len([d for d in (LARGE).iterdir() if d.is_dir()])} 个")


if __name__ == "__main__":
    main()
