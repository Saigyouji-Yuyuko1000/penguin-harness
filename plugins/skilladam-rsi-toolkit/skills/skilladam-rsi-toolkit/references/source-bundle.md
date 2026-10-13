# Build a source bundle for Harbor

Run this preparation on the machine chosen for the experiment, before launching any model calls. Use a Linux checkout and Node binary matching the task containers' architecture. Resolve `REPO` to the Penguin source checkout, `CHECKOUT` to the benchmark repository at the commit in the installed statements, and `OUT` to this experiment's output directory. These are separate directories. Require Docker access, Compose, uv, Python 3, pnpm and Node >= 24. Follow the benchmark repository's shared-checkout setup and run rules; never replace someone else's checkout or installation.

## Stage the source and its dependencies

Build the local production dependency graph, then use pnpm's workspace deployment to stage it. Installing a CLI tarball with npm alone can resolve its core/server dependencies from the registry and does not meet this requirement.

```bash
cd "$REPO"
pnpm install --frozen-lockfile
pnpm --filter '@prismshadow/penguin-cli...' build

STAGE="$(mktemp -d "$OUT/source-bundle-XXXXXX")"
BUNDLE_ROOT="$STAGE/penguin-bench"
CLI_ROOT="$BUNDLE_ROOT/npm/lib/node_modules/@prismshadow/penguin-cli"
mkdir -p "$BUNDLE_ROOT/bin" "$(dirname "$CLI_ROOT")"
pnpm --filter @prismshadow/penguin-cli deploy --prod "$CLI_ROOT"

# This helper downloads and verifies Node only, not the Penguin release.
sh "$CHECKOUT/agents/penguin_agent/node_install.sh" 24.18.0 "$BUNDLE_ROOT/node"
cat > "$BUNDLE_ROOT/bin/penguin" <<'SHIM'
#!/bin/sh
exec /opt/penguin-bench/node/bin/node /opt/penguin-bench/npm/lib/node_modules/@prismshadow/penguin-cli/dist/penguin.js "$@"
SHIM
chmod 755 "$BUNDLE_ROOT/bin/penguin"
```

Check the exit status after each command; stop if any build or deploy fails. Before packaging, verify:

- The deployed CLI, core, server and workspace plugin packages come from this checkout. Compare their staged `dist/` or declared package files with the corresponding source build, and retain the hashes. The new optimizer plugin is imported separately on the controller; the Target's learned Skill travels in its State archive.
- Every deployed symlink resolves within `BUNDLE_ROOT`; a link back to the host checkout or pnpm store is not a portable bundle.
- The staged Node can run `CLI_ROOT/dist/penguin.js version --json` without the host's `node_modules` or CLI. Record its build identity, not only the npm release number.

Write `BUNDLE_ROOT/bundle.json` as JSON with `penguin_version` from the deployed CLI manifest, `node_version` from the staged Node without its `v` prefix, `arch` from `uname -m`, and `built_at` in UTC. Add `source` metadata containing the checkout commit, dirty status, lockfile hash and the verified package/build hashes. Keep the source revision and any local diff with the experiment. An npm version by itself is not proof of a source build.

```bash
BUNDLE="$OUT/penguin-source.tar.gz"
# Require both output names to be unused before creating them.
tar -czf "$BUNDLE.partial" -C "$STAGE" penguin-bench
mv "$BUNDLE.partial" "$BUNDLE"
sha256sum "$BUNDLE"
```

Record the archive hash and versions in `experiment.json`. Keep the staging tree until validation succeeds. All workers use this exact archive; a changed build starts a new experiment.

## Validate the container path before evolution

First check that the bundled launcher runs in the task's container environment. Then run one training cell through the existing Harbor evaluator, with this bundle and the explicit Target/project/model arguments from `gdpevo.md`. Use a fresh Target and job, concurrency one, and the installed task's unchanged turn/time/resource/network limits. This is a preparation check, not an optimizer iteration or an improvement claim.

Validate the actual runtime identity, native verifier reward, complete worker result, receipt-to-trial binding and readable Target traces. Confirm the score can be formatted with `skilladam.py report` against a specification for exactly this one cell; keep this preparation result separate from the experiment's reporting set. If the Target never starts, repair the diagnosed setup problem before a bounded retry; if it runs and scores zero, retain that real result. Once these checks pass, start the configured experiment. Report this preparation call's cost separately.
