# 3.1 可办理活动查询接口

> **数据来源**：
> **梳理日期**：2026-07-09
> **API名称**：actInfoQryService
> **参数与报文示例**：见同目录 `demo_参数与报文.md`
>
> **说明**：本接口为能力共享接口，由活动中心提供，能力清单编码为 `json_redPacket_redPacketCenter_actInfoQryService`。

## 一、接口基础信息

| 项目      | 值                 |
| ------- | ----------------- |
| 接口编号    | 3.1               |
| 接口名称    | 可办理活动查询接口（权益进联通公众app）|
| API名称   | actInfoQryService |
| HTTP方式  | HTTP-POST         |
| 数据格式    | JSON              |
| 是否需授权   | 是                 |
| 版本      | v1                |
| 发起方/落地方 | 外围 / 活动中心         |
| 入参压缩    | 否                 |
| 出参压缩    | 否                 |

### 调用入口

| 环境   | URL                                                                               |
| ---- | --------------------------------------------------------------------------------- |
| 外网生产 | <https://open.chinaunicom.cn/api/redPacket/redPacketCenter/actInfoQryService/v1>  |
| 外网联调 | <https://open1.chinaunicom.cn/api/redPacket/redPacketCenter/actInfoQryService/v1> |
| 内网生产 | <http://10.168.35.151:8000/api/redPacket/redPacketCenter/actInfoQryService/v1>    |
| 内网联调 | <http://10.125.10.131:8000/api/redPacket/redPacketCenter/actInfoQryService/v1>    |

## 二、业务需求描述

- 外围系统 ->能力共享->活动中心
- 功能点描述：根据相关条件的组合，向活动中心查询可办理的活动范围；
- 查询成功：活动中心根据相关条件返回可以办理的活动别表，返回应答码为000000；
- 查询失败：返回应答码，请参照附录中错误代码章节；

## 三、输入参数
3.
详见 `demo_参数与报文.md` 第一节。

## 四、输出参数

详见 `demo_参数与报文.md` 第二节。

## 五、代码实现定位

### 5.1 API名称到实现类映射机制

**结论：真正对外入口是 activity 工程 precise 能力集的 `com.chinaunicom.activity.precise.ablility.ActInfoQryService.queryActInfo()`，实现类 `com.chinaunicom.activity.precise.ability.impl.ActInfoQryServiceImpl`。**

> **勘误（v1.0->v2.0）**：v1.0 误将入口判定为 bss 工程的 `com.chinaunicom.gd.gdhb.bss.intfce.impl.ActInfoQryServiceImpl.actInfoQryService()`。实际上 bss 那个类对应的是另一个接口 `actInfoQryOnlineService`（可售活动查询接口，能力清单编码 `json_redPacket_redPacketCenter_actInfoQryOnlineService`），**不是本接口**。本接口 `actInfoQryService` 在能力清单中明确归属 **precise 能力集**。

**权威源（能力清单 `_api_impl_map.json`）**：

| 字段 | 值 |
|---|---|
| 编码 | `json_redPacket_redPacketCenter_actInfoQryService` |
| 接口名称 | 可办理活动查询接口(权益进联通公众app) |
| 实现类 | `ActInfoQryService` |
| 方法 | `queryActInfo` |
| 能力集 | **precise** |
| 包路径 | `com.chinaunicom.activity.precise.ablility.*` |

**URL路由机制**：能力共享平台 API 网关接收 HTTP 请求 `/api/redPacket/redPacketCenter/actInfoQryService/v1`，将 URL 路径段 `actInfoQryService` 映射到 activity 工程 precise 能力集发布的 HSF 服务 `com.chinaunicom.activity.precise.ablility.ActInfoQryService`，由网关完成 HTTP->HSF 协议转换。

**证据链**：

1. **接口定义**（precise_api）：`activity/precise_api/src/main/java/com/chinaunicom/activity/precise/ablility/ActInfoQryService.java:7-14`
   - `@ProxyConsumer(beanId="actInfoQryService", version="${ACTIVITYV2_VERSION}", group="${ACTIVITYV2_GROUP}", clientTimeout=60000)`
   - 方法签名：`ActInfoQueryRspBO queryActInfo(QueryActInfoReqBO queryActInfoReqBO)`
2. **实现类**（precise_center）：`activity/precise_center/src/main/java/com/chinaunicom/activity/precise/ability/impl/ActInfoQryServiceImpl.java:18-19`
   - `@ProxyProvider(version="${ACTIVITYV2_VERSION}", group="${ACTIVITYV2_GROUP}")` -- **由 ohaotian 框架注解自动发布为 HSF provider**，无显式 `<hsf:provider>` XML（全工程 grep 无 `<hsf:provider>` 显式声明，所有 precise provider 均走注解发布）
3. **bean 定义**：`activity/precise_center/src/main/resources/spring/spring-activity-precise-ability-service.xml:97-101`
4. **HSF 发布参数实测值**（test 环境 `test-config/testhbzx-configmap/precise/env.properties`）：`ACTIVITYV2_VERSION=1.0.0`、`ACTIVITYV2_GROUP=TESTGDHB`

> **注**：precise 能力集入口结构与 bss 不同--bss 靠 `web.xml` 引用 `spring-bss-intfce-phsf.xml` 发布；precise 靠 `@ProxyProvider` 注解发布。但**本接口同样具备 MSHA 双活开关**（Bridge/Normal 分支），并非"无双活模板"，开关 Redis key 为 `MSHA_SWITCH_KEY_ActInfoQryServicePrecise`（注意后缀 `Precise`，与 bss 的 `MSHA_SWITCH_KEY_ActInfoQryService` 区分）。

