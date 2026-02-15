#!/usr/bin/env node

import { spawnSync } from "node:child_process";

const steps = [
  ["lint", ["run", "lint"]],
  ["typecheck", ["run", "typecheck"]],
  ["unit/integration", ["run", "test"]],
  ["contract", ["run", "test:contract"]],
  ["a11y", ["run", "test:a11y"]],
  ["build", ["run", "build"]],
  ["e2e", ["run", "test:e2e"]],
];

for (const [label, npmArgs] of steps) {
  console.log(`\n[gate] ${label}`);
  const result = spawnSync("npm", npmArgs, {
    stdio: "inherit",
    shell: true,
  });

  if (result.status !== 0) {
    console.error(`\n[gate] failed at ${label}`);
    process.exit(result.status ?? 1);
  }
}

console.log("\n[gate] all checks passed");

