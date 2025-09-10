# Gemini CLI MCP Bridge — 工具清单与最小示例

> 前置条件：已安装并完成认证的 `gemini` CLI；将本服务器作为 MCP（stdio）方式接入你的客户端。

## 工具与签名

下表与当前服务器已注册的工具保持一致（见工具列表截图）。

| 工具名 | 签名（简化） | 返回 |
|---|---|---|
| gemini_extensions_list | `gemini_extensions_list(timeout_s?: number)` | string |
| gemini_mcp_add | `gemini_mcp_add(name: string, command_or_url: string, transport?: "stdio"&#124;"http"&#124;"sse", args?: string[], env_vars?: Record<string,string>, headers?: Record<string,string>, scope?: "user"&#124;"project", timeout_ms?: number, trust?: boolean, description?: string, include_tools?: string[], exclude_tools?: string[], timeout_s?: number)` | string |
| gemini_mcp_list | `gemini_mcp_list(scope?: "user"&#124;"project", timeout_s?: number)` | string |
| gemini_mcp_remove | `gemini_mcp_remove(name: string, scope?: "user"&#124;"project", timeout_s?: number)` | string |
| gemini_prompt | `gemini_prompt(prompt: string, model?: string, include_dirs?: string[], timeout_s?: number, extra_args?: string[])` | string |
| gemini_prompt_plus | `gemini_prompt_plus(prompt: string, model?: string, include_dirs?: string[], attachments?: string[], approval_mode?: "default"&#124;"auto_edit"&#124;"yolo", yolo?: boolean, checkpointing?: boolean, extra_args?: string[], timeout_s?: number)` | string |
| gemini_prompt_with_memory | `gemini_prompt_with_memory(prompt: string, memory_paths?: string[], attachments?: string[], model?: string, include_dirs?: string[], approval_mode?: string, yolo?: boolean, checkpointing?: boolean, extra_args?: string[], timeout_s?: number)` | string |
| gemini_search | `gemini_search(query: string, model?: string, include_dirs?: string[], approval_mode?: string, yolo?: boolean, checkpointing?: boolean, extra_args?: string[], timeout_s?: number)` | string |
| gemini_version | `gemini_version(timeout_s?: number)` | string |
| gemini_web_fetch | `gemini_web_fetch(prompt: string, urls: string[], model?: string, include_dirs?: string[], approval_mode?: string, yolo?: boolean, checkpointing?: boolean, extra_args?: string[], timeout_s?: number)` | string |

### 示例调用（通用工具）

