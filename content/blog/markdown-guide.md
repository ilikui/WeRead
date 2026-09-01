---
title: "Markdown 全格式指南：Mermaid、数学公式与更多"
date: 2026-09-01
tags: ["Markdown", "Hugo", "教程"]
summary: "一篇涵盖 Mermaid 流程图、KaTeX 数学公式、表格、脚注、任务列表、定义列表等全部 Markdown 能力的示例文章。"
toc: true
---

本文演示本站博客支持的全部 Markdown 能力。你只需在 `content/blog/` 下新建 `.md` 文件，用纯 Markdown 编写即可。

## 表格

| 特性 | 语法 | 状态 |
| --- | --- | --- |
| 表格 | `\| a \| b \|` | ✅ |
| 脚注 | `[^1]` | ✅ |
| 任务列表 | `- [x]` | ✅ |
| Mermaid | ` ```mermaid ` | ✅ |
| 数学公式 | `$$ ... $$` | ✅ |

## 代码块（含语法高亮）

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("WeRead"))
```

## Mermaid 流程图

```mermaid
flowchart TD
    A[开始] --> B{是否有笔记?}
    B -- 是 --> C[生成卡片]
    B -- 否 --> D[结束]
    C --> D
```

再来一个时序图：

```mermaid
sequenceDiagram
    participant U as 用户
    participant H as Hugo
    U->>H: 编写 Markdown
    H->>H: 渲染为 HTML
    H-->>U: 返回页面
```

## 数学公式

行内公式 $E = mc^2$ 与独立公式：

$$
\int_{-\infty}^{+\infty} e^{-x^2}\,dx = \sqrt{\pi}
$$

## 引用

> 读一本好书，就是和许多高尚的人谈话。 —— 歌德

## 任务列表

- [x] 接入微信读书数据
- [x] 卡片化博客
- [ ] 上线 Gallery

## 定义列表

Hugo
: 一个用 Go 编写的静态站点生成器

Mermaid
: 基于文本的图表绘制工具

## 脚注与删除线

本站支持脚注[^1]和~~删除线~~。

[^1]: 这是脚注内容，会显示在文章末尾。
