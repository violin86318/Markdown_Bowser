# Markdown Bowser

一款超轻量级、零依赖（仅需标准 Python + `mistune` + `pygments`）的 Markdown 预览服务器，专为 macOS 设计，主打移动端响应式布局与无缝的 Cloudflare 内网穿透体验。

## ✨ 核心特性

- **移动端优先体验**: 在桌面端与移动端浏览器上优雅地渲染文件目录和 Markdown 文档。
- **GitHub 风格 Markdown**: 原生支持代码高亮与表格渲染。
- **后台守护进程**: 利用 `nohup` 或 macOS 的 `launchd`，一键运行，长久守护。
- **系统开机自启**: 自动配置 macOS 原生 `launchd` 与 Cloudflare 隧道（`cloudflared`），实现在系统启动时作为安全沙盒服务无感静默运行。
- **内网穿透**: 借助 Cloudflare 安全地将本地的 Markdown 笔记库暴露到公网，彻底告别繁琐的路由器端口映射配置。
- **HTTP 基础认证**: 充当安全门卫，强制拦截未经授权的公网访问请求。

---

## 🚀 快速开始

### 1. 配置应用
复制配置模板并设置你的私密参数：
```bash
cp config.example.sh config.sh
nano config.sh
```
在 `config.sh` 内，设置你的 `TARGET_ROOT`（存放你 Markdown 笔记的绝对文件夹路径）并且修改 `AUTH_CREDS`（用户名:密码）来保护你的外网访问界面。如果需要浏览 `TARGET_ROOT` 之外的目录，把 `ALLOWED_ROOTS` 设置为逗号分隔的绝对路径列表。

### 2. 手动启动 (仅限局域网)
如果你只想在处于本地局域网时让它在后台临时运行：
```bash
./start.sh
```
你可以通过 `./stop.sh` 随时停止服务。

---

## 🌍 云原生自动启动 (高阶玩法)

想把你的 Mac 变成一个永不宕机的云笔记专属服务器？我们精心打造了一个**原生自动自启安装器**。这个脚本会彻底自动化启动你的服务器，并对接免费的 Cloudflare 隧道，让你在全世界任何角落都能通过安全网址访问你的笔记。

### 安装步骤

只需在 macOS 操作系统的访达 (Finder) 界面中，双击运行 `install_autostart.command` 文件。

该脚本将会全自动完成以下魔法：
1. 绕过国内使用 Homebrew 常遇到的卡顿及报错，直接从 GitHub Release 加速节点智能拉取轻量级的 `cloudflared` `bin` 核心包。
2. 将启动脚本克隆到深层的个人目录 `~/.markdown-bowser/` 中（详情请见下方“技术细节”）。
3. 注册 macOS `launchd` plist 系统服务文件以实现开机自启。
4. 在后台为你生成一个公网专属的 `xxx.trycloudflare.com` URL。

### 获取你的公网链接

安装成功后，稍微等待 5 秒钟左右，在终端输入以下命令即可查看内网穿透日志：
```bash
cat ~/.markdown-bowser/logs/tunnel.log
```
在日志中找到类似 `https://xxxx.trycloudflare.com` 的网址，直接在手机或电脑浏览器中打开它，输入你在 `config.sh` 设置的账号密码即可阅览！

想要卸载自动启动服务，双击 `stop_autostart.command` 即可一键清理。

---

## 🛠️ 技术攻坚记录 (为开发者准备)

如果你正在翻阅这套源码，你或许会好奇为何启动逻辑如此迂回曲折。那是因为在适配 macOS 系统时，我们解决了一系列极其顽固的底层限制：

1. **突破 macOS TCC (隐私安全沙盒) 的封锁**:
   在 macOS 较新系统中，`launchd` 会以一种近乎偏执的安全策略，严厉禁止后台静默组件随意读取或写入用户的敏感隐私目录（诸如 `~/Documents`, `~/Desktop`, 和 `~/Downloads`）——这就导致如果你将该项目放在文稿里，系统唤起时会无情地报出 `Operation not permitted` 的底层权限崩溃。
   - **破解法**: 我们的 `install_autostart.command` 巧妙地引入了“绿区沙盒分身机制”：它会在安装时主动将守护进程脚本以及 Python 源码强制隔离克隆到用户根目录下（`~/.markdown-bowser/`）。由于该隐蔽层不在 TCC 强监管范围内，从而实现了彻底逃逸底层拦截。

2. **IPv6 与 IPv4 绑定的冲突避让**:
   在启动 Cloudflare 隧道时，如果我们将其绑定目标设置为 `http://localhost:8642`，macOS 在 DNS 解析时往往会自作主张地将其解析为 IPv6 地址的 `[::1]`。然而，我们的 Python HTTP 服务死死咬定监听着基于 IPv4 的 `0.0.0.0`，这种鸡同鸭讲的通讯偏差会导致隧道立刻疯狂报错 `Connection refused`。
   - **破解法**: 我们在启动脚本中，以雷霆手段将其重定向绑定为了绝对准确的 IPv4 通道：`http://127.0.0.1:8642`。

3. **中国大陆网络环境下的自动化下载劫难**:
   在大陆开发时，若通过原生的 `Homebrew` 拉取 `cloudflared` 必然会频频碰壁——无论是因 `ghcr.io` 注册表遭到系统级屏蔽而陷入无限黑洞，还是遭遇 Xcode 繁文缛节的 license 许可协议阻击。
   - **破解法**: 安装器被直接升级为了轻骨架下载引擎机制。它具备内置测速判定并优先使用加速镜像 `mirror.ghproxy.com` 提取官方源的完整二进制包（Tarball）解压方案，彻底摘除了针对 Homebrew 的依赖症，保证在各种恶劣网络下畅通无阻。
