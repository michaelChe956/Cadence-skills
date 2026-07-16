# 3.1 可办理活动查询接口 - 参数与报文

> **主文件**：`3.1_可办理活动查询接口_actInfoQryService.md`

## 一、输入参数

| 节点名称 | 父节点名称 | 约束 | 类型 | 长度 | 说明 |
|---|---|---|---|---|---|
| QRY_ACT_INFO_REQ | UNI_BSS_BODY | 1 | | | |
| PUBLIC_ENTITY | QRY_ACT_INFO_REQ | 1 | Object | | |
| REQUEST_TIME | PUBLIC_ENTITY | 1 | String | V17 | 请求时间戳 / 24小时进制，精确到毫秒 / 格式：yyyyMMddHHmmssSSS |
| MECHANISM_CODE | PUBLIC_ENTITY | 1 | String | V32 | 接入机构 |
| JOB_NUMBER | PUBLIC_ENTITY | 1 | String | V32 | 工号 |
| CHANNEL_CODE | PUBLIC_ENTITY | 1 | String | V20 | 渠道编码 |
| PROVINCE_NO | PUBLIC_ENTITY | 1 | String | V12 | 省份 |
| CITY_NO | PUBLIC_ENTITY | 1 | String | V12 | 地市 |
| AREA_NO | PUBLIC_ENTITY | ？ | String | V12 | 区县 |
| TRADE_TYPE | QRY_ACT_INFO_REQ | 1 | String | V2 | 业务类型 / 01 开户业务 / 02 非开户业务 |
| ACC_NBR | QRY_ACT_INFO_REQ | ？ | String | V20 | 用户号码（业务类型为02非开户业务时必填） |
| PROD_CODE | QRY_ACT_INFO_REQ | 1 | String | V20 | 商品ID／产品ID（与活动资源进行绑定或打包的产品，cb系统可为附加产品ID，或主产品ID。其它受理触点可为触点自有产品/商品ID） |
| MAIN_PROD_CODE | QRY_ACT_INFO_REQ | ？ | String | V20 | 主产品ID（cb通信业务主产品） |
| ACT_NAME | QRY_ACT_INFO_REQ | ？ | String | V256 | 活动名称 |
| ACT_ID | QRY_ACT_INFO_REQ | ？ | String | V20 | 活动编码（当ACT_ID传值时，仅返回1个活动，返回BSS_ACT_CODE值与ACT_ID相同） |
| TOUCH_POINT | QRY_ACT_INFO_REQ | ？ | String | V16 | 办理触点 |

## 二、输出参数