### 5.2 实现类清单

| 层级 | 类型 | 全限定类名 | 文件路径 |
|---|---|---|---|
| **对外入口(precise ability)** | interface | `com.chinaunicom.activity.precise.ablility.ActInfoQryService` | `activity/precise_api/.../ablility/ActInfoQryService.java` |
| **对外入口实现** | class | `com.chinaunicom.activity.precise.ability.impl.ActInfoQryServiceImpl` | `activity/precise_center/.../ability/impl/ActInfoQryServiceImpl.java` |
| precise msha 接口 | interface | `com.chinaunicom.activity.precise.ablility.msha.ActInfoQryMshaService` | `activity/precise_api/.../ablility/msha/ActInfoQryMshaService.java` |
| precise msha 实现（normal 路径） | class | `com.chinaunicom.activity.precise.ability.msha.impl.ActInfoQryMshaServiceImpl` | `activity/precise_center/.../ability/msha/impl/ActInfoQryMshaServiceImpl.java` |
| precise bridge 接口 | interface | `com.chinaunicom.activity.precise.ablility.bridge.ActInfoQryBridgeService` | `activity/precise_api/.../ablility/bridge/ActInfoQryBridgeService.java` |
| precise bridge 实现（双活路径） | class | `com.chinaunicom.activity.precise.ability.bridge.impl.ActInfoQryBridgeServiceImpl` | `activity/precise_center/.../ability/bridge/impl/ActInfoQryBridgeServiceImpl.java` |
| precise busi 实现（核心业务） | class | `com.chinaunicom.activity.precise.busi.impl.ActInfoQryBusiServiceImpl` | `activity/precise_center/.../busi/impl/ActInfoQryBusiServiceImpl.java` |
| 活动配置查询 busi（跨 jar bean） | class | `com.chinaunicom.activity.config.busi.impl.QryActInfoConfigBusiServiceImpl` | `activity_config/activity_config_impl/.../busi/impl/QryActInfoConfigBusiServiceImpl.java` |
| 电子券面额查询（msha 组装返参时调用） | interface | `com.chinaunicom.activity.config.ablility.RuFeeRelationDataQryService` | `activity_config/activity_config_api/.../ablility/RuFeeRelationDataQryService.java` |

> **易混淆类（非本接口，勿张冠李戴）**：
> - `com.chinaunicom.gd.gdhb.bss.intfce.ActInfoQryService` + 方法 `actInfoQryService()`（bss 工程）-> 对应接口 **`actInfoQryOnlineService`（可售活动查询接口，3.x 另一条目）**，不是本接口。
> - `com.chinaunicom.activity.precise.ablility.QryActInfoService.queryActInfo()`（precise 工程）-> 对应接口 **`qryActInfoService`（可办理活动查询接口，不带"权益进公众app"后缀）**，是本接口的姊妹条目。

## 六、调用链路

### 6.1 调用树

