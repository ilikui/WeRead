# WeRead → Hugo 读书笔记博客

基于 `ReadMe.md` 在 `Hugo/` 目录中实现的 Hugo 静态博客，包含 **阅读（Read）**、**博客（Blog）**、**相册（Gallery）** 三个板块。

## 项目结构

```
Hugo/
├── archetypes/                       # Hugo 内容模板
├── assets/css/weread-theme.css       # 主题样式
├── content/
│   ├── about.md                      # 关于页面
│   ├── blog/                         # 博客（Markdown 编写，卡片式展示）
│   ├── gallery/_index.md             # 相册页
│   └── weread/                       # 阅读页（每本书一个 .md）
├── layouts/
│   ├── _default/                     # 默认布局（baseof / list / single）
│   ├── blog/                         # 博客卡片列表 + 文章页
│   ├── gallery/                      # 相册布局
│   ├── partials/markdown-extensions.html  # Mermaid / KaTeX 按需加载
│   ├── weread.html                   # 阅读页主布局（书架 + 笔记详情）
│   └── shortcodes/weread-card.html
├── static/
│   ├── data/weread_notes.json        # 笔记 JSON 数据
│   └── gallery/                      # 相册图片（放入即自动展示）
├── .github/workflows/export-weread-notes.yml  # 自动化导出 + 部署
├── hugo.yml                          # Hugo 站点配置
└── weread_hugo_exporter.py           # 微信读书 → Hugo 导出脚本
```

## 本地预览

```bash
cd Hugo
hugo server -D
```

访问 <http://localhost:1313/weread/> 查看阅读页；Blog 在 `/blog/`，相册在 `/gallery/`。

## 博客写作

在 `content/blog/` 下新建 `.md` 文件即可，自动以卡片形式出现在博客列表页，支持全部标准 Markdown 语法以及：

- **Mermaid 图表**：使用 ` ```mermaid ` 代码围栏
- **数学公式**：`$...$` 行内、`$$...$$` 独立公式（KaTeX）
- 表格、脚注、任务列表、定义列表、删除线、代码高亮等

示例见 `content/blog/markdown-guide.md`。

## 相册

把图片放入 `static/gallery/` 目录即可自动展示，点击可放大查看。支持 jpg/png/gif/webp/bmp/svg。

## 从微信读书导出真实数据

1. 配置环境变量：

```bash
export WEREAD_API_KEY="your-api-key"
export WEREAD_API_GATEWAY="https://i.weread.qq.com/api/agent/gateway"
```

2. 运行导出脚本：

```bash
cd Hugo
python weread_hugo_exporter.py --site-dir .
```

3. 重新构建站点：

```bash
hugo --gc --minify
```

## GitHub Actions 自动更新与部署

工作流 `.github/workflows/export-weread-notes.yml` 会在以下时机运行：

- **每天晚上 12 点**（北京时间 00:00 = UTC 16:00）自动拉取微信读书数据并部署
- 推送到 `main` 分支时（发布博客/相册等新内容）
- 手动触发（`workflow_dispatch`）

启用步骤：

1. 在仓库 **Settings → Secrets and variables → Actions** 添加密钥 `WEREAD_API_KEY`（微信读书 API 密钥）。
2. 在 **Settings → Pages** 中，将 **Source** 设为 **GitHub Actions**。
3. 推送代码到 `main`，等待工作流完成即可通过 Pages 链接访问。

工作流会在构建时自动计算 baseURL，同时兼容「用户/组织站点」（`<user>.github.io`）与「项目站点」（`<user>.github.io/<repo>/`）两种子路径。
