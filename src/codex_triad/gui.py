"""Local task launcher. Tk is loaded only when the graphical entry point is used."""
import os
from pathlib import Path
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog

from .workflow import WorkflowError, project_models, task_command, task_prompt
from .storage import InstallationError

BG, PANEL, INK, MUTED, LINE, BLUE = "#f4f6fa", "#ffffff", "#172033", "#667085", "#e2e7ef", "#315efb"
MODE_CARDS = {
    "auto": ("自动协作", "按任务选择合适的分工", "先理解任务，再决定直接处理或安排协作。"),
    "quick": ("快速处理", "主协调直接完成", "由主协调直接推进，减少委派和等待。"),
    "team": ("多人协作", "并行调查 · 实现 · 审查", "工作者调查独立问题，主协调实现，顾问审查重要改动。"),
    "review": ("只做审查", "查找问题，不修改文件", "检查你指定的改动或代码，给出具体问题与建议。"),
}


class TaskWindow:
    def __init__(self, root: tk.Tk, project: Path):
        self.root, self.process = root, None
        root.title("Codex Triad · 任务工作台")
        root.geometry("1100x780")
        root.minsize(950, 740)
        root.configure(bg=BG)
        self.project = tk.StringVar(value=str(project.resolve()))
        self.mode = tk.StringVar(value="auto")
        self.status = tk.StringVar(value="准备好了。写下任务，选择你希望的协作方式。")
        self.model_vars = {role: tk.StringVar() for role in ("main", "worker", "advisor")}
        self.cards = {}

        sidebar = tk.Frame(root, bg="#142036", width=238)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="●  ●  ●", bg="#142036", fg="#8ba9ff", font=("Segoe UI", 17)).pack(anchor="w", padx=25, pady=(29, 5))
        tk.Label(sidebar, text="TRIAD", bg="#142036", fg="white", font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=25)
        tk.Label(sidebar, text="把想法交给团队", bg="#142036", fg="#b7c5dd", font=("Microsoft YaHei UI", 10)).pack(anchor="w", padx=26, pady=(8, 34))
        tk.Label(sidebar, text="  任务工作台", bg="#253b61", fg="white", anchor="w", padx=17, pady=13,
                 font=("Microsoft YaHei UI", 11, "bold")).pack(fill="x", padx=15)
        tk.Label(sidebar, text="项目模型", bg="#142036", fg="#92a6c5", font=("Microsoft YaHei UI", 9)).pack(anchor="w", padx=26, pady=(35, 14))
        for role, label in (("main", "主协调"), ("worker", "工作者"), ("advisor", "顾问")):
            tk.Label(sidebar, text=label, bg="#142036", fg="#92a6c5", font=("Microsoft YaHei UI", 9)).pack(anchor="w", padx=26)
            tk.Label(sidebar, textvariable=self.model_vars[role], bg="#142036", fg="#ecf2ff", anchor="w", justify="left",
                     wraplength=185, font=("Segoe UI", 10)).pack(anchor="w", padx=26, pady=(4, 19))
        tk.Label(sidebar, text="沿用项目与 Codex 设置\n任务完成后，在 Codex 中继续对话。", bg="#142036", fg="#92a6c5",
                 justify="left", wraplength=186, font=("Microsoft YaHei UI", 9)).pack(side="bottom", anchor="w", padx=26, pady=28)

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=30, pady=26)
        tk.Label(body, text="开始新任务", bg=BG, fg=INK, font=("Microsoft YaHei UI", 21, "bold")).pack(anchor="w")
        tk.Label(body, text="告诉 Triad 你想得到什么结果，剩下的交给合适的分工。", bg=BG, fg=MUTED,
                 font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(8, 20))

        self.label(body, "项目目录")
        folder_row = tk.Frame(body, bg=BG)
        folder_row.pack(fill="x", pady=(8, 17))
        tk.Entry(folder_row, textvariable=self.project, relief="flat", bg=PANEL, fg=INK, font=("Segoe UI", 10),
                 highlightthickness=1, highlightbackground=LINE).pack(side="left", fill="x", expand=True, ipady=9)
        self.button(folder_row, "选择目录…", self.browse).pack(side="left", padx=(10, 0), ipady=5)

        self.label(body, "你想完成什么？")
        task_border = tk.Frame(body, bg=LINE, padx=1, pady=1)
        task_border.pack(fill="both", expand=True, pady=(8, 8))
        self.task = tk.Text(task_border, height=4, wrap="word", undo=True, bg=PANEL, fg=INK,
                            insertbackground=BLUE, relief="flat", padx=14, pady=12, font=("Microsoft YaHei UI", 11))
        self.task.pack(fill="both", expand=True)
        samples = tk.Frame(body, bg=BG)
        samples.pack(fill="x", pady=(0, 18))
        for text, task, mode in (
            ("修复问题", "修复：[描述遇到的问题]\n期望结果：[修复后应该怎样工作]", "auto"),
            ("开发功能", "实现：[描述想要的功能]\n使用场景：[谁会怎样使用它]\n完成标准：[你想看到的结果]", "team"),
            ("审查改动", "审查当前工作区的未提交改动，重点检查行为回归、错误处理和数据安全。只报告具体问题，不修改文件。", "review")):
            self.button(samples, text, lambda t=task, m=mode: self.use_sample(t, m)).pack(side="left", padx=(0, 9))

        self.label(body, "这次怎样协作？")
        cards = tk.Frame(body, bg=BG)
        cards.pack(fill="x", pady=(8, 7))
        for i, (mode, (title, subtitle, _)) in enumerate(MODE_CARDS.items()):
            card = tk.Radiobutton(cards, variable=self.mode, value=mode, text=f"{title}\n{subtitle}", indicatoron=False,
                                  command=self.select_mode, anchor="w", justify="left", padx=15, pady=12,
                                  relief="flat", borderwidth=0, highlightthickness=1, font=("Microsoft YaHei UI", 10),
                                  bg=PANEL, fg=INK, selectcolor="#eaf0ff", activebackground="#eaf0ff", cursor="hand2")
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=(0 if i % 2 == 0 else 6, 6 if i % 2 == 0 else 0), pady=5)
            self.cards[mode] = card
        cards.columnconfigure((0, 1), weight=1, uniform="mode")
        self.mode_hint = tk.StringVar()
        tk.Label(body, textvariable=self.mode_hint, bg=BG, fg=MUTED, anchor="w", justify="left",
                 wraplength=740, font=("Microsoft YaHei UI", 9)).pack(fill="x", pady=(0, 16))

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x")
        self.start_button = self.button(actions, "开始任务  ↗", self.launch, primary=True)
        self.start_button.pack(side="right", ipadx=16, ipady=7)
        self.button(actions, "复制到当前对话", self.copy).pack(side="left", ipady=7)
        self.button(actions, "预览指令", self.preview).pack(side="left", padx=9, ipady=7)
        tk.Label(body, textvariable=self.status, bg=BG, fg=MUTED, anchor="w", justify="left", wraplength=740,
                 font=("Microsoft YaHei UI", 9)).pack(fill="x", pady=(12, 0))
        self.project.trace_add("write", lambda *_: self.refresh_models())
        root.bind("<Control-Return>", lambda _: self.launch())
        self.select_mode()
        self.refresh_models()
        self.task.focus_set()

    def label(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=INK, font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")

    def button(self, parent, text, command, *, primary=False):
        return tk.Button(parent, text=text, command=command, bg=BLUE if primary else PANEL, fg="white" if primary else INK,
                         activebackground="#244bdf" if primary else "#eaf0ff", activeforeground="white" if primary else INK,
                         relief="flat", borderwidth=0, padx=12, pady=6, cursor="hand2", font=("Microsoft YaHei UI", 10))

    def browse(self):
        selected = filedialog.askdirectory(parent=self.root, title="选择项目目录", initialdir=self.project.get() or str(Path.cwd()))
        if selected:
            self.project.set(selected)

    def refresh_models(self):
        project = Path(self.project.get()).expanduser()
        try:
            if not project.is_dir():
                raise ValueError("目录不存在")
            models = project_models(project)
        except (InstallationError, OSError, ValueError):
            models = {role: "项目配置暂不可读" for role in self.model_vars}
        for role, value in models.items():
            self.model_vars[role].set(value)

    def select_mode(self):
        for mode, card in self.cards.items():
            card.configure(highlightbackground=BLUE if mode == self.mode.get() else LINE,
                           highlightcolor=BLUE if mode == self.mode.get() else LINE)
        self.mode_hint.set(MODE_CARDS[self.mode.get()][2])

    def use_sample(self, task, mode):
        if self.task.get("1.0", "end-1c").strip():
            self.status.set("先保留你已写的任务。清空输入框后可以填入模板。")
            return
        self.task.insert("1.0", task)
        self.mode.set(mode)
        self.select_mode()
        self.task.focus_set()

    def prompt(self):
        task = self.task.get("1.0", "end-1c").strip()
        if not task:
            raise WorkflowError("先写下你想完成的任务。")
        if any(part in task for part in ("[描述", "[修复后", "[谁会", "[你想")):
            raise WorkflowError("把模板中方括号里的提示替换为你的实际需求。")
        return task_prompt(task, self.mode.get(), project=Path(self.project.get()).expanduser())

    def copy(self):
        try:
            prompt = self.prompt()
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            self.status.set("已复制。粘贴到当前 Codex 对话即可开始，沿用本次协作方式。")
        except WorkflowError as exc:
            self.status.set(str(exc))

    def preview(self):
        try:
            prompt = self.prompt()
        except WorkflowError as exc:
            self.status.set(str(exc))
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Triad · 本次任务指令")
        dialog.geometry("820x620")
        text = tk.Text(dialog, wrap="word", bg=PANEL, fg=INK, padx=20, pady=18, font=("Segoe UI", 10))
        text.pack(fill="both", expand=True)
        text.insert("1.0", prompt)
        text.configure(state="disabled")

    def launch(self):
        if self.process is not None and self.process.poll() is None:
            self.status.set("Codex 会话已在运行。请在那个窗口继续，或复制另一项任务到当前对话。")
            return
        try:
            self.prompt()
            project = Path(self.project.get()).expanduser().resolve()
            command = task_command(project, self.task.get("1.0", "end-1c").strip(), self.mode.get())
            if os.name == "nt":
                self.process = subprocess.Popen(command, cwd=project, creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif shutil.which("x-terminal-emulator"):
                self.process = subprocess.Popen(["x-terminal-emulator", "-e", *command], cwd=project)
            else:
                raise WorkflowError("当前系统没有可用的终端启动器。请点击“复制到当前对话”，在 Codex 中继续。")
        except (OSError, ValueError) as exc:
            self.status.set(f"未启动：{exc}")
            return
        self.start_button.configure(state="disabled", text="Codex 会话运行中")
        self.status.set("已打开 Codex 任务窗口。实际执行可能消耗模型额度；请在该窗口查看进度并继续对话。")
        self.root.after(1000, self.check_session)

    def check_session(self):
        if self.process.poll() is None:
            self.root.after(1000, self.check_session)
            return
        code = self.process.returncode
        self.status.set("Codex 会话已关闭，可以开始下一项任务。" if code == 0 else f"Codex 已退出（状态 {code}）。请检查该窗口中的启动错误。")
        self.start_button.configure(state="normal", text="开始任务  ↗")


def main(project: Path | None = None):
    root = tk.Tk()
    TaskWindow(root, project or Path.cwd())
    root.mainloop()


if __name__ == "__main__":
    main()