```
外围系统
 └─ HTTP-POST /api/redPacket/redPacketCenter/actInfoQryService/v1
     └─ 能力共享平台 API 网关（HTTP->HSF 协议转换，API名 actInfoQryService -> precise HSF 服务）
         └─ ActInfoQryServiceImpl.queryActInfo()  [activity/precise_center/.../ability/impl/ActInfoQryServiceImpl.java:25]
             ├─ cacheService.get("MSHA_SWITCH_KEY_ActInfoQryServicePrecise")  -> Redis  :29
             ├─(MSHA开)-> ActInfoQryBridgeServiceImpl.queryActInfo()  [.../bridge/impl/ActInfoQryBridgeServiceImpl.java:19]  (分支①)
             │              ├─ userAttrInfoConfService.qryProvinceForMsha(accNbr)  -> 本地bean(含CB查归属省)  :22
             │              ├─ CommonMshaRouterIdUtils.commonRoute(province)  -> 本地路由标计算  :31
             │              └─ mshaService.queryActInfo(province, reqBO)  -> HSF actInfoQryMshaService2  :32
             │                  [spring-activity-remote-consumer.xml:8, target=${ACTIVITYV2TARGET_IP}]
             │                  └─ （对端机房同下方 msha 路径）
             └─(MSHA关，默认)-> ActInfoQryMshaServiceImpl.queryActInfo(province, reqBO)  [.../msha/impl/ActInfoQryMshaServiceImpl.java:71]  (分支②)
                 ├─ verifyReq(reqBO)  -> 本地入参校验  :74
                 ├─ BeanUtils.copyProperties -> QueryActInfoBusiBO  :94
                 ├─ activityResourceBusiService.fetchActCodeList(busiBO)  -> 本地bean actInfoQryBusiService  :106
                 │   └─ ActInfoQryBusiServiceImpl.fetchActCodeList()  [.../busi/impl/ActInfoQryBusiServiceImpl.java:126]
                 │       ├─ checkUserExistBusiService.getUserId(accNbr)  -> InfoNbrUserDAO  -> MySQL info_nbr_user  :132
                 │       ├─ fuzzyFetchActCodeList(reqBO)  :137
                 │       │   ├─(actId非空) qryActInfoConfigBusiService.fetchActCode  -> QryActInfoDAO.fetchActCode  -> MySQL a_activity_instance⋈a_out_in_activity_rel  :834
                 │       │   ├─ cacheQueryService.selectValueByKey("ACT_QRY_PROD_{prodCode}")  -> 本地内存 Ehcache Block6
                 │       │   ├─ fetchPublishRangeActCode -> cacheQueryService("ACT_QRY_QG/PC/P/C_{...}")  -> 本地内存 Ehcache Block5
                 │       │   └─ cacheQueryService.selectValueByKey("ACT_QRY_INFO_{actCode}")  -> 本地内存 Ehcache Block5
                 │       ├─ checkBlack(actCode,date,accNbr)  [父类 ActivityResourceBase:407]
                 │       │   ├─ ruNbrLabelRelDAO.qryByNbr  -> MySQL ru_nbr_label_rel
                 │       │   └─ qryBlackListService.qryBlackListInfo  -> 本地bean(内存/Redis)
                 │       ├─ getJoinRule(actCode)  -> cacheQueryService  -> 本地内存 Ehcache Block2  :167
                 │       ├─ checkJoinRule(...)  [父类 override:689]
                 │       │   ├─ cacheBigService.get("ACTIVITY_WHITE_SWITCH") / get("WHITE_{actCode}_{accNbr}")  -> Redis, TTL=300s
                 │       │   └─ callJoinRuleEngine -> JoinRuleEngine.assemblyJoinRule  -> 本地规则引擎SDK
                 │       │       └─(paramSource=ES) basicDataService.queryBasicData  -> ES(fallback: qryUserfullInfoNewService.qryByUser HSF->cb-collection)
                 │       ├─ checkActMutex(...)  [父类:1550] -> checkActMutexService.checkActMutex  -> 本地bean(MySQL)
                 │       ├─ checkSendRule(...)  [父类:840]
                 │       │   ├─ cacheQueryService("ACT_{actCode}_SALE_SOURCE/_RPSEND_RULE")  -> 本地内存 Ehcache
                 │       │   └─ callSendRuleEngine -> JoinRuleEngine.assemblyJoinRule  -> 本地规则引擎SDK
                 │       ├─(蜂行动 busiCategory=10) qryActInfoConfigBusiService.getQybFxdRes  :270
                 │       │   ├─ QryActInfoDAO.getRuleInstList  -> MySQL a_activity_rule_instance⋈a_activity_channel_instance
                 │       │   ├─ QryActInfoDAO.getResByRule  -> MySQL a_activity_resource_rule_rel⋈a_activity_sale_resource_rel
                 │       │   └─ QryActInfoDAO.getRpInfo  -> MySQL ru_rp_define
                 │       ├─ resourceNumGetService.getNumPreFixAndResTab(resType)  -> AResourceNumDefineDAO  -> MySQL a_resource_num_define  :310
                 │       ├─ resourceNameCacheService.getResourceInfo(resId,resType)  :315
                 │       │   ├─ cacheService.get("resource_info_{resId}")  -> Redis
                 │       │   └─(miss) resourceNameDataCacheService.getResourceInfo  -> MySQL ru_rp_define / a_right
                 │       ├─(免押先享 typeId=50) ruActParamsService.query  -> RuActParamsDAO  -> MySQL ru_act_params  :379
                 │       └─(分期 06) aActivitySaleResourceRelService.getChannelType(channelCode)  -> AActivitySaleResourceRelDAO  -> MySQL code_channel  :456
                 └─ generatorQueryActInfoRspBO(actCodeInfoList)  :120
                     └─(rpId以"10"开头 & resType∈{01,02,03}) ruFeeRelationDataQryService.queryRpFee(rpId.substring(2))  :160
                         └─ RuFeeRelationServiceImpl.queryRpFee -> RuFeeRelationDAO  -> MySQL ru_rp_define  (注意:方法名含Fee，实际查 ru_rp_define)
```

### 6.2 分支决策表

| 分支条件 | 路径 | 入口类:行号 -> 终点 |
|---|---|---|
| MSHA 双活开关 = true（Redis `MSHA_SWITCH_KEY_ActInfoQryServicePrecise`="true" **且** 全局 `NewDrainagePropertiesUtils.mshaServiceSwitch`="true"） | 双活路径（跨单元） | `ActInfoQryServiceImpl:25` -> `ActInfoQryBridgeServiceImpl:19` -> HSF `actInfoQryMshaService2`(`spring-activity-remote-consumer.xml:8`) -> 对端机房 `ActInfoQryMshaServiceImpl:71` -> 进入 busi 层 |
| MSHA 双活开关 = false（**默认**，任一条件不满足） | 正常路径（本地） | `ActInfoQryServiceImpl:25` -> `ActInfoQryMshaServiceImpl:71`(本地) -> `ActInfoQryBusiServiceImpl:126`(busi) -> 本地内存 Ehcache + MySQL |
| 入参含 ACT_ID（actId 非空） | 单活动直查分支 | `ActInfoQryBusiServiceImpl:834` -> `QryActInfoDAO.fetchActCode`（MySQL 单查，跳过产品->活动的内存初筛） |
| 入参不含 ACT_ID（默认） | 产品->活动初筛分支 | `ActInfoQryBusiServiceImpl:137` -> `fuzzyFetchActCodeList` 走本地内存 Ehcache Block5/6 初筛活动列表 |

> 两条 MSHA 分支在 `ActInfoQryMshaServiceImpl` 之后合并，后续 busi 层链路一致。actId 分支与产品初筛分支在 `fuzzyFetchActCodeList` 内部互斥。

### 6.3 逐层调用明细

