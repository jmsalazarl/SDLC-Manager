// sdlc-manager-managed
import { Plugin } from "@opencode/plugin"

const eventId = (input: Record<string, unknown>) =>
  typeof input.event_id === "string" ? input.event_id : undefined

async function processEvent(directory: string, input: Record<string, unknown>) {
  const child = Bun.spawn([...__SDLC_MANAGER_COMMAND_JSON__, "event", "process", "--stdin"], {
    cwd: directory,
    stdin: "pipe",
    stdout: "pipe",
    stderr: "pipe",
  })
  child.stdin.write(JSON.stringify(input))
  child.stdin.end()
  const output = await new Response(child.stdout).text()
  await child.exited
  try {
    return JSON.parse(output) as Record<string, unknown>
  } catch {
    return { status: "ERROR", error_code: "INVALID_CLI_OUTPUT", decision: null }
  }
}

function contextFromResult(result: Record<string, unknown>): string | undefined {
  const recommendations = Array.isArray(result.recommendations)
    ? result.recommendations.filter((item): item is string => typeof item === "string")
    : []
  const decision = result.decision
  const explanation = typeof result.explanation === "string" ? result.explanation : undefined
  if (recommendations.length === 0 && (decision === "WARN" || decision === "BLOCK") && explanation) {
    recommendations.push(explanation)
  }
  if (
    recommendations.length === 0
    && explanation
    && (result.status === "rejected" || result.status === "error")
  ) {
    recommendations.push(explanation)
  }
  if (recommendations.length === 0) return undefined
  const suffix = decision === "WARN" || decision === "BLOCK" ? `\nDecision: ${decision}.` : ""
  return `SDLC Manager:\n- ${recommendations.join("\n- ")}${suffix}`.slice(0, 10000)
}

export default Plugin.define({
  id: "sdlc-manager",
  async setup(ctx) {
    let pendingContext: string | undefined

    await ctx.session.hook("context", (event) => {
      if (!pendingContext) return
      event.system.push({ type: "text", text: pendingContext })
      pendingContext = undefined
    })

    const initial = await processEvent(ctx.location.directory, {
      event_type: "session_started",
      source_client: "opencode",
      project_root: ctx.location.directory,
      timestamp: new Date().toISOString(),
      context: {},
      schema_version: "1.0",
    })
    pendingContext = contextFromResult(initial)

    await ctx.tool.hook("execute.after", async (event) => {
      if (event.status !== "completed") return
      const toolInput = (event.input ?? {}) as Record<string, unknown>
      const path = typeof toolInput.filePath === "string"
        ? toolInput.filePath
        : typeof toolInput.file_path === "string"
          ? toolInput.file_path
          : typeof toolInput.path === "string" ? toolInput.path : undefined
      if (!path) return
      const normalized = {
        event_id: eventId(toolInput),
        event_type: "file_changed",
        source_client: "opencode",
        project_root: ctx.location.directory,
        path,
        timestamp: new Date().toISOString(),
        affected_files: [path],
        context: {},
        schema_version: "1.0",
      }
      const result = await processEvent(ctx.location.directory, normalized)
      pendingContext = contextFromResult(result)
      event.result = {
        ...event.result,
        metadata: { ...(event.result.metadata ?? {}), sdlcManager: result },
      }
    })
  },
})
