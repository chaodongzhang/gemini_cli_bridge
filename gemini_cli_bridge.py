#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import re
import json
import time
import signal
import contextlib
import urllib.request
import urllib.error
import socket
import ipaddress
from urllib.parse import urlparse, urlencode
from pathlib import Path
from typing import List, Optional, Dict

from fastmcp import FastMCP  # 若你改用官方 SDK，则用: from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini-cli-bridge")

# 统一输出截断上限（可通过环境覆盖）
MAX_OUT = int(os.getenv("MCP_MAX_OUTPUT", "20000"))

@mcp.tool()  # 关键改动：必须带括号
def gemini_prompt(
    prompt: str,
    model: str = "gemini-2.5-pro",
    include_dirs: Optional[List[str]] = None,
    timeout_s: int = 120,
    extra_args: Optional[List[str]] = None,
) -> str:
    """调用本地 `gemini` CLI 的非交互接口，返回标准输出文本。"""
    cmd = ["gemini", "-m", model, "-p", prompt]
    if include_dirs:
        cmd += ["--include-directories", ",".join(include_dirs)]
    if extra_args:
        for a in extra_args:
            if isinstance(a, str) and a.startswith("-"):
                cmd.append(a)
    res = _run(cmd, timeout_s=timeout_s)
    return str(res["stdout"]).strip()


