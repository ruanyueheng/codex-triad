"""Discover client-visible models and let users assign them to three responsibilities."""
from dataclasses import replace
import os
from pathlib import Path
import re
import shutil
import tempfile
import urllib.request

from .appserver import Client
from .templates import EFFORTS, Settings


class ModelSelectionError(ValueError):
    pass


ROLE_FAMILIES = {"main": "sol", "advisor": "astra", "worker": "luna"}


def latest_model(catalog: list[dict], family: str) -> dict | None:
    """Rank stable family IDs by numeric version, then rolling alias or snapshot."""
    candidates = []
    pattern = r"(?:[^/]+/)*gpt-([0-9]+(?:\.[0-9]+)*)-" + re.escape(family) + r"(?:-(latest|[0-9]{4}-[0-9]{2}-[0-9]{2}))?"
    for model in catalog:
        match = re.fullmatch(pattern, model["model"])
        if match:
            version = tuple(int(part) for part in match[1].split("."))
            suffix = match[2]
            alias = 2 if suffix == "latest" else 1 if suffix is None else 0
            candidates.append(((version, alias, suffix or "", model["is_default"], model["model"]), model))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def visible_models(entries: list) -> list[dict]:
    result = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ModelSelectionError("Invalid model catalog entry")
        if entry.get("hidden", False):
            continue
        model = entry.get("model")
        efforts = entry.get("supportedReasoningEfforts")
        if not isinstance(model, str) or not model or model in seen:
            raise ModelSelectionError("Invalid or duplicate model ID")
        if not isinstance(efforts, list) or not efforts:
            raise ModelSelectionError(f"Client did not report reasoning options for {model}; use explicit flags instead")
        options = [e.get("reasoningEffort") if isinstance(e, dict) else None for e in efforts]
        if any(e not in EFFORTS for e in options) or entry.get("defaultReasoningEffort") not in options:
            raise ModelSelectionError(f"Unsupported reasoning metadata for {model}")
        seen.add(model)
        result.append({"model": model, "efforts": list(dict.fromkeys(options)),
                       "default_effort": entry["defaultReasoningEffort"], "is_default": entry.get("isDefault") is True})
    if not result:
        raise ModelSelectionError("The client reported no visible models; nothing was installed")
    return result


def discover_models(project: Path, *, codex_home: Path | None = None, system_proxy: bool = False) -> list[dict]:
    executable = shutil.which("codex")
    if not executable:
        raise ModelSelectionError("Codex CLI not found; use explicit model flags or install a supported client")
    environment = os.environ.copy()
    if codex_home is not None:
        environment["CODEX_HOME"] = str(codex_home.resolve(strict=True))
    if system_proxy:
        for scheme, value in urllib.request.getproxies().items():
            if scheme in ("http", "https"):
                environment[scheme.upper() + "_PROXY"] = value
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
        client = Client(executable, project, environment, stderr)
        try:
            client.call("initialize", {"clientInfo": {"name": "codex-triad-model-picker", "version": "1"}})
            client.send({"method": "initialized", "params": {}})
            entries = []
            cursor = None
            seen_cursors = set()
            while True:
                params = {"limit": 100, "includeHidden": False}
                if cursor is not None:
                    params["cursor"] = cursor
                page = client.call("model/list", params)
                if not isinstance(page, dict) or not isinstance(page.get("data"), list):
                    raise ModelSelectionError("Invalid model/list response")
                entries.extend(page["data"])
                cursor = page.get("nextCursor")
                if cursor is None:
                    return visible_models(entries)
                if not isinstance(cursor, str) or not cursor or cursor in seen_cursors:
                    raise ModelSelectionError("Invalid/repeated model catalog cursor")
                seen_cursors.add(cursor)
        except (RuntimeError, TimeoutError) as exc:
            stderr.flush()
            stderr.seek(0)
            detail = stderr.read(2000).strip()
            raise ModelSelectionError(f"Could not query client model catalog: {exc}. {detail}") from exc
        finally:
            client.close()


def choose_settings(catalog: list[dict], initial: Settings, *, ask=input, show=print) -> Settings:
    show("当前客户端报告的模型（列表不等于实际调用权限证明；同一模型可用于多个职责）：")
    for index, model in enumerate(catalog, 1):
        show(f"  {index}. {model['model']}  强度: {', '.join(model['efforts'])}")
    result = initial
    fallback = next((m for m in catalog if m["is_default"]), catalog[0])
    for role, title in (("main", "主协调 / 实现"), ("worker", "工作者 / 探索"), ("advisor", "顾问 / 审查")):
        current = next((m for m in catalog if m["model"] == getattr(initial, role + "_model")), fallback)
        while True:
            value = ask(f"{title} 选择编号或模型ID [回车 {current['model']}]: ").strip()
            selected = next((m for i, m in enumerate(catalog, 1) if value in (str(i), m["model"])), None) if value else current
            if selected:
                break
            show("请输入上面列表中的编号或完整模型ID。")
        default = getattr(initial, role + "_effort") if selected["model"] == getattr(initial, role + "_model") else selected["default_effort"]
        if default not in selected["efforts"]:
            default = selected["default_effort"]
        while True:
            effort = ask(f"{title} 推理强度 {selected['efforts']} [回车 {default}]: ").strip() or default
            if effort in selected["efforts"]:
                break
            show("该模型没有报告支持这个强度，请从列出的选项选择。")
        result = replace(result, **{role + "_model": selected["model"], role + "_effort": effort})
    show(f"分配：主协调={result.main_model}/{result.main_effort}；工作者={result.worker_model}/{result.worker_effort}；顾问={result.advisor_model}/{result.advisor_effort}")
    return result
