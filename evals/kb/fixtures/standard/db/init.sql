-- demo 商城 DDL（4 表，三库归属）
CREATE DATABASE IF NOT EXISTS demo_user;
USE demo_user;
CREATE TABLE t_user (
  user_id   BIGINT PRIMARY KEY COMMENT '用户唯一标识',
  user_name VARCHAR(64)  NOT NULL COMMENT '用户姓名',
  mobile    VARCHAR(20)  COMMENT '手机号',
  email     VARCHAR(128) COMMENT '邮箱',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='用户基本信息表';

CREATE DATABASE IF NOT EXISTS demo_account;
USE demo_account;
-- F6 埋点：业务规则在表注释
CREATE TABLE t_user_account (
  id         BIGINT PRIMARY KEY COMMENT '主键',
  user_id    BIGINT NOT NULL COMMENT '用户唯一标识，同 t_user.user_id',
  account_no VARCHAR(32) NOT NULL COMMENT '账户号',
  balance    DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '账户余额；业务规则：余额不可为负',
  status     VARCHAR(16) NOT NULL DEFAULT 'NORMAL' COMMENT '账户状态：NORMAL/FROZEN/CLOSED',
  UNIQUE KEY uk_account_no (account_no)
) COMMENT='用户账户表；本表余额字段不允许出现负值（业务硬约束）';

CREATE DATABASE IF NOT EXISTS demo_order;
USE demo_order;
CREATE TABLE t_order (
  order_id  BIGINT PRIMARY KEY COMMENT '订单号',
  user_id   BIGINT NOT NULL COMMENT '下单用户，同 t_user.user_id',
  status    VARCHAR(16) NOT NULL COMMENT '订单状态：CREATED/PAID/SHIPPED/COMPLETED/CANCELLED',
  amount    DECIMAL(18,2) NOT NULL COMMENT '订单金额',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='订单表；状态迁移受 OrderService 状态机约束';

-- F7 语境
CREATE TABLE t_export_file (
  id         BIGINT PRIMARY KEY COMMENT '主键',
  order_id   BIGINT COMMENT '关联订单',
  file_path  VARCHAR(256) COMMENT '导出文件路径',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '导出时间；保留 7 天后清理'
) COMMENT='订单导出文件登记表';
