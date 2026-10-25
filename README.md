# guodongsubs.com

GuodongSubs 官网 —— 静态版（Hugo + Stack），部署在 GitHub Pages，原 Typecho 站（DigitalOcean）的完整迁移。

## 目录结构

```
site/
├── hugo.toml            # 站点配置（标题/菜单/分类/输出）
├── content/
│   ├── posts/           # 全部文章（文件名 = 原 Typecho 文章 ID）
│   ├── pages/           # 独立页面（About / Projects / Recruitment / Notice）
│   └── archives.md      # 归档页（替代原 tags-and-archives）
├── static/
│   ├── uploads/         # 原 /usr/uploads 全部图片（路径保持一致）
│   └── CNAME            # 自定义域名 guodongsubs.com
├── layouts/404.html     # 旧链接重定向（/index.php/archives/N/ 等 → 新地址）
├── tools/nyaa_watch.py  # Nyaa 发布监控脚本
└── .github/workflows/
    ├── deploy.yml        # push 后自动构建并部署到 GitHub Pages
    └── nyaa-watcher.yml  # 每小时检查 Nyaa RSS，出新种自动发文
```

## 日常使用

**写新文章**：在 `content/posts/` 放一个 Markdown 文件（front matter 仿照现有文章），push 后自动上线。

**改主题/外观**：改 `hugo.toml`；本地预览：`hugo serve`（需安装 Hugo extended）。

**自动追更**：`nyaa-watcher.yml` 每小时跑一次 `tools/nyaa_watch.py`，发现 GuodongSubs 在 Nyaa 的新种子就自动生成文章并部署。发布记录存在 `data/nyaa_seen.json`，不会重复发。标题含 [JP]/日本語 会自动归入日文分类，否则英文分类；可发文后手动调整。

**手动跑一次追更**：GitHub 仓库 → Actions → "Nyaa release watcher" → Run workflow。

## 旧链接兼容

所有旧 Typecho 地址仍然可用（浏览器端自动跳转）：
- `/index.php/archives/123/` → `/archives/123/`
- `/index.php/about.html` → `/about/`
- `/EN/xxx.html`、`/JP/xxx.html`（老站本来就 404 的美化链接）→ 对应文章页
- `/index.php/feed` → `/index.xml`（RSS）

## 上线步骤（一次性）

1. GitHub 仓库 Settings → Pages → Source 选 **GitHub Actions**。
2. 域名 DNS：把 `guodongsubs.com` 的 A 记录指到 GitHub Pages（185.199.108.153 / .109 / .110 / .111）或 CNAME 指到 `<用户名>.github.io`；等证书签发后勾选 Enforce HTTPS。
3. 原站确认无误后，销毁 DigitalOcean droplet。
