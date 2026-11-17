// sdlc-manager-managed
import { Plugin } from "@opencode/plugin"

const eventId = (input: Record<string, unknown>) =>
  typeof input.event_id === "string" ? input.event_id : undefined

async function processEvent(directory: string, input: Record<string, unknown>) {
  const child = Bun.spawn(["uv", "--directory", "__SDLC_MANAGER_ROOT__", "run", "--frozen", "sdlc-manager", "event", "process", "--stdin"], {
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

export default Plugin.define({
  id: "sdlc-manager",
  async setup(ctx) {
    await ctx.tool.hook("execute.after", async (event) => {
      if (event.status !== "completed") return
      const toolInput = (event.input ?? {}) as Record<string, unknown>
      const path = typeof toolInput.filePath === "string"
        ? toolInput.filePath
        : typeof toolInput.file_path === "string" ? toolInput.file_path : undefined
      if (!path) return
      const normalized = {
        event_id: eventId(toolInput),
      event_type: "file_changed",
      source_client: "opencode",
      project_id: process.env.SDLC_MANAGER_PROJECT_ID,
      timestamp: new Date().toISOString(),
        affected_files: [path],
      context: {},
      schema_version: "1.0",
    }
      const result = await processEvent(ctx.location.directory, normalized)
      event.result = {
        ...event.result,
        metadata: { ...event.result.metadata, sdlcManager: result },
      }
    })
  },
})