**第1层：precise ability 入口**
- 类.方法：`ActInfoQryServiceImpl.queryActInfo(QueryActInfoReqBO)`
- 文件：`activity/precise_center/src/main/java/com/chinaunicom/activity/precise/ability/impl/ActInfoQryServiceImpl.java:25`
- bean：`actInfoQryService`（`spring-activity-precise-ability-service.xml:97-101`，注入 bridgeService/normalService/cacheService）
- 关键代码：

```java
String mshaSwitchRedisKey = "MSHA_SWITCH_KEY_ActInfoQryServicePrecise";
String mshaRedisSwitch = cacheService.get(mshaSwitchRedisKey, String.class);
if ("true".equals(NewDrainagePropertiesUtils.mshaServiceSwitch) && "true".equals(mshaRedisSwitch)){
    return bridgeService.queryActInfo(queryActInfoReqBO);        // 双活路径
}else {
    return normalService.queryActInfo("",queryActInfoReqBO);     // 正常路径
}
```

**第2层：precise msha（normal 路径，业务编排核心）**
- 类.方法：`ActInfoQryMshaServiceImpl.queryActInfo(String province, QueryActInfoReqBO)`
- 文件：`activity/precise_center/src/main/java/com/chinaunicom/activity/precise/ability/msha/impl/ActInfoQryMshaServiceImpl.java:71`
- bean：`actInfoQryMshaService`（`@ProxyProvider(version="${ACTIVITYV2_VERSION}", group="${ACTIVITYV2_GROUP}")`，行 34；同时是 HSF provider 供 bridge 跨机房调用）
- 职责：入参校验 `verifyReq`（业务类型/产品编码/号码/公共参数，行 252-302）+ BO 转换 + 调用 busi 层 + 组装返参（含电子券面额补查）
- 关键代码：

```java
verifyReq(queryActInfoReqBO);                                              // :74
QueryActInfoBusiBO busiBO = new QueryActInfoBusiBO();
BeanUtils.copyProperties(queryActInfoReqBO, busiBO);                       // :94
List<ActivityQueryInfoRspBO> actCodeInfoList =
    activityResourceBusiService.fetchActCodeList(busiBO);                  // :106 -> busi 层
rspBO = generatorQueryActInfoRspBO(actCodeInfoList);                       // :108
```

- 返参组装时电子券面额补查（`generatorQueryActInfoRspBO` 行 120-211，行 160）：

```java
// 仅对 resType∈{01,02,03}(通兑/优惠/终端券) 且 rpId 以 "10" 开头的资源
RuFeeRelationDataBO bo = ruFeeRelationDataQryService.queryRpFee(
    resourceBo.getRpId().substring(2, resourceBo.getRpId().length()));      // :160 去掉"10"前缀
```

**第2层（备选）：precise bridge（双活路径）**
- 类.方法：`ActInfoQryBridgeServiceImpl.queryActInfo(QueryActInfoReqBO)`
- 文件：`activity/precise_center/src/main/java/com/chinaunicom/activity/precise/ability/bridge/impl/ActInfoQryBridgeServiceImpl.java:19`
- bean：`actInfoQryBridgeService`（`spring-activity-precise-bridge-service.xml:24-28`，注入 mshaService=`actInfoQryMshaService2`、userAttrInfoConfService）
- 路由：先按手机号查用户归属省（`userAttrInfoConfService.qryProvinceForMsha`，含 CB 调用），fallback 取入参 provinceNo，经 `CommonMshaRouterIdUtils.commonRoute(province)` 标准化后，通过 HSF consumer `actInfoQryMshaService2` 调对端机房
- 关键代码：

```java
UserAttrInfoConfBO u = userAttrInfoConfService.qryProvinceForMsha(req.getAccNbr());  // :22
String province = (u!=null && u.getUserProvince()!=null) ? u.getUserProvince()
    : (req.getPublicEntity()!=null ? req.getPublicEntity().getProvinceNo() : "");     // :23-30
province = CommonMshaRouterIdUtils.commonRoute(province);                            // :31
return mshaService.queryActInfo(province, req);                                      // :32 HSF跨单元
```

**第3层：precise busi（活动查询核心业务）**
- 类.方法：`ActInfoQryBusiServiceImpl.fetchActCodeList(QueryActInfoBusiBO)`
- 文件：`activity/precise_center/src/main/java/com/chinaunicom/activity/precise/busi/impl/ActInfoQryBusiServiceImpl.java:126`
- 继承：`extends ActivityResourceBase`（父类 `activity/activity_busi_impl/.../ActivityResourceBase.java` 提供 cacheQueryService/cacheBigService/checkActMutexService 等）
- bean：`actInfoQryBusiService`（注入到 msha 层 `activityResourceBusiService` 字段）
- 职责：用户校验 -> 活动初筛 -> 黑名单 -> 参与规则 -> 互斥校验 -> 依赖产品 -> 派发规则 -> 资源组装
- 关键调用（行号见 6.1 调用树）：主数据来自**本地内存 Ehcache**（MemoryCacheInfo，由 MQ/定时任务从 MySQL 离线构建），少数路径实时查 MySQL（号码->userId、actId->actCode、蜂行动、资源前缀/名称、分期参数、渠道类型）

**第4层：DAO（MySQL）** - 见第七节表清单。

**本地内存构建链路（离线，MQ/定时任务触发）**：
- `CacheDefineServiceImpl.init()`（`spring-activityv2-busi-service.xml:85`，init-method="init"）启动时全量加载 Ehcache Block 1/5/6
- `CacheManagerServiceImpl.mergeActivityMemoryInfo(activityCode)` 活动审核/变更时增量加载 Block 2/3/4，从 MySQL 查活动配置后填充 Ehcache

