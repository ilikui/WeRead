---
title: "你好，WeRead 博客"
date: 2026-08-25
tags: ["随笔"]
summary: "欢迎来到这个由 Hugo 驱动的读书笔记博客。"
toc: false
---

欢迎来到我的读书笔记博客。

这里主要记录两件事：

1. **读书**：来自微信读书的划线、批注与思考
2. **写作**：把零散的笔记整理成有结构的长文

## 开始写作

只需在 `content/blog/` 下新建一个 `.md` 文件：

```markdown
---
title: "我的文章标题"
date: 2026-09-01
tags: ["标签"]
summary: "一句话摘要"
---

正文从这里开始……
```

保存后，文章会自动以卡片形式出现在 Blog 列表页。

## 加入专题

给文章的 Front Matter 加上 `topics`，就能把它归入一个或多个专题卡片盒：

```markdown
topics: ["geren-chengzhang", "xie-zuo-fang-fa"]
```

专题本身在 `content/topics/<文件夹名>/_index.md` 中定义封面与说明，详见 [专题](/topics/) 页面。一篇笔记可以同时属于多个专题——这正是卢曼卡片盒「一卡多线」的思路。

## 下一步

- 完善 Gallery 相册
- 接入更多自动化
- 持续更新读书笔记

祝阅读愉快 📚
