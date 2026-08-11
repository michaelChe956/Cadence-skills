## 1. 引用基线扫描

- [ ] 1.1 扫描全仓被移动/删除文件的文件名引用形成基线，确定引用修复清单

## 2. 删除无价值旧文档

- [ ] 2.1 使用 `git rm` 删除 `cadence/docs/` 15 份与 `cadence/analysis/` 3 份旧文档，移除空的 `cadence/analysis/` 目录

## 3. 建立归档结构并迁移历史产物

- [ ] 3.1 新建 `cadence/archive/` 镜像子目录，使用 `git mv` 迁移全部 45 份归档文档并生成 `INDEX.md`

## 4. 归档 OpenSpec change

- [ ] 4.1 将 `improve-progressive-disclosure-routing` 移入 archive 并把 3 份 capability spec 落地到 `openspec/specs/`

## 5. 验证与交付

- [ ] 5.1 迁移后复扫引用并修复残留，输出删除/归档/specs 落地核对清单，与预期逐项比对
