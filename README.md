<div align="center">

# WeRead · 个人阅读与知识记录站

**把微信读书的阅读笔记、Flomo 的日常灵感与原创文章，汇集成一个可持续发布的个人知识空间。**

[在线站点](https://blog.zzek.cn/) · [阅读笔记](https://blog.zzek.cn/weread/) · [Memos 灵感](https://blog.zzek.cn/memos/) · [博客](https://blog.zzek.cn/blog/) · [相册](https://blog.zzek.cn/gallery/)

![Hugo](https://img.shields.io/badge/Hugo-Static%20Site-blue?logo=hugo)
![Python](https://img.shields.io/badge/Python-Data%20Export-3776AB?logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automation-2088FF?logo=githubactions&logoColor=white)

</div>

---

## 项目简介

WeRead 是一个基于 **Hugo** 的静态阅读与知识记录站，使用 Python 整理数据，并通过 GitHub Actions 自动构建与发布。项目将不同来源的知识内容汇集到统一、可检索、便于长期维护的网站中。

| 栏目 | 主要内容 | 访问入口 |
| --- | --- | --- |
| **阅读笔记** | 微信读书书籍、阅读记录与笔记 | [打开阅读页](https://blog.zzek.cn/weread/) |
| **Memos 灵感库** | Flomo memo、标签筛选与全文搜索 | [打开 Memos](https://blog.zzek.cn/memos/) |
| **博客** | Markdown 文章、技术记录与知识整理 | [打开博客](https://blog.zzek.cn/blog/) |
| **相册** | 个人图片与图像浏览 | [打开相册](https://blog.zzek.cn/gallery/) |

## 内容流转

~~~mermaid
flowchart LR
    A[微信读书] --> E[Python 数据导出]
    B[Flomo 灵感] --> E
    C[Markdown 文章] --> F[Hugo 构建]
    D[相册资源] --> F
    E --> G[结构化数据]
    G --> F
    F --> H[静态网站]
    H --> I[阅读笔记]
    H --> J[Memos]
    H --> K[博客与相册]
~~~

## 技术栈

- **Hugo**：静态站点生成与页面模板渲染。
- **Python**：导出、整理微信读书与 Flomo 数据。
- **JSON / Markdown**：分别承载结构化数据与可维护内容。
- **GitHub Actions**：自动运行数据更新、构建和部署流程。
- **Mermaid / KaTeX**：用于知识关系图、流程图与数学公式（以当前站点配置为准）。

## 项目结构

~~~text
.
├── .github/workflows/
│   └── export-weread-notes.yml   # 数据更新、构建与部署
├── archetypes/                   # Hugo 内容模板
├── assets/css/                   # 站点样式
├── content/
│   ├── blog/                     # Markdown 博客
│   ├── gallery/                  # 相册栏目
│   ├── memos/                    # Memos 页面内容
│   └── weread/                   # 阅读栏目内容
├── layouts/                      # 页面布局与模板
├── static/
│   ├── data/
│   │   ├── weread_notes.json     # 微信读书数据
│   │   └── flomo_memos.json      # Flomo memo 数据
│   └── gallery/                  # 相册图片
├── weread_hugo_exporter.py       # 数据导出脚本
├── hugo.yml                      # Hugo 配置
└── README.md
~~~

## 快速开始

### 环境准备

安装 [Hugo](https://gohugo.io/installation/) 与 Python 3，然后在仓库根目录运行：

~~~bash
hugo version
python --version
~~~

### 本地预览

~~~bash
hugo server -D
~~~

打开 <http://localhost:1313/> 即可预览。Hugo 会监听文件变化，便于边写作边检查页面。

### 构建网站

~~~bash
hugo --gc --minify
~~~

构建产物默认生成在 public/。一般应修改 content/、layouts/、assets/、static/ 或配置文件，而不是直接编辑构建产物。

## 内容维护

### 写博客

在 content/blog/ 中创建 Markdown 文件：

~~~~markdown
---
title: "从一个问题开始"
date: 2026-10-24
draft: false
---

## 观察与思考

记录问题、证据、推理过程和结论。

~~~mermaid
flowchart TD
    A[问题] --> B[证据]
    B --> C[结论]
~~~
~~~~

文章可以使用标准 Markdown、表格、任务列表和代码块；Mermaid 图表、数学公式等功能以当前模板配置为准。

### 更新相册

将图片放入 static/gallery/，并按照相册页面现有规则组织内容。建议使用清晰的文件名、压缩较大的图片，以改善加载速度和后续维护体验。

## 微信读书与 Flomo 数据导出

导出脚本为 weread_hugo_exporter.py，生成的数据位于 static/data/：

- **weread_notes.json**：微信读书笔记数据。
- **flomo_memos.json**：Flomo memo 数据。

### 微信读书配置

~~~bash
export WEREAD_API_KEY="your-api-key"
export WEREAD_API_GATEWAY="https://i.weread.qq.com/api/agent/gateway"
~~~

### Flomo 配置

~~~bash
pip install flomo
export FLOMO_AUTHORIZATION="your-flomo-authorization"
export FLOMO_TAG=""
~~~

**Flomo 默认导出全部 memo。** 将 FLOMO_TAG 留空即可不按标签过滤；如需限定范围，可填写标签，例如 Archive/Blog，此时仅导出该标签及其子标签范围的数据。

在仓库根目录执行：

~~~bash
python weread_hugo_exporter.py --site-dir .
~~~

运行前可通过以下命令查看当前版本支持的参数：

~~~bash
python weread_hugo_exporter.py --help
~~~

请妥善保管授权令牌，不要把真实的 API Key、Authorization 值或其他密钥提交到仓库。

## GitHub Actions 自动发布

工作流配置位于 [.github/workflows/export-weread-notes.yml](.github/workflows/export-weread-notes.yml)。它支持的触发方式与部署步骤以该文件的实际配置为准。

1. 打开仓库 **Settings → Secrets and variables → Actions**。
2. 添加工作流所需的 Secrets，例如 WEREAD_API_KEY；启用 Flomo 自动导出时，还需要 FLOMO_AUTHORIZATION。
3. 打开 **Settings → Pages**，确认发布来源与工作流部署方式匹配。
4. 在 **Actions** 页面查看最新运行记录。构建和部署均成功后，再检查线上页面。

### 数据没有更新时如何排查

1. 查看 Actions 最近一次运行是否成功，重点检查数据导出与部署步骤。
2. 查看 static/data/flomo_memos.json 中的 meta.total_memos。
3. 对比线上 JSON 响应与仓库文件是否一致。
4. 如果 JSON 数据正确但页面仍旧显示旧内容，检查浏览器控制台、数据请求路径及缓存。

不要仅凭工作流已启动或某一个步骤成功，就判断网站已经完成更新。

## 常见问题

**Memos 显示数量少于 Flomo？**

先确认 FLOMO_TAG 是否留空，再检查导出日志和 JSON 中的 meta.total_memos。如果仓库 JSON 已有完整数据而页面不一致，继续核对线上 JSON 响应与页面请求结果。

**修改文章后线上没有变化？**

确认修改已提交到正确分支，检查 Actions 的最新结果，并确认 GitHub Pages 发布来源配置正确。

**如何安全地调试？**

优先在本地预览和构建；使用环境变量或 GitHub Secrets 管理敏感配置。提交前检查差异，避免意外上传授权信息或个人隐私数据。

## 参与维护

欢迎通过 Issue 反馈问题、提出改进建议，或提交 Pull Request。建议提交前完成以下检查：

- [ ] 检查 Markdown、YAML 和链接路径。
- [ ] 本地执行 hugo --gc --minify。
- [ ] 检查新增页面与静态资源是否正常。
- [ ] 确认没有提交密钥、授权令牌或不必要的生成文件。

---

<div align="center">

**持续阅读 · 持续记录 · 持续创造**

<sub>由 Hugo、Python 与 GitHub Actions 驱动的个人知识记录站</sub>

</div>
