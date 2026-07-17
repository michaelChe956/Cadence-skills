-- KnowledgeBase 可选 DDL 证据模板
-- 数据库类型：MySQL / MariaDB / PostgreSQL / Oracle / SQL Server / 其他
-- 数据库或实例：example_database
-- Schema：example_schema
-- 环境：开发 / 测试 / 生产脱敏副本
-- 导出时间：YYYY-MM-DD HH:MM:SS
-- 说明：仅在 data-model-scope.md 将本文件登记为结构证据时填写；不得包含密码、连接串或真实个人数据。

CREATE TABLE example_table (
  id BIGINT NOT NULL,
  name VARCHAR(128),
  created_at TIMESTAMP,
  PRIMARY KEY (id)
);