# --- 工具封装与辅助函数 -------------------------------------------------------
def _env_with_path(extra_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = os.environ.copy()
    # 关闭颜色，便于上游（MCP 客户端）解析
    env["NO_COLOR"] = "1"
    env["PATH"] = env.get("PATH", "") + ":/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
    if extra_env:
        for k, v in extra_env.items():
            if not (isinstance(k, str) and isinstance(v, str)):
                continue
            if k.upper() == "PATH":
                # 安全：不允许外部覆盖 PATH
                continue
            env[k] = v
    return env


def _run(cmd: List[str], timeout_s: int = 120, *, env: Optional[Dict[str, str]] = None, cwd: Optional[str] = None) -> Dict[str, object]:
    """
    以结构化结果执行子进程命令。
    返回: {"cmd": [...], "exit_code": int, "stdout": str, "stderr": str}
    失败时抛出 RuntimeError，包含 stderr 或退出码。
    """
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=_env_with_path(env),
        cwd=cwd,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"command exit {proc.returncode}: {' '.join(cmd)}")
    return {
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _at_ref(path: str) -> str:
    """将路径安全地转为 @引用，避免空格/引号导致的断裂。"""
    raw = path[1:] if isinstance(path, str) and path.startswith("@") else str(path)
    safe = raw.replace('"', '\\"')
    return f'@"{safe}"'


def _is_private_url(url: str) -> bool:
    """粗略判断 URL 是否解析到内网/回环/链路本地地址，防止 SSRF。"""
    try:
        u = urlparse(url)
        if u.scheme not in {"http", "https"}:
            return True
        host = u.hostname or ""
        # 明确回环/本地域名
        if host in {"localhost"}:
            return True
        # 解析所有地址
        for fam, _, _, _, sockaddr in socket.getaddrinfo(host, None):
            ip = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast:
                return True
        return False
    except Exception:
        # 无法解析的 URL 一律视为不安全
        return True


@mcp.tool()
def gemini_version(timeout_s: int = 60) -> str:
    """返回本机已安装的 gemini CLI 版本字符串（等同于: gemini --version）。"""
    res = _run(["gemini", "--version"], timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_mcp_list(scope: Optional[str] = None, timeout_s: int = 120) -> str:
    """列出 gemini CLI 中已配置的 MCP 服务器（等同: gemini mcp list）。scope 可选: user|project。"""
    cmd = ["gemini", "mcp", "list"]
    if scope in {"user", "project"}:
        cmd += ["--scope", scope]
    res = _run(cmd, timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_mcp_add(
    name: str,
    command_or_url: str,
    transport: str = "stdio",  # stdio|http|sse
    args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    scope: str = "project",  # user|project
    timeout_ms: Optional[int] = None,
    trust: bool = False,
    description: Optional[str] = None,
    include_tools: Optional[List[str]] = None,
    exclude_tools: Optional[List[str]] = None,
    timeout_s: int = 120,
) -> str:
    """
    通过 gemini CLI 新增 MCP 服务器（等同: gemini mcp add ...）。
    - transport: stdio | http | sse
    - 对于 stdio: command_or_url 传可执行命令；对于 http/sse: 传 URL。
    - headers 仅在 http/sse 有效。
    返回 CLI 标准输出。
    """
    cmd = ["gemini", "mcp", "add", name]

    # 传输类型
    if transport in {"http", "sse"}:
        cmd += ["--transport", transport, command_or_url]
    else:
        # 默认 stdio
        cmd += [command_or_url]
        if args:
            cmd += args

    # 作用域
    if scope in {"user", "project"}:
        cmd += ["--scope", scope]

    # 环境变量（多个 -e KEY=VAL）
    if env_vars:
        for k, v in env_vars.items():
            if k and v is not None:
                cmd += ["-e", f"{k}={v}"]

    # HTTP 头（多个 -H "K: V"）
    if headers and transport in {"http", "sse"}:
        for hk, hv in headers.items():
            cmd += ["-H", f"{hk}: {hv}"]

    if timeout_ms is not None and isinstance(timeout_ms, int) and timeout_ms > 0:
        cmd += ["--timeout", str(timeout_ms)]
    if trust:
        cmd += ["--trust"]
    if description:
        cmd += ["--description", description]
    if include_tools:
        cmd += ["--include-tools", ",".join(include_tools)]
    if exclude_tools:
        cmd += ["--exclude-tools", ",".join(exclude_tools)]

    res = _run(cmd, timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_mcp_remove(name: str, scope: str = "project", timeout_s: int = 120) -> str:
    """删除 gemini CLI 配置的 MCP 服务器（等同: gemini mcp remove <name>）。"""
    cmd = ["gemini", "mcp", "remove", name]
    if scope in {"user", "project"}:
        cmd += ["--scope", scope]
    res = _run(cmd, timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_web_fetch(
    prompt: str,
    urls: List[str],
    model: str = "gemini-2.5-pro",
    include_dirs: Optional[List[str]] = None,
    approval_mode: Optional[str] = None,  # default|auto_edit|yolo
    yolo: bool = False,
    checkpointing: bool = False,
    extra_args: Optional[List[str]] = None,
    timeout_s: int = 180,
) -> str:
    """
    便捷包装：强制在提示中注入 URL 列表，触发 CLI 的 web_fetch 能力。
    说明：web_fetch 是 CLI 的内置工具，模型会基于包含的 URL 决定是否调用。
    """
    urls = [u for u in (urls or []) if isinstance(u, str) and (u.startswith("http://") or u.startswith("https://"))]
    if not urls:
        raise ValueError("urls 至少需要一个 http(s) 链接")

    composed = f"{prompt.strip()}\n\n" + "\n".join(urls)
    cmd = ["gemini", "-m", model, "-p", composed]
    if include_dirs:
        cmd += ["--include-directories", ",".join(include_dirs)]
    if checkpointing:
        cmd += ["--checkpointing"]
    if approval_mode in {"default", "auto_edit", "yolo"}:
        cmd += ["--approval-mode", approval_mode]
    elif yolo:
        cmd += ["--yolo"]
    if extra_args:
        for a in extra_args:
            if isinstance(a, str) and a.startswith("-"):
                cmd.append(a)

    res = _run(cmd, timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_extensions_list(timeout_s: int = 60) -> str:
    """列出本机可用的 Gemini CLI 扩展（等同: gemini --list-extensions）。"""
    res = _run(["gemini", "--list-extensions"], timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_prompt_plus(
    prompt: str,
    model: str = "gemini-2.5-pro",
    include_dirs: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    approval_mode: Optional[str] = None,  # default|auto_edit|yolo
    yolo: bool = False,
    checkpointing: bool = False,
    extra_args: Optional[List[str]] = None,
    timeout_s: int = 180,
) -> str:
    """
    高级非交互执行：支持 @附件、审批策略、检查点、目录上下文与额外 flags。
    - attachments: 传绝对或相对路径，自动转换为 @path 插入到 prompt 文本尾部。
    - approval_mode: default|auto_edit|yolo；若未设置且 yolo=True，则使用 --yolo。
    """
    final_prompt = prompt or ""
    if attachments:
        at_refs = " ".join(_at_ref(p) for p in attachments)
        if at_refs:
            final_prompt = (final_prompt.rstrip() + "\n\n" + at_refs).strip()

    cmd = ["gemini", "-m", model]
    if include_dirs:
        cmd += ["--include-directories", ",".join(include_dirs)]
    if checkpointing:
        cmd += ["--checkpointing"]
    if approval_mode in {"default", "auto_edit", "yolo"}:
        cmd += ["--approval-mode", approval_mode]
    elif yolo:
        cmd += ["--yolo"]

    cmd += ["-p", final_prompt]
    if extra_args:
        for a in extra_args:
            if isinstance(a, str) and a.startswith("-"):
                cmd.append(a)

    res = _run(cmd, timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_search(
    query: str,
    model: str = "gemini-2.5-pro",
    include_dirs: Optional[List[str]] = None,
    approval_mode: Optional[str] = None,
    yolo: bool = False,
    checkpointing: bool = False,
    extra_args: Optional[List[str]] = None,
    timeout_s: int = 180,
) -> str:
    """
    轻量搜索包装：提示模型使用内置 web_search 工具搜索并给出带引用的答案。
    注意：是否调用 web_search 由模型决定，此函数通过提示工程来鼓励调用该工具。
    """
    guidance = (
        "Please use the built-in web_search tool to find up-to-date, authoritative sources, "
        "then synthesize an answer with citations. Prioritize primary sources and include URLs.\n\n"
    )
    final_prompt = guidance + f"Search task: {query.strip()}"

    cmd = ["gemini", "-m", model]
    if include_dirs:
        cmd += ["--include-directories", ",".join(include_dirs)]
    if checkpointing:
        cmd += ["--checkpointing"]
    if approval_mode in {"default", "auto_edit", "yolo"}:
        cmd += ["--approval-mode", approval_mode]
    elif yolo:
        cmd += ["--yolo"]
    cmd += ["-p", final_prompt]
    if extra_args:
        for a in extra_args:
            if isinstance(a, str) and a.startswith("-"):
                cmd.append(a)
    res = _run(cmd, timeout_s=timeout_s)
    return res["stdout"].strip()


@mcp.tool()
def gemini_prompt_with_memory(
    prompt: str,
    memory_paths: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    model: str = "gemini-2.5-pro",
    include_dirs: Optional[List[str]] = None,
    approval_mode: Optional[str] = None,
    yolo: bool = False,
    checkpointing: bool = False,
    extra_args: Optional[List[str]] = None,
    timeout_s: int = 180,
) -> str:
    """
    将指定 memory_paths 作为高优先级上下文注入，再执行非交互推理；可选附件同样以 @path 注入。
    - memory_paths: 作为“系统/项目记忆”优先注入，适合传递 GEMINI.md 或标准作业/规范等。
    - attachments: 额外文件/目录内容注入。
    """
    blocks: List[str] = []
    if memory_paths:
        at_mem = "\n".join(_at_ref(p) for p in memory_paths)
        if at_mem:
            blocks.append(
                "[HIGH-PRIORITY CONTEXT]\n"
                "Use the following project memory and conventions as authoritative context.\n\n"
                + at_mem
            )
    if prompt:
        blocks.append(prompt.strip())
    if attachments:
        at_refs = "\n".join(_at_ref(p) for p in attachments)
        if at_refs:
            blocks.append(at_refs)
    final_prompt = "\n\n".join(blocks).strip()

    cmd = ["gemini", "-m", model]
    if include_dirs:
        cmd += ["--include-directories", ",".join(include_dirs)]
    if checkpointing:
        cmd += ["--checkpointing"]
    if approval_mode in {"default", "auto_edit", "yolo"}:
        cmd += ["--approval-mode", approval_mode]
    elif yolo:
        cmd += ["--yolo"]
    cmd += ["-p", final_prompt]
    if extra_args:
        for a in extra_args:
            if isinstance(a, str) and a.startswith("-"):
                cmd.append(a)
    res = _run(cmd, timeout_s=timeout_s)
    return res["stdout"].strip()


# --- 通用系统/网络工具（按需求定制的集合） ------------------------------------

@mcp.tool()
def Shell(cmd: str, cwd: Optional[str] = None, timeout_s: int = 120) -> str:
    """执行 shell 命令并返回 JSON：{code, stdout, stderr}；默认禁用，设置 MCP_BASH_ALLOW=1 启用。"""
    if os.getenv("MCP_BASH_ALLOW", "0") != "1":
        return json.dumps({"code": 126, "stdout": "", "stderr": "Shell disabled (set MCP_BASH_ALLOW=1)"}, ensure_ascii=False)
    try:
        completed = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            env=_env_with_path({}),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        if len(stdout) > MAX_OUT:
            stdout = stdout[:MAX_OUT] + "\n...[truncated]..."
        if len(stderr) > MAX_OUT:
            stderr = stderr[:MAX_OUT] + "\n...[truncated]..."
        return json.dumps({"code": completed.returncode, "stdout": stdout, "stderr": stderr}, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"code": 124, "stdout": "", "stderr": f"timeout after {timeout_s}s"}, ensure_ascii=False)


@mcp.tool()
def FindFiles(pattern: str = "*", base: str = ".", recursive: bool = True) -> str:
    """查找文件：返回 JSON 数组路径列表。支持递归匹配。"""
    base_path = Path(base).expanduser().resolve()
    try:
        if recursive and "**" not in pattern:
            pattern = f"**/{pattern}"
        matches = [str(p) for p in base_path.glob(pattern) if p.exists()]
        return json.dumps(matches, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def ReadFile(path: str) -> str:
    """读取文本文件（utf-8，忽略非法字符）。失败抛异常。"""
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(str(p))
    return p.read_text(encoding="utf-8", errors="ignore")


@mcp.tool()
def ReadFolder(path: str = ".", recursive: bool = False, max_entries: int = 2000) -> str:
    """读取目录：返回 JSON 路径数组；递归可选。"""
    root = Path(path).expanduser().resolve()
    items: List[str] = []
    try:
        if recursive:
            for dirpath, dirnames, filenames in os.walk(root):
                for d in dirnames:
                    items.append(str(Path(dirpath, d)) + "/")
                for f in filenames:
                    items.append(str(Path(dirpath, f)))
                if len(items) >= max_entries:
                    break
        else:
            for child in sorted(root.iterdir()):
                items.append(str(child) + ("/" if child.is_dir() else ""))
        return json.dumps(items[:max_entries], ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def ReadManyFiles(paths: List[str], ignore_missing: bool = True) -> str:
    """批量读取多个文件：返回 JSON 对象 {path: content}。"""
    result: Dict[str, str] = {}
    for p0 in paths or []:
        p = Path(str(p0)).expanduser().resolve()
        if not p.exists() or not p.is_file():
            if ignore_missing:
                continue
            raise FileNotFoundError(str(p))
        try:
            result[str(p)] = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            result[str(p)] = f"<error: {e}>"
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def SaveMemory(path: str, content: str, mode: str = "append") -> str:
    """保存记忆：将内容写入指定路径；mode=append|overwrite；返回 JSON {ok, bytes}."""
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    data = content or ""
    try:
        if mode == "overwrite":
            p.write_text(data, encoding="utf-8")
        else:
            with p.open("a", encoding="utf-8") as f:
                f.write(data)
        return json.dumps({"ok": True, "bytes": len(data)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
def SearchText(pattern: str, path: str, case_insensitive: bool = False) -> str:
    """在单个文件中搜索文本，返回 JSON 数组 [{line, text}]。"""
    p = Path(path).expanduser().resolve()
    results: List[Dict[str, object]] = []
    if not p.exists() or not p.is_file():
        return json.dumps(results, ensure_ascii=False)
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        flags = re.MULTILINE | (re.IGNORECASE if case_insensitive else 0)
        for i, line in enumerate(text.splitlines(), start=1):
            if re.search(pattern, line, flags=flags):
                results.append({"line": i, "text": line})
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def WriteFile(path: str, content: str) -> str:
    """写入文本文件（utf-8），必要时创建父目录。返回 ok。"""
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return "ok"


@mcp.tool()
def Edit(path: str, find: str, replace: str, count: int = 0) -> str:
    """进行字符串替换，count=0 表示替换全部。返回 JSON：{"replaced": n}。"""
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(str(p))
    s = p.read_text(encoding="utf-8", errors="ignore")
    if count == 0:
        replaced = s.count(find)
        s2 = s.replace(find, replace)
    else:
        replaced = min(s.count(find), max(count, 0))
        s2 = s.replace(find, replace, replaced)
    p.write_text(s2, encoding="utf-8")
    return json.dumps({"replaced": replaced}, ensure_ascii=False)


# 以上工具集合对应：Edit（已保留）、FindFiles、GoogleSearch（见下）、ReadFile、ReadFolder、ReadManyFiles、SaveMemory、SearchText、Shell、WebFetch、WriteFile。


@mcp.tool()
def WebFetch(url: str, timeout_s: int = 15) -> str:
    """最小网页抓取：优先 requests，其次 urllib；返回 JSON {ok,status,content?,error?}。"""
    data: Dict[str, object] = {"url": url, "ok": False, "status": None, "content": None, "error": None}
    # SSRF 粗略防护
    if _is_private_url(url):
        data["error"] = "Blocked private/loopback URL"
        return json.dumps(data, ensure_ascii=False)
    headers = {"User-Agent": "gemini-cli-bridge/1.0"}
    try:
        try:
            import requests  # 可选依赖
            r = requests.get(url, headers=headers, timeout=timeout_s)
            content = r.text
            if len(content) > MAX_OUT:
                content = content[:MAX_OUT] + "\n...[truncated]..."
            data.update({"ok": bool(r.ok), "status": r.status_code, "content": content})
        except Exception:
            req = urllib.request.Request(url, headers=headers)
            with contextlib.closing(urllib.request.urlopen(req, timeout=timeout_s)) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                body = resp.read().decode(charset, errors="ignore")
                if len(body) > MAX_OUT:
                    body = body[:MAX_OUT] + "\n...[truncated]..."
                data.update({"ok": True, "status": getattr(resp, "status", 200), "content": body})
    except Exception as e:
        data["error"] = str(e)
    return json.dumps(data, ensure_ascii=False)


@mcp.tool()
def GoogleSearch(query: str, limit: int = 5, cse_id: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """使用 Google Programmable Search (Custom Search JSON API)。
    需要环境变量 GOOGLE_CSE_ID 与 GOOGLE_API_KEY，或通过参数传入。
    返回 JSON：{ok, results: [{title, link, snippet}], error?}
    """
    cse = cse_id or os.getenv("GOOGLE_CSE_ID")
    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not cse or not key:
        return json.dumps({
            "ok": False,
            "results": [],
            "hint": "Set GOOGLE_CSE_ID and GOOGLE_API_KEY or pass cse_id/api_key",
        }, ensure_ascii=False)
    try:
        params = {
            "key": key,
            "cx": cse,
            "q": query,
            "num": max(1, min(int(limit or 5), 10)),  # API 单次最多 10
        }
        url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
        headers = {"User-Agent": "gemini-cli-bridge/1.0"}
        req = urllib.request.Request(url, headers=headers)
        with contextlib.closing(urllib.request.urlopen(req, timeout=15)) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset, errors="ignore")
        data = json.loads(raw or "{}")
        items = data.get("items", []) or []
        results = []
        for it in items:
            results.append({
                "title": it.get("title"),
                "link": it.get("link"),
                "snippet": it.get("snippet"),
            })
        return json.dumps({"ok": True, "results": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "results": [], "error": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()  # 默认 STDIO 传输

# 供 console_script 使用
def main() -> None:
    """Entry point for uvx/pipx console_script."""
    mcp.run()
