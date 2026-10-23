# GitHub publication checklist / 发布清单

The project archive is a **local source distribution**, not a published GitHub repository. Publishing is a separate, explicit maintainer action.

1. Choose an available repository name, e.g. `codex-triad`; check GitHub search and trademarks. Decide owner and repository URL.
2. Set the actual maintainer name and contact method. Setup documentation uses local source paths until a real repository URL exists. Review `SECURITY.md` so vulnerability reports reach a private channel; enable GitHub private vulnerability reporting if available.
3. Inspect `git status` and make sure there are no local API keys, `.env`, transcripts, private datasets, auth files, billing details or proxy configurations. Check `git diff --cached` before every push.
4. Run `python -m pip install -e .`, `python -m unittest discover -s tests -v`, `python -m compileall -q src tests tools`, `python tools/build_release.py` and `python tools/check_wheel.py`. Inspect the source ZIP and SHA256SUMS. Build tools must already be installed for offline builds.
5. Perform a **real local Codex smoke test** in a trusted *throwaway* repo using all three models. Record the Codex version, actual effective model selection and any provider/routing errors without including secrets.
6. Enable GitHub Actions and verify Windows/Linux CI passes. Create GitHub issue labels and a `good first issue` task. Review the license and attribution.
7. Keep `v0.2.0a1` a pre-release until 3-model runtime verification and a complete uninstall/upgrade walkthrough are documented. Avoid claiming guaranteed autonomous gating or cost savings.
8. Once verified, publish a release tag and a short, reproducible announcement with explicit limitations, screenshots, and benchmark raw data.

## Optional local Git steps (do not run blindly on user projects)

```bash
cd codex-triad
git init
git add .
git diff --cached --stat
git commit -m "feat: initial Codex Triad alpha"
# Create GitHub repository yourself, then set its remote and push.
```

License: MIT. This repository is community-maintained and is not endorsed by OpenAI.

当前发布阻塞：名称/商标及包名可用性未审定，维护者私密联系方式未配置，远端 CI 未运行，真实三模型烟测/费用/截图未取得。它们不会阻碍本地源码交付，但不应伪称发布准备全部完成。本次没有运行上面的 Git 命令，也没有创建公开仓库、push、部署或 Release。
