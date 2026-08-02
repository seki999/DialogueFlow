# DialogueFlow

一个可直接部署到 GitHub Pages 的双人对话课程播放器。页面读取仓库内的 Markdown 与 `.conversation` 素材，渲染课程内容、Mermaid 图表，并使用浏览器原生 Web Speech API 播放 Speaker 1 / Speaker 2 对话。

> 本版本不包含录屏、录音、FFmpeg、服务端 TTS 或音频缓存功能。站点是纯静态网页，不需要 Python、数据库、API Key 或后端服务器。

## 在线功能

- 递归识别 `slides/` 下的课程目录和数字编号章节
- 渲染 Markdown、表格、任务列表、折叠答案和 Mermaid 图表
- 支持汉语、日语、英语对话文件与通用兜底文件
- Speaker 1 默认优先匹配男音，Speaker 2 默认优先匹配女音
- 页面内可分别选择两个角色的浏览器声音
- 支持整段、单章、单句播放以及暂停、继续、停止
- 支持语速、音量、音高、字幕字号和章节范围调节
- 响应式布局，可在桌面和手机浏览器使用
- GitHub Actions 自动构建并部署 GitHub Pages

## 浏览器声音说明

网页使用 `window.speechSynthesis`，声音来自访问者的浏览器和操作系统。Web Speech API 不提供统一的“性别”字段，因此程序会根据常见声音名称优先匹配男音和女音，并把当前设备实际可用的声音全部列在下拉框中供手动确认或更换。

不同设备、浏览器和操作系统显示的声音名称可能不同。推荐使用最新版 Chrome 或 Edge。若系统没有当前语言的声音，浏览器可能使用默认声音；页面文字和其他功能仍可正常使用。

## 本地运行

需要 Node.js 22 或更高版本。

```bash
npm install
npm run dev
```

浏览器打开终端显示的本地地址。第一次播放语音必须由用户点击“开始播放”或某条对话，这是浏览器的自动播放安全限制。

完整验证：

```bash
npm run verify
```

生产构建输出在 `dist/`。

## 部署到 GitHub Pages

仓库已包含 [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)。

1. 将代码推送到 GitHub 仓库的 `main` 分支。
2. 打开仓库的 **Settings → Pages**。
3. 在 **Build and deployment → Source** 选择 **GitHub Actions**。
4. 打开 **Actions**，等待 `Deploy GitHub Pages` 工作流完成。
5. 页面地址通常是 `https://<用户名>.github.io/<仓库名>/`。

Vite 使用相对资源路径，因此仓库名无需写死，既支持项目站点子路径，也支持 `<用户名>.github.io` 根站点。

## 添加课程

课程目录可以任意嵌套；某个目录中只要直接包含数字命名的 Markdown 文件，就会成为一门可选课程：

```text
slides/
  课程名称/
    中文版/
      01.md
      01.conversation
      02.md
      02.conversation
```

对话格式：

```text
speaker 1: 这是第一句话
speaker 2: 这是第二句回应
speaker 1: 这一句话可以换行
           没有新 speaker 标记的行会继续接在上一句后面
```

多语言文件可使用：

```text
01.conversation.zh
01.conversation.ja
01.conversation.en
```

如果语言专属文件不存在，播放器会使用不带语言后缀的 `01.conversation`。它只会改变朗读声音，不会自动翻译文本。

## 技术边界

- GitHub Pages 只能托管静态文件，不能运行原项目的 Flask/Python 进程。
- 语音由访问者本机浏览器即时合成，不会生成或上传 MP3/WAV 文件。
- 站点不会录制屏幕、麦克风或系统声音。
- `slides/` 内容在构建时打包；更新课程后需重新触发 GitHub Actions 部署。