## 七、数据库与表

本接口为查询接口，仅读不写。活动配置类表（a_/ru_/code_ 前缀）主存于**配置库 `testhbzx_dpara`**（由 activity_config 工程数据源访问）；号码用户/标签类表存于**实例库 `testhbzx_dhb`**（由 activity 工程数据源访问）。两库表名一致时以工程数据源为准。

| 库 | 表名 | 用途 | 操作 | DAO / 方法 | 代码位置 |
|---|---|---|---|---|---|
| dhb（实例库） | `info_nbr_user` | 号码-用户映射（getUserId） | R | `InfoNbrUserDAO.queryByNbrInfo` | `ActInfoQryBusiServiceImpl.java:132` |
| dpara（配置库） | `a_activity_instance` ⋈ `a_out_in_activity_rel` | 活动实例+外部活动编码（actId 直查） | R | `QryActInfoDAO.fetchActCode` | `ActInfoQryBusiServiceImpl.java:834` |
| dpara | `a_activity_rule_instance` ⋈ `a_activity_channel_instance` | 蜂行动规则实例（busiCategory=10） | R | `QryActInfoDAO.getRuleInstList` | `ActInfoQryBusiServiceImpl.java:270` |
| dpara | `a_activity_resource_rule_rel` ⋈ `a_activity_sale_resource_rel` | 蜂行动资源规则关联 | R | `QryActInfoDAO.getResByRule` | `ActInfoQryBusiServiceImpl.java:270` |
| dpara | `ru_rp_define` | 红包/电子券定义（rp_name、面额 grant_content） | R | `QryActInfoDAO.getRpInfo` / `RuFeeRelationDAO.queryRpFee` / `RuRpDefineDAO.selectByPrimaryKey` | `ActInfoQryBusiServiceImpl.java:270`；`ActInfoQryMshaServiceImpl.java:160` |
| dpara | `a_resource_num_define` | 资源号段前缀+资源表名映射 | R | `AResourceNumDefineDAO.getNumPrefixAndResTab` | `ActInfoQryBusiServiceImpl.java:310` |
| dpara | `a_right` | 权益名称（right_name） | R | `ARightDAO.getRpName` | `ResourceAtomServiceImpl`（resourceNameCache miss 时） |
| dpara | `ru_act_params` | 免押先享分期参数（typeId=50） | R | `RuActParamsDAO.query` | `ActInfoQryBusiServiceImpl.java:379` |
| dpara | `code_channel` | 渠道类型（分期活动 06） | R | `AActivitySaleResourceRelDAO.getChannelType` | `ActInfoQryBusiServiceImpl.java:456` |
| dhb（实例库） | `ru_nbr_label_rel` | 号码-标签关系（黑名单校验） | R | `RuNbrLabelRelDAO.qryByNbr` | `ActivityResourceBase.java:407`（checkBlack） |

> **说明**：活动主数据（活动列表/参与规则/派发规则/匹配规则/营销资源/发布范围等）**不直接查库**，而是从本地内存 Ehcache（`MemoryCacheInfo`，见 8.4）读取，Ehcache 由 MQ 消费者 + 定时任务从上述配置表离线构建。实时查 MySQL 仅发生在：号码->userId、actId->actCode 直查、蜂行动资源、资源号段前缀、资源名称（cache miss fallback）、免押先享参数、渠道类型、黑名单标签等少数路径。

## 八、中间件使用明细

### 8.1 Redis（KV）

| 用途 | Key 格式 | Value 类型/结构 | TTL | 读/写时机 | 代码位置 |
|---|---|---|---|---|---|
| MSHA 双活开关 | `MSHA_SWITCH_KEY_ActInfoQryServicePrecise` | String（值 `"true"` = 走 Bridge 双活路径） | 无（持久 key，运维切换） | 入口处 `get(..., String.class)` 判断走双活/正常 | `ActInfoQryServiceImpl.java:28-29` |
| 白名单开关 | `ACTIVITY_WHITE_SWITCH` | String（"true"） | 无 | checkJoinRule->checkBaseRule 前 `get` | `ActivityResourceBase.java`（checkJoinRule 内） |
| 白名单数据 | `WHITE_{activityCode}_{accNbr}` | `WhiteListInfoBO`（序列化对象） | **300 秒**（5 分钟） | 白名单校验时 `get`，miss 走默认 | `ActivityResourceBase.java:731,742` |
| 资源信息缓存 | `resource_info_{resourceId}` | `ResourceInfoQryBO`（序列化对象） | 无（永久） | resourceNameCacheService.getResourceInfo 先 `get`，miss 查库后写回 | `ResourceNameCacheServiceImpl.java:39-49` |
| 资源名称缓存 | `resource_name_{resourceId}` | String | 无 | 资源名称查询 | `ResourceNameCacheServiceImpl.java:21-31` |
| 资源 chargeIds | `AMOUNT_CHARGEIDS_{serialNumber}_{activityCode}` | String（逗号拼接） | **300 秒** | callSendRuleEngine 内 | `ActivityResourceBase.java:1192-1194` |
| 渠道类型缓存 | `CHANNEL_TYPE_KEY_{provinceCode}{channelNo}` | String | **86400 秒**（24 小时） | checkCombRule 内 | `ActivityResourceBase.java:1418,1432` |

### 8.2 消息队列（MQ）

本接口查询主链路**不直接生产/消费 MQ**，但依赖 MQ 异步刷新本地内存 Ehcache（见 8.4）：

