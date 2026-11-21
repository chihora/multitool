import type { Plugin } from "@opencode-ai/plugin"

export const GuardPlugin: Plugin = async ({ $, worktree }) => ({
  "tool.execute.before": async (input, output) => {
    const payload = JSON.stringify({ tool: input.tool, args: output.args })
    const result = await $`echo ${payload} | uv run python guard/guard.py`
      .cwd(worktree)
      .quiet()
      .nothrow()

    if (result.exitCode !== 0) {
      throw new Error(result.text().trim())
    }
  },
})
