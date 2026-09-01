---
title: 关于
description: 关于 WeRead 读书笔记博客
---

## 关于本站

本站使用 [Hugo](https://gohugo.io/) 构建，数据来源为微信读书划线与批注。

通过 `weread_hugo_exporter.py` 脚本，可以：

1. 从微信读书 API 拉取包含笔记的书单
2. 递归获取每本书的划线与想法
3. 标准化并去重
4. 生成 Hugo 内容文件与 JSON 数据
5. 在 Hugo 站点中以卡片网格形式展示

## 技术栈

- Hugo 静态站点生成器
- 原生 JavaScript（无框架依赖）
- CSS 变量与响应式布局
- GitHub Actions 自动化（可选）
