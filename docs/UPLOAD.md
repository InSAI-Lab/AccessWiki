# 上传到现有 GitHub 仓库

本次最终整理目录名为 AccessWiki。此前的 AccessWiki-demo 和 accesswiki-github 是旧版交付，不需要一起上传。

1. 登录 GitHub，打开 InSAI-Lab/AccessWiki。
2. 若空仓库显示 uploading an existing file，点击它；有文件时选择 Add file → Upload files。
3. 打开本地 AccessWiki 文件夹，拖入其内部文件与目录。不要把外层 AccessWiki 文件夹嵌套到仓库里，也不要只上传 ZIP。确认根目录能看到 README.md、index.html、generators、experiments、topics、docs。
4. 若已存在同名文件，先比较变更，并优先用新分支提交，避免覆盖团队工作。
5. Commit message 可填 Add AccessWiki code and runnable study materials。
6. 按页面选项提交；使用新分支时创建 Pull request 并检查差异，再由有权限的人合并。
7. 提交后确认根目录 README 显示、generators 下两份 Python、formal_v01 下音频及脚本均存在。

浏览器支持每次最多 100 文件、单文件最大 25 MiB；此包按实际文件数和体积检查后给出结果。规则来源：[GitHub 上传说明](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)。

上传代码不等于发布在线网页。先完成仓库内容，再决定是否启用 GitHub Pages。没有访问权限时需要项目维护者授权，不需要向任何人提供登录密码。