```json
{
  ## 通用系统/网络工具（定制版）

  Available Gemini CLI tools:

  - Edit
  - FindFiles
  - GoogleSearch
  - ReadFile
  - ReadFolder
  - ReadManyFiles
  - Save Memory
  - SearchText
  - Shell
  - WebFetch
  - WriteFile

  | 工具名 | 签名（简化） | 返回 |
  |---|---|---|
  | Edit | `Edit(path: string, find: string, replace: string, count?: number)` | JSON {replaced} |
  | FindFiles | `FindFiles(pattern?: string, base?: string, recursive?: boolean)` | JSON 路径数组 |
  | GoogleSearch | `GoogleSearch(query: string, limit?: number, cse_id?: string, api_key?: string)` | JSON {ok,results[],error?} |
  | ReadFile | `ReadFile(path: string)` | 文件文本 |
  | ReadFolder | `ReadFolder(path?: string, recursive?: boolean, max_entries?: number)` | JSON 路径数组 |
  | ReadManyFiles | `ReadManyFiles(paths: string[], ignore_missing?: boolean)` | JSON {path: content} |
  | Save Memory | `SaveMemory(path: string, content: string, mode?: "append"|"overwrite")` | JSON {ok,bytes,error?} |
  | SearchText | `SearchText(pattern: string, path: string, case_insensitive?: boolean)` | JSON [{line,text}] |
  | Shell | `Shell(cmd: string, cwd?: string, timeout_s?: number)` | JSON {code,stdout,stderr} |
  | WebFetch | `WebFetch(url: string, timeout_s?: number)` | JSON {ok,status,content?,error?} |
  | WriteFile | `WriteFile(path: string, content: string)` | ok |

  ### 示例调用（通用工具）

  ```json
  {"name": "Edit", "arguments": {"path": "tmp/demo.txt", "find": "hello", "replace": "hi"}}
  ```

  ```json
  {"name": "FindFiles", "arguments": {"pattern": "**/*.md", "base": "."}}
  ```

  ```json
  {"name": "GoogleSearch", "arguments": {"query": "MCP protocol", "limit": 3}}
  ```

  ```json
  {"name": "ReadFile", "arguments": {"path": "README.md"}}
  ```

  ```json
  {"name": "ReadFolder", "arguments": {"path": ".", "recursive": false}}
  ```

  ```json
  {"name": "ReadManyFiles", "arguments": {"paths": ["README.md", "pyproject.toml"]}}
  ```

  ```json
  {"name": "SaveMemory", "arguments": {"path": "GEMINI.md", "content": "notes...", "mode": "append"}}
  ```

  ```json
  {"name": "SearchText", "arguments": {"pattern": "^# ", "path": "README.md"}}
  ```

  ```json
  {"name": "Shell", "arguments": {"cmd": "echo hello"}}
  ```

  ```json
  {"name": "WebFetch", "arguments": {"url": "https://example.com"}}
  ```

  ```json
  {"name": "WriteFile", "arguments": {"path": "tmp/x.txt", "content": "hello"}}
  ```
| LS | `LS(path?: string)` | JSON 字符串（数组） |
| Glob | `Glob(pattern: string, base?: string)` | JSON 字符串（数组） |
| Grep | `Grep(pattern: string, path: string, case_insensitive?: boolean)` | JSON 字符串（数组） |
| Read | `Read(path: string)` | string（文件文本） |
| Write | `Write(path: string, content: string)` | string（ok） |
| Edit | `Edit(path: string, find: string, replace: string, count?: number)` | JSON 字符串 {replaced} |
| MultiEdit | `MultiEdit(edits: Array<{path, find, replace, count?}>)` | JSON 字符串 {path: replaced} |
| NotebookEdit | `NotebookEdit(path: string, edits?: Array<Record<string, any>>)` | string（ok） |
| Task | `Task(title: string, detail?: string, tags?: string[])` | JSON 字符串（任务对象） |
| TodoWrite | `TodoWrite(path: string, title: string, detail?: string, tags?: string[])` | string（ok） |
| ExitPlanMode | `ExitPlanMode(enable: boolean)` | string（PLAN_MODE=...） |
| WebFetch | `WebFetch(url: string, timeout_s?: number)` | JSON 字符串 {ok,status,content?,error?} |
| WebSearch | `WebSearch(query: string, limit?: number)` | JSON 字符串 {ok,results[],hint?} |

### 示例调用

```json
{"name": "Bash", "arguments": {"cmd": "echo hello"}}
```

```json
{"name": "BashOutput", "arguments": {"cmd": "uname -a"}}
```

```json
{"name": "LS", "arguments": {"path": "."}}
```

```json
{"name": "Glob", "arguments": {"pattern": "**/*.md", "base": "."}}
```

```json
{"name": "Grep", "arguments": {"pattern": "^# ", "path": "README.md"}}
```

```json
{"name": "Read", "arguments": {"path": "README.md"}}
```

```json
{"name": "Write", "arguments": {"path": "tmp/demo.txt", "content": "hello"}}
```

```json
{"name": "Edit", "arguments": {"path": "tmp/demo.txt", "find": "hello", "replace": "hi"}}
```

```json
{
  "name": "MultiEdit",
  "arguments": {
    "edits": [
      {"path": "tmp/a.txt", "find": "foo", "replace": "bar"},
      {"path": "tmp/b.txt", "find": "x", "replace": "y", "count": 1}
    ]
  }
}
```

```json
{
  "name": "NotebookEdit",
  "arguments": {"path": "tmp/plan.ipynb", "edits": [{"cell": 0, "op": "insert", "text": "demo"}]}
}
```

```json
{"name": "Task", "arguments": {"title": "Ship feature", "detail": "add tests", "tags": ["feat", "test"]}}
```

```json
{"name": "TodoWrite", "arguments": {"path": "TODO.md", "title": "Refactor", "detail": "extract utils"}}
```

```json
{"name": "ExitPlanMode", "arguments": {"enable": true}}
```

```json
{"name": "WebFetch", "arguments": {"url": "https://example.com"}}
```

```json
{"name": "WebSearch", "arguments": {"query": "MCP protocol overview", "limit": 3}}
```

## 备注

- attachments 与 memory_paths 可传入相对或绝对路径；文内会自动转为 `@path` 注入。
- 审批策略优先使用 `approval_mode`（default|auto_edit|yolo）；若未指定且 `yolo=true`，则使用 `--yolo`。
- 出错会返回子进程 `stderr` 或退出码信息，便于快速定位。

## 快速接入配置示例

前置：确保已安装 Python 3.10+ 与 `fastmcp`，并能在终端运行 `gemini --version`。

### 方式 A：在 Gemini CLI 中接入本 MCP 服务器

在项目根目录 `.gemini/settings.json`（或用户 `~/.gemini/settings.json`）中加入：

```json
{
  "mcpServers": {
    "gemini-cli-bridge": {
      "command": "python3",
      "args": ["/absolute/path/to/gemini_cli_bridge.py"],
      "trust": false,
      "timeout": 60000
    }
  }
}
```

重启 `gemini` 后，使用 `/mcp` 查看是否成功发现工具，或直接让模型调用如 `gemini_version`。

### 方式 B：在通用 MCP 客户端（如 Claude Desktop/VS Code 插件）中接入

多数 MCP 客户端支持 stdio 方式配置，示例：

```json
{
  "mcpServers": {
    "gemini-cli-bridge": {
      "command": "python3",
      "args": ["/absolute/path/to/gemini_cli_bridge.py"],
      "env": {
        "NO_COLOR": "1"
      }
    }
  }
}
```

保存后在客户端的工具列表中应能看到上述工具。建议先调用 `gemini_version` 做健康检查。

## 用 uv/uvx 运行与接入

推荐使用 uv（更快的 Python 包管理器）以隔离依赖，并通过 `uvx` 一次性运行：

### 一次性直接运行（无需手动安装依赖）

```zsh
# 方式 1：本地源码
uvx --from . gemini-cli-bridge