| Topic / Tag / CID | 方向 | 触发时机 | 消息体 | 生产者 / 消费者 | 代码位置 |
|---|---|---|---|---|---|
| `MEMORY_CACHE_MERGE_TOPIC` / `MEMORY_CACHE_MERGE_TAG` / CID=`MEMORY_CACHE_MERGE_CID` | 消费 | 活动审核/变更时由配置侧生产 | `activityCode` | 配置侧生产 / `MemoryMergeConsumer` 消费并 `mergeActivityMemoryInfo` | `activity/activity_busi_impl/.../consumer/MemoryMergeConsumer.java` |
| `MEMORY_CACHE_UPDATE_TOPIC` / CID=`MEMORY_CACHE_UPDATE_CID` | 消费 | 活动状态变更 | `activityCode` | 配置侧 / `MemoryUpdateConsumer` | 同目录 |
| `MEMORY_CACHE_DELETE_TOPIC` / `MEMORY_CACHE_DELETE_TAG` / CID=`MEMORY_CACHE_DELETE_CID` | 消费 | 活动删除 | `activityCode` | 配置侧 / `MemoryDeleteConsumer` | 同目录 |
| `BREACH_INFO_UPDATE_TOPIC` / CID=`BREACH_INFO_CID` | 消费 | 互斥信息变更 | 互斥信息 | 配置侧 / `MemoryRedisMergeConsumer` | 同目录 |

> 常量定义：`activity_config/activity_config_busi_api/.../constant/MemoryTopicConstant.java`

### 8.3 ElasticSearch

本接口主链路**不直接查 ES**。仅当规则引擎参数来源 `paramSource=ES` 时，`basicDataService.queryBasicData` 查 ES 用户资料（fallback `qryUserfullInfoNewService.qryByUser` 走 HSF 到 cb-collection 工程）。属规则校验的间接可选路径，非活动查询主数据源。

### 8.4 本地内存缓存（Ehcache 堆内）

| 缓存对象 | 数据结构 | 初始化/加载方式 | 刷新机制 | 代码位置 |
|---|---|---|---|---|
| `MemoryCacheInfo`（22 个 `UserManagedCache` 静态字段，分 8 Block） | Ehcache `UserManagedCache<String, List/Object>`（`build(false)` 不启用统计）。本接口读取的 Block：**Block5**（`ACTIVITY_CACHE_5_FILTER_ACT/_ACT_BASE/_ACT_BREACH/_ACT_PARAMS`，可办理活动 filter/base/互斥/params）+ **Block6**（`ACTIVITY_CACHE_6_PRODUCT`，产品->活动）+ **Block2**（参与/派发/匹配/附加规则、营销资源）+ **Block4**（资源->派发规则） | 启动时 `CacheDefineServiceImpl.init()` 全量加载 Block 1/5/6；活动审核时 `CacheManagerServiceImpl.mergeActivityMemoryInfo` 增量加载 Block 2/3/4 | **三重刷新**：① MQ 消费者（`MemoryMergeConsumer` 等，活动变更触发 `mergeActivityMemoryInfo`）；② 定时任务 `RefreshMemoryTimer`（每 5 分钟增量刷新最近 10 分钟变更）；③ 定时清理 `CleanMemoryTimer`（每 24 小时清空强制重载） | 定义：`activity/activity_busi_impl/.../utils/MemoryCacheInfo.java:8-96`；读：`CacheQueryServiceImpl.selectValueByKey` |

本接口 `fetchActCodeList` 实际读取的 Ehcache key（前缀来自 `MemoryConstant`）：
- `ACT_QRY_PROD_{prodCode}`（Block6，产品->活动列表）
- `ACT_QRY_QG_{actCode}` / `ACT_QRY_P_{provinceNo}_{actCode}` / `ACT_QRY_PC_{provinceNo}_{actCode}` / `ACT_QRY_C_{cityNo}_{actCode}`（Block5，发布范围：全国/省/省渠道/地市）
- `ACT_QRY_INFO_{actCode}`（Block5 `_ACT_BASE`，活动基础信息 ActQryInfoBO）
- `ACT_{actCode}` + 参与/派发/匹配/附加规则前缀（Block2/Block4）

### 8.5 HSF 跨进程调用

| 服务接口 | group / version | target | consumer 配置 | provider 配置 | 代码位置 |
|---|---|---|---|---|---|
| `actInfoQryMshaService2`（**唯一网络 HSF**，bridge 跨单元） | `${ACTIVITYV2_GROUP}`=TESTGDHB / `${ACTIVITYV2_VERSION}`=1.0.0 | `${ACTIVITYV2TARGET_IP}`（clientTimeout=60000） | `spring-activity-remote-consumer.xml:8` | 对端 `@ProxyProvider`（`ActInfoQryMshaServiceImpl:34`） | 调用：`ActInfoQryBridgeServiceImpl:32` |
| `ActInfoQryService`（对外 provider） | `${ACTIVITYV2_GROUP}` / `${ACTIVITYV2_VERSION}` | activity/precise_center | 网关 HTTP->HSF | `@ProxyProvider` 注解（`ActInfoQryServiceImpl:18`），无显式 phsf XML | bean：`spring-activity-precise-ability-service.xml:97-101` |
| `basicDataService.queryBasicData`（规则引擎 ES 参数，fallback） | - | cb-collection 工程（HSF） | - | - | `ActivityResourceBase.getRuleReq`（paramSource=ES 时） |
| `qryUserfullInfoNewService.qryByUser`（ES fallback） | - | cb-collection 工程（HSF） | - | - | 同上 |