| 节点名称 | 父节点名称 | 约束 | 类型 | 长度 | 说明 |
|---|---|---|---|---|---|
| QRY_ACT_INFO_RSP | UNI_BSS_BODY | 1 | object | | |
| RESP_CODE | QRY_ACT_INFO_RSP | 1 | String | V6 | 应答码 |
| RESP_DESC | QRY_ACT_INFO_RSP | ？ | String | V2000 | 结果描述 |
| ACT_RELATION_ENTITY | QRY_ACT_INFO_RSP | * | Array | | 活动关系 |
| ACT_LIST | ACT_RELATION_ENTITY | 1 | String | V2048 | 活动列表 / BSS_ACT_CODE1，BSS_ACT_CODE2，…，BSS_ACT_CODEn，多个活动间用英文逗号分开 |
| ACT_RELATION_TYPE | ACT_RELATION_ENTITY | 1 | String | V2 | 关系类型 / 02 最大可选 |
| ACT_NUM | ACT_RELATION_ENTITY | ？ | String | V2 | 数量 / 当ACT_RELATION_TYPE=02时，此字段必传 |
| ACTIVITY_ENTITY | QRY_ACT_INFO_RSP | * | Array | | 活动信息实体 |
| BSS_ACT_CODE | ACTIVITY_ENTITY | 1 | String | V40 | 活动ID |
| ACT_NAME | ACTIVITY_ENTITY | 1 | String | V1024 | 活动名称 |
| ACT_DESC | ACTIVITY_ENTITY | ？ | String | V1024 | 活动描述 |
| ACT_TYPE | ACTIVITY_ENTITY | ？ | String | V2 | 活动类别 / 01 普通活动 / 02 溢价活动 / 03 满减活动 / 04 打折活动 / 05 拼团活动 / 06 分期活动（解耦模式） / 07 免押先享活动 |
| FEE_ITEM | ACTIVITY_ENTITY | ？ | String | V64 | 费用项,（02 溢价活动必传） |
| FEE_ITEM_NAME | ACTIVITY_ENTITY | ？ | String | V64 | 费用项名称 |
| FEE_ITEM_TYPE | ACTIVITY_ENTITY | ？ | String | V2 | 费用科目大类,（02 溢价活动必传） / 0 一次性费用 / 1 押金 / 2 预存 |
| ACT_PRICE | ACTIVITY_ENTITY | ？ | String | V12 | 活动价格 / (活动类别ACT_TYPE，02：溢价金额（单位分）03：满减规则 如100:10（满:减，单位分） 04：打折折扣，如0.2) |
| ACT_OBJECT | ACTIVITY_ENTITY | ？ | String | V2 | 活动对象 / 01：用户 / 02：渠道 |
| ACT_RELATION | ACTIVITY_ENTITY | ？ | String | V2 | 活动属性 / 1 叠加 / 2 互斥 |
| RES_ENTITY | ACTIVITY_ENTITY | * | Array | | 资源实体 |
| RES_NAME | RES_ENTITY | 1 | String | V256 | 资源名称 |
| RES_ID | RES_ENTITY | 1 | String | V256 | 资源ID |
| RES_TYPE | RES_ENTITY | 1 | String | V3 | 资源类型 / 01 通兑券 / 02 优惠券 / 03 终端券 / 04 权益券 |
| IS_SELECT | RES_ENTITY | 1 | String | V2 | 资源属性 / 1 必选 / 2 可选 |
| RELATION_ENTITY | ACTIVITY_ENTITY | * | Array | | 资源关系 |
| RES_LIST | RELATION_ENTITY | 1 | String | V2048 | 资源列表 / RES_ID1，RES_ID2，RES_ID3··RES_Idn / 多个资源间，用英文逗号分开 |
| RELATION_TYPE | RELATION_ENTITY | 1 | String | V2 | 关系类型 / 01 固定选 / 02 最大可选 |
| NUM | RELATION_ENTITY | ？ | String | V2 | 数量 / 当RELATION_TYPE=01，02时，此字段必传 |
| INSTALL_ENTITY | ACTIVITY_ENTITY | * | Array | | 分期规则实体 / （ACT_TYPE=06分期活动时返回） |
| TOUCH_POINT | INSTALL_ENTITY | ？ | String | V16 | 办理触点 |
| MAIN_PROD_CODE | INSTALL_ENTITY | ？ | String | V20 | 主套餐产品ID |
| PAY_METHOD | INSTALL_ENTITY | 1 | String | V16 | 支付方式 / PM0001支付宝预授权 / PM0002花呗分期 / PM0003招联分期 / PM0004余额宝质押 / PM0005银行卡质押 / PM0006微信支付分小直降 / PM0007花呗月月付 / PM0008沃分期整合 / PM0009京东白条 |
| INSTALL_NUM | INSTALL_ENTITY | 1 | String | V2 | 分期期数 |
| INSTALL_FEE | INSTALL_ENTITY | 1 | String | V16 | 分期本金，单位分 |
| BSS_ACT_RATE | INSTALL_ENTITY | 1 | String | V10 | 还款费率 |
| SUBSIDY_TYPE | INSTALL_ENTITY | 1 | String | V2 | 贴息模式 / 01商户贴息 / 03用户付息 |

## 三、请求/响应报文示例

参考附录6 示例报文。
