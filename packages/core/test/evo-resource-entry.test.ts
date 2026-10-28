/**
 * Given one user sentence and an installed Evo plugin, the native main Session
 * can read its actual Skill and prepare a new Workspace dataset through tools.
 * Missing authorization is returned without dispatching learning or test calls.
 * Scripted provider emissions verify the native entry wiring, not autonomous reasoning.
 */
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, expect, it, vi } from "vitest";
import {
  createAgent,
  installPlugin,
  readLibraryPackage,
  GenerativeModel,
  userText,
  toolCall,
  assistantText,
} from "../src/index.js";
import type { Session } from "../src/index.js";
import { seedProject } from "./seeded-project.js";
import { stubProviderKeys } from "./provider-keys.js";

let root: string, session: Session | undefined, restore: (() => void) | undefined;
afterEach(async () => {
  session?.dispose();
  restore?.();
  vi.restoreAllMocks();
  if (root) await fs.rm(root, { recursive: true, force: true });
});

it("runs the installed resource entry from one sentence and stops before unauthorized calls", async () => {
  root = await fs.mkdtemp(path.join(os.tmpdir(), "evo-native-entry-"));
  restore = stubProviderKeys();
  await seedProject(root);
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No network or paid model"));
  const agent = await createAgent({ root, agentId: "controller" });
  await installPlugin(
    root,
    "default_project",
    "controller",
    readLibraryPackage(
      path.resolve(import.meta.dirname, "../../../plugins/evo-harness-rsi-toolkit"),
    ),
  );
  const project = path.join(root, "default_project");
  for (const split of ["train", "test"]) {
    const dir = path.join(project, "benchmarks", "new-workspace-" + split);
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(
      path.join(dir, "benchmark_config.toml"),
      `id="new-workspace-${split}"\ntitle="New Workspace ${split}"\nstatus="published"\nversion="1"\n`,
    );
    for (const kind of ["statement", "rubric"]) {
      const part = path.join(dir, "CASE-local", kind);
      await fs.mkdir(part, { recursive: true });
      await fs.writeFile(
        path.join(part, "README.md"),
        kind === "statement" ? "Public input" : "PRIVATE_RUBRIC",
      );
    }
  }
  await fs.writeFile(
    path.join(project, "evo-experiment.json"),
    JSON.stringify({
      runtime: { provider: "deepseek", model_id: "deepseek-flash", thinking_level: "max" },
      test_benchmark: "new-workspace-test",
      paid_authorized: false,
    }),
  );
  const workspace = path.join(root, "workspace");
  await fs.mkdir(workspace);
  const skill = path.join(project, "agents/controller/agent_state/skills/evo-harness-rsi-toolkit");
  const request = path.join(workspace, "entry.json"),
    receipt = path.join(workspace, "receipt.json");
  const prompt = "使用 new-workspace-train 进行 RSI，沿用本项目已有实验配置。";
  const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
  const steps = [
    { name: "read_file", args: { file_path: path.join(skill, "SKILL.md") } },
    {
      name: "write_file",
      args: { file_path: request, content: JSON.stringify({ project, prompt, output: receipt }) },
    },
    {
      name: "exec_command",
      args: {
        cmd: `python3 -B ${quote(path.join(skill, "scripts/resources.py"))} ${quote(request)}`,
      },
    },
    { name: "read_file", args: { file_path: receipt } },
  ];
  let call = 0;
  vi.spyOn(GenerativeModel.prototype, "streamGenerate").mockImplementation(async function* () {
    const step = steps[call++];
    if (step)
      yield toolCall({
        name: step.name,
        arguments: JSON.stringify(step.args),
        toolCallId: "entry-" + call,
      });
    else
      yield assistantText(
        "Resources prepared; current budget authorization is missing. No experiment started.",
      );
    return { status: "completed" as const };
  });
  session = await agent.createSession({
    workspaceDir: workspace,
    source: "user",
    provider: "deepseek",
    modelId: "deepseek-flash",
    thinkingLevel: "max",
  });
  for await (const _ of session.run([userText(prompt)], { approve: async () => "allow" })) {
  }
  const result = JSON.parse(await fs.readFile(receipt, "utf8"));
  expect(result.ready).toBe(false);
  expect(result.plan.missing_inputs).toContain("current budget authorization");
  expect(result.plan.contracts[0].capabilities.original_solver_feedback).toBe(true);
  expect(result.plan.algorithm.test_repeats).toBe(3);
  expect(result.dispatches).toBe(0);
  expect(JSON.stringify(result)).not.toContain("PRIVATE_RUBRIC");
  expect(session.listBackgroundSubagents()).toHaveLength(0);
}, 20000);