# 方式 2：若已发布到 PyPI，可直接
# uvx gemini-cli-bridge
```

### 在 Gemini CLI 中以 uvx 接入（stdio）

在 `.gemini/settings.json` 配置：

```json
{
  "mcpServers": {
    "gemini-cli-bridge": {
      "command": "uvx",
      "args": ["--from", ".", "gemini-cli-bridge"],
      "trust": false,
      "timeout": 60000,
      "env": {"NO_COLOR": "1"}
    }
  }
}
```

说明：

- `--from "."` 表示从当前目录的 `pyproject.toml` 解析依赖并临时运行；若你将包发布到 PyPI，替换为 `"gemini-cli-bridge"` 即可。
- 首次启动会自动解析并构建隔离环境；之后会缓存，启动更快。


### 在通用 MCP 客户端中以 uvx 接入

```json
{
  "mcpServers": {
    "gemini-cli-bridge": {
      "command": "uvx",
      "args": ["--from", ".", "gemini-cli-bridge"],
      "env": {"NO_COLOR": "1"}
    }
  }
}
```

可选优化：若你的客户端运行目录与仓库不同，可把 `--from "."` 改为仓库绝对路径；或在 `args` 中添加 `"--python", "/path/to/python"` 指向特定 Python。

## 常见问题与排查（PATH、认证、Sandbox）

### 1) PATH 问题

- 症状：`RuntimeError: command exit ...` 或提示找不到 `gemini`。
- 快速检查：

```zsh
which gemini
gemini --version
echo $PATH
```

- 修复思路：
  - 将 Homebrew 路径加入 PATH（Apple Silicon 通常为 `/opt/homebrew/bin`）：

```zsh
echo 'export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