> busi 层调用的 `actInfoQryBusiService`/`qryActInfoConfigBusiService`/`ruActParamsService`/`aActivitySaleResourceRelService`/`newRuFeeRelationDataQryService`/`resourceNumGetService`/`resourceNameCacheService`/`checkUserExistBusiService`/`checkActMutexService` 等虽部分带 `@ProxyProvider` 注解，但实际是 **activity_config_impl / activity_busi_impl 同 JVM 本地 bean**（跨 jar 注入），不走 HSF 网络。

### 8.6 定时任务

| 任务 | 触发方式 | 作用 | 代码位置 |
|---|---|---|---|
| `CacheDefineServiceImpl.init` | spring `init-method="init"`（启动一次） | 全量加载 Ehcache Block 1/5/6 | `spring-activityv2-busi-service.xml:85` |
| `RefreshMemoryTimer` | `new Timer().scheduleAtFixedRate(timer, 5*60*1000, 5*60*1000)`（启动后 5 分钟，**每 5 分钟**） | 增量刷新最近 10 分钟 `update_time` 变化的活动内存（`qryActivityListService.qryActivityListByUpdateTime(10)` -> `mergeActivityMemoryInfo`） | `activity/activity_busi_impl/.../RefreshMemoryTimer.java:114-115` |
| `CleanMemoryTimer` | `new Timer().scheduleAtFixedRate(timer, 5*60*1000, 60*60*24*1000)`（启动后 5 分钟，**每 24 小时**） | 清空 Ehcache 强制下次请求重载 | `activity/activity_busi_impl/.../CleanMemoryTimer.java:40-41` |

> 均为 JDK `java.util.Timer`（非 Quartz/Elastic-Job），无 cron，单机调度。

### 8.7 其他下游 HTTP 接口

本接口查询主链路（normal 路径）**未调用下游 HTTP**。bridge 双活路径中 `userAttrInfoConfService.qryProvinceForMsha(accNbr)` 内部含 CB 调用查用户归属省（仅 MSHA 开启时触发，非默认路径）。

## 九、数据源分析（重点）

### 9.1 主路径数据源

- **主数据走本地内存 Ehcache**（`MemoryCacheInfo`）：活动列表（产品->活动、发布范围）、活动基础信息、参与规则、派发规则、匹配规则、附加规则、营销资源、资源->派发规则关系。由 `CacheQueryServiceImpl.selectValueByKey` 从 Ehcache Block 2/4/5/6 读取。
- **Ehcache 离线构建数据源**：MySQL 配置库 `testhbzx_dpara` 的活动配置表（`a_activity_instance`/`a_activity_rule_instance`/`a_activity_sale_resource_rel`/`a_activity_range_rule` 等），由 `CacheDefineServiceImpl.init`（启动全量）+ MQ 消费者（变更增量）+ `RefreshMemoryTimer`（每 5 分钟兜底）三重机制同步。

### 9.2 实时查库路径数据源（fetchActCodeList 内的 DAO 调用）

对链路上所有"实时查库/补数"类子调用逐个验证：

| 调用 | 实现类 | 验证结果 | 证据文件:行号 | 返回字段 |
|---|---|---|---|---|
| `checkUserExistBusiService.getUserId(accNbr)` | `CheckUserExistBusiServiceImpl` -> `InfoNbrUserDAO` | **DAO 查库**（实例库 dhb `info_nbr_user`） | `ActInfoQryBusiServiceImpl.java:132` | userId（用户标识） |
| `qryActInfoConfigBusiService.fetchActCode`（actId 非空时） | `QryActInfoConfigBusiServiceImpl` -> `QryActInfoDAO` | **DAO 查库**（配置库 `a_activity_instance⋈a_out_in_activity_rel`） | `ActInfoQryBusiServiceImpl.java:834` | provinceCode/activityCode/outActivityId/systemSource |
| `ruNbrLabelRelDAO.qryByNbr`（黑名单校验） | `RuNbrLabelRelDAO`（MyBatis） | **DAO 查库**（实例库 `ru_nbr_label_rel`） | `ActivityResourceBase.java:407`（checkBlack） | 号码标签关系 |
| `qryActInfoConfigBusiService.getQybFxdRes`（蜂行动） | `QryActInfoDAO.getRuleInstList/getResByRule/getRpInfo` | **DAO 查库**（配置库 3 表 JOIN） | `ActInfoQryBusiServiceImpl.java:270` | 蜂行动规则实例/资源/红包定义 |
| `resourceNumGetService.getNumPreFixAndResTab` | `ResourceAtomServiceImpl` -> `AResourceNumDefineDAO` | **DAO 查库**（配置库 `a_resource_num_define`） | `ActInfoQryBusiServiceImpl.java:310` | numPrefix/resourceTable（号段前缀+资源表名） |
| `resourceNameCacheService.getResourceInfo` | `ResourceNameCacheServiceImpl` | **Redis 缓存优先**（`resource_info_{resId}`），miss 时 fallback `resourceNameDataCacheService` -> **DAO 查库**（`ru_rp_define`/`a_right`） | `ActInfoQryBusiServiceImpl.java:315` | 资源名称/信息 |
| `ruActParamsService.query`（免押先享 typeId=50） | `RuActParamsDAO`（MyBatis） | **DAO 查库**（配置库 `ru_act_params`） | `ActInfoQryBusiServiceImpl.java:379` | 免押先享分期参数 |
| `aActivitySaleResourceRelService.getChannelType`（分期 06） | `AActivitySaleResourceRelDAO`（MyBatis） | **DAO 查库**（配置库 `code_channel`） | `ActInfoQryBusiServiceImpl.java:456` | channelType（渠道类型） |
| `ruFeeRelationDataQryService.queryRpFee`（msha 返参组装） | `RuFeeRelationServiceImpl` -> `RuFeeRelationDAO` | **DAO 查库**（配置库 `ru_rp_define`，注意方法名含 Fee 但实际查 ru_rp_define） | `ActInfoQryMshaServiceImpl.java:160` | grant_content（电子券面额） |
| `basicDataService.queryBasicData`（规则引擎 ES 参数） | `BasicDataService` | **ES 查询**（paramSource=ES 时），fallback **HSF->cb-collection** | `ActivityResourceBase.getRuleReq` | 用户三户资料（规则校验用） |

