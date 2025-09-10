# Gemini CLI MCP Bridge

一个将本地 Gemini CLI 暴露为 MCP 服务器的小工具，提供常用的 Gemini CLI 包装器与文件/网络实用工具，适配 Gemini CLI、Claude Code（VS Code）等支持 MCP 的客户端。

注意：在各客户端列表/配置中，本服务名称显示为 “Gemini”。启动命令仍为 `gemini-cli-bridge`（或 `uvx --from . gemini-cli-bridge`）。

## 特性

- 标准 MCP（stdio）服务，开箱即用
- 封装常用 Gemini CLI 操作：版本查询、Prompt、WebFetch/Search、MCP 管理等
- 内置实用工具：读写文件、目录遍历、简单抓取、文本搜索、可选 Shell（默认禁用）
- 兼容 uv/uvx 一次性运行，免手动装依赖

## 前置条件

- Python 3.10+（建议 3.11+）
- 已安装并完成认证的 Gemini CLI（用于真正调用模型）
- macOS 推荐将 Homebrew bin 加入 PATH：`/opt/homebrew/bin`

快速自检：

```zsh
python3 --version
which gemini && gemini --version
```

## 安装与运行

在开始之前，先将仓库克隆到本地：

```zsh
git clone https://github.com/chaodongzhang/gemini_cli_bridge.git
cd gemini_cli_bridge
```

方式 A（推荐，全局安装一次，后续任意目录可用）：

```zsh
# 使用 uv 将命令安装到全局工具路径
uv tool install --from . gemini-cli-bridge

# 验证（应能在任意目录执行）
gemini-cli-bridge
```

提示：确保将 uv 工具目录加入 PATH。

- macOS（zsh）：

  ```zsh
  # uv 工具路径通常为：$HOME/Library/Application Support/uv/tools/bin
  echo 'export PATH="$HOME/Library/Application Support/uv/tools/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
  ```

- Linux：`~/.local/bin` 通常已在 PATH，如无则自行加入。

方式 B（一键试用，本地仓库内运行）：

```zsh
# 在仓库根目录一次性运行（uv 会解析 pyproject 并临时安装依赖）
uvx --from . gemini-cli-bridge
```

方式 C（直接运行脚本）：

```zsh
python3 ./gemini_cli_bridge.py
```

## 在常见客户端中接入（安装/配置示例）

以下示例均为 stdio 方式，命令与路径请按本机实际调整。

### 1) Codex CLI（官方建议的 MCP 配置）

Codex 通过 TOML 配置文件启用 MCP 服务器（当前仅支持全局配置）：`~/.codex/config.toml`。在该文件中添加：

```toml
[mcp_servers.Gemini]
command = "gemini-cli-bridge"
args = []

[mcp_servers.Gemini.env]
NO_COLOR = "1"
```

说明：

- 路径：目前仅支持全局 `~/.codex/config.toml`（macOS/Linux）。Windows 建议使用 WSL，并在其家目录下同一路径配置。
- 截至 2025-09-10，Codex 尚不自动加载“项目目录内的 .codex/config.toml”。如需此能力，请关注社区提案与后续版本更新。
- 变更后重启 Codex CLI。第一次使用会提示信任与认证。
- 在 Codex 中输入提示后，可调用本服务工具；建议先调用 `gemini_version` 做健康检查。


### 2) Claude Code（VS Code 扩展）

安装 VS Code 与 Claude Code 扩展（在扩展市场搜索“Claude Code”并安装）。

在 VS Code 用户设置 JSON 中添加（命令面板：Preferences: Open User Settings (JSON)）：

```json
{
  "claude.mcpServers": {
  "Gemini": {
  "command": "gemini-cli-bridge",
  "args": [],
      "env": {"NO_COLOR": "1"}
    }
  }
}
```

保存后在 Claude 侧边栏的工具/服务器列表中可见；尝试调用 `gemini_version` 验证。

### 3) 通用 MCP CLI（用于本地调试）

以开源 MCP CLI 为例（任选其一的 CLI 工具）：

```zsh
# 安装某个通用 MCP CLI（示例命令，按工具文档调整）
npm i -g @modelcontextprotocol/cli

# 启动并连接本服务（示例）
mcp-cli --server gemini-cli-bridge
```

### 4) Claude Desktop（可选）

多数版本支持在配置文件中添加：

```json
{
  "mcpServers": {
  "Gemini": {
  "command": "gemini-cli-bridge",
  "args": [],
      "env": {"NO_COLOR": "1"}
    }
  }
}
```

若路径/键名与版本差异，请以应用内文档为准。

## 典型用法（在客户端内）

- 查询版本：`gemini_version`
- 非交互推理：`gemini_prompt(prompt=..., model="gemini-2.5-pro")`
- 附件/审批等高级推理：`gemini_prompt_plus(...)`
- Web 抓取：`gemini_web_fetch(prompt, urls=[...])`
- 管理 Gemini CLI 的 MCP：`gemini_mcp_list / gemini_mcp_add / gemini_mcp_remove`

### MCP 工具调用请求示例

从任意 MCP 客户端调用 `gemini_prompt_plus` 的 payload 示例：

```json
{
  "name": "gemini_prompt_plus",
  "arguments": {
    "prompt": "hello",
    "extra_args": ["--debug", "--proxy=http://127.0.0.1:7890"]
  }
}
```

## 常见问题

1. 找不到 gemini 或权限问题

```zsh
which gemini
gemini --version
echo $PATH
```

Apple Silicon 常见：将 `/opt/homebrew/bin` 加入 PATH，或在客户端配置中为本服务显式设置 PATH。

1. 未登录/未授权

```zsh
gemini  # 按提示完成一次登录
```

1. 代理/超时

可通过工具参数 `timeout_s` 或 `extra_args: ["--proxy=http://..."]` 调整。

## 启动/握手超时排查（MCP client failed to start: request timed out）

常见原因：

- 使用 `uvx --from . gemini-cli-bridge` 冷启动时需要解析依赖，首次/网络慢时可能超过客户端握手超时。
- 网络访问受限导致依赖解析缓慢。
- 客户端默认握手超时较短。

建议修复：

1) 预安装后使用已安装命令，避免每次 uvx 解析

```zsh
# 二选一（开发态可用 -e）
pip install .
# pip install -e .

# 或使用 pipx/uv 工具将脚本安装为独立命令
# pipx install .
# uv tool install --from . gemini-cli-bridge
```

将 Codex 全局配置 `~/.codex/config.toml` 调整为直接调用已安装命令：

```toml
[mcp_servers.Gemini]
command = "gemini-cli-bridge"
args = []

[mcp_servers.Gemini.env]
NO_COLOR = "1"
```

1) 如果必须使用 uvx，考虑在客户端上调启动/握手超时（若客户端支持），并确保网络可达。

1) 本地快速自检：

```zsh
gemini-cli-bridge   # 启动服务，应快速常驻
which gemini && gemini --version
```

1) PATH 问题：将 `/opt/homebrew/bin` 加入 PATH，或在客户端配置中通过 env 显式设置。

## 许可

MIT