- 或在 MCP 配置中为服务器设置 PATH（推荐最小化影响范围）：

```json
{
  "mcpServers": {
    "gemini-cli-bridge": {
      "command": "python3",
      "args": ["/absolute/path/to/gemini_cli_bridge.py"],
      "env": {"PATH": "/opt/homebrew/bin:/usr/local/bin:$PATH", "NO_COLOR": "1"}
    }
  }
}
```

### 2) 认证问题

- 症状：stderr 中出现未认证、401、提示登录等。
- 方案 A：OAuth 登录（个人或 Code Assist）

```zsh
gemini  # 按提示走浏览器登录
```

- 方案 B：API Key / Vertex

```zsh
# Gemini API Key（aistudio.google.com/apikey）
export GEMINI_API_KEY="YOUR_API_KEY"

# Vertex（示例，需按文档配置项目/位置/凭据）
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
```

- 验证：

```zsh
gemini --version
gemini -m gemini-2.5-pro -p "hello"
```

### 3) Sandbox 问题

- 症状：在 IDE/客户端内工具失败，而在本机终端可用；提示网络/权限受限。
- 要点：
  - 某些客户端会在沙箱/Docker 中运行工具；需确保沙箱内也安装并可调用 `gemini`，且网络策略允许访问。
  - 在 Gemini CLI 中使用 `--sandbox` 或设置 `GEMINI_SANDBOX` 时同理，需要镜像或环境内具备依赖。
  - 使用 YOLO（`--approval-mode yolo`/`--yolo`）时默认会开启沙箱配置，确保 Docker 可用。

- 建议：
  - 若需自定义沙箱镜像，请基于官方 `gemini-cli-sandbox` 构建，并在镜像内安装 `gemini` 与所需可执行文件。
  - 开发阶段可临时禁用沙箱验证问题，生产再启用。

### 4) 代理与超时

- 可通过工具参数 `timeout_s` 增大超时。
- 透传 CLI 代理：使用 `extra_args` 的等号形式避免参数值被丢弃，例如：

```json
{
  "name": "gemini_prompt_plus",
  "arguments": {
    "prompt": "test proxy",
    "extra_args": ["--proxy=http://127.0.0.1:7890"]
  }
}
```

说明：当 CLI flag 需要跟随一个独立值（如 `--proxy http://...`）时，建议使用 `--key=value` 形式传递，避免值不以 `-` 开头而被忽略。

## 命令参考速查（常用 flags 对照表）

本桥接将常用 CLI flags 映射为 MCP 工具参数；未覆盖的 flags 可通过 `extra_args` 透传。

- 模型选择：`-m, --model <name>` → 参数 `model`
- 非交互提示：`-p, --prompt <text>` → 参数 `prompt`
- 多目录上下文：`--include-directories <d1,d2,...>` → 参数 `include_dirs[]`
- 审批策略：`--approval-mode <default|auto_edit|yolo>` → 参数 `approval_mode`
- YOLO 自动批准：`--yolo` → 参数 `yolo: true`（或用 `approval_mode: "yolo"`）
- 检查点：`--checkpointing` → 参数 `checkpointing: true`
- 版本：`--version` → 工具 `gemini_version`
- 列扩展：`--list-extensions` → 工具 `gemini_extensions_list`
- MCP 管理：`gemini mcp list/add/remove` → 工具 `gemini_mcp_list / gemini_mcp_add / gemini_mcp_remove`
- 调试输出：`-d, --debug` → 通过 `extra_args: ["--debug"]`
- 代理：`--proxy <url>` → 通过 `extra_args: ["--proxy=http://127.0.0.1:7890"]`
- 全量文件上下文：`-a, --all-files` → 通过 `extra_args: ["--all-files"]`
- 沙箱：`-s, --sandbox` 与 `--sandbox-image` → 通过 `extra_args` 传入（或在 settings 中配置）

示例（传递代理与调试）：

```json
{
  "name": "gemini_prompt_plus",
  "arguments": {
    "prompt": "hello",
    "extra_args": ["--debug", "--proxy=http://127.0.0.1:7890"]
  }
}
```