### 9.3 结论（分层）

- **活动主数据走本地内存 Ehcache**：`MemoryCacheInfo` Block 2/4/5/6（活动列表/规则/资源关系），由 MQ + 定时任务从 MySQL 配置库 `testhbzx_dpara` 离线构建，实时查询不直接查活动配置主表。
- **号码类数据走库**：MySQL 实例库 `testhbzx_dhb` 的 `info_nbr_user`（用户标识）、`ru_nbr_label_rel`（黑名单标签）。
- **资源/参数类数据走库**：MySQL 配置库 `testhbzx_dpara` 的 `a_resource_num_define`/`ru_rp_define`/`a_right`/`ru_act_params`/`code_channel`，部分经 Redis 缓存（资源名称/信息）。
- **actId 直查走库**：入参含 ACT_ID 时 `QryActInfoDAO.fetchActCode` 直接查 `a_activity_instance⋈a_out_in_activity_rel`（跳过内存初筛）。
- **规则引擎为本地 SDK**：`JoinRuleEngine.assemblyJoinRule`（`com.chinaunicom.rule.core`），非 HSF/HTTP；其参数若依赖 ES 数据则走 `basicDataService.queryBasicData`（ES）+ fallback HSF（cb-collection）。
- **Redis 非主数据源**：仅用于 MSHA 开关、白名单、资源名称/info 缓存、渠道类型缓存、chargeIds -- 均为辅助缓存/开关。
- **全程无下游 HTTP（normal 路径）**：唯一网络 HSF 是 bridge 路径的 `actInfoQryMshaService2`（跨机房双活）；normal 路径所有调用均为本地 bean + DAO。

## 十、关键代码引用

| 引用 | 文件:行号 |
|---|---|
| 能力清单条目（权威源） | `cadence/knowledge-base/_api_impl_map.json`（编码 `json_redPacket_redPacketCenter_actInfoQryService`） |
| 接口定义（@ProxyConsumer） | `activity/precise_api/src/main/java/com/chinaunicom/activity/precise/ablility/ActInfoQryService.java:7-14` |
| 入口实现（@ProxyProvider + MSHA 开关） | `activity/precise_center/src/main/java/com/chinaunicom/activity/precise/ability/impl/ActInfoQryServiceImpl.java:18-38` |
| 入口 bean 定义 | `activity/precise_center/src/main/resources/spring/spring-activity-precise-ability-service.xml:97-101` |
| msha 实现（normal 路径） | `activity/precise_center/src/main/java/com/chinaunicom/activity/precise/ability/msha/impl/ActInfoQryMshaServiceImpl.java:71-118` |
| msha 返参组装（电子券面额补查） | `activity/precise_center/.../ability/msha/impl/ActInfoQryMshaServiceImpl.java:120-211`（queryRpFee:160） |
| bridge 实现（双活路径） | `activity/precise_center/src/main/java/com/chinaunicom/activity/precise/ability/bridge/impl/ActInfoQryBridgeServiceImpl.java:19-33` |
| bridge bean（注入 actInfoQryMshaService2） | `activity/precise_center/src/main/resources/spring/spring-activity-precise-bridge-service.xml:24-28` |
| HSF consumer（唯一网络 HSF，跨机房） | `activity/precise_center/src/main/resources/spring/spring-activity-remote-consumer.xml:8` |
| busi 核心（fetchActCodeList） | `activity/precise_center/src/main/java/com/chinaunicom/activity/precise/busi/impl/ActInfoQryBusiServiceImpl.java:126-545` |
| 父类（规则/互斥/黑名单/缓存工具） | `activity/activity_busi_impl/src/main/java/com/chinaunicom/activity/utils/ActivityResourceBase.java` |
| 本地内存定义（Ehcache 22 字段） | `activity/activity_busi_impl/src/main/java/com/chinaunicom/activity/utils/MemoryCacheInfo.java:8-96` |
| 本地内存初始化（init-method） | `spring-activityv2-busi-service.xml:85`（CacheDefineServiceImpl） |
| 定时刷新内存（5 分钟） | `activity/activity_busi_impl/.../RefreshMemoryTimer.java:114-115` |
| MQ 常量定义 | `activity_config/activity_config_busi_api/.../constant/MemoryTopicConstant.java` |
| QryActInfoDAO Mapper（actId 直查） | `activity_config/activity_config_impl/.../dao/mapper/QryActInfoMapper.xml:6`（a_activity_instance⋈a_out_in_activity_rel） |
| InfoNbrUser Mapper | `activity/activity_busi_impl/.../order/dao/mapper/InfoNbrUserMapper.xml:16` |

## 十一、请求/响应报文示例

详见 `demo_参数与报文.md` 第三节。
