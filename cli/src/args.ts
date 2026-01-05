export interface ParsedArgs {
  positional: string[];
  options: Record<string, string | boolean>;
}

/**
 * Minimal argv parser: `--flag value`, `--flag=value`, and bare `--flag`
 * (boolean true) are all supported; everything else is positional.
 * Values that themselves look like flags (start with "--") are never
 * consumed as an option's value.
 */
export function parseArgs(argv: readonly string[]): ParsedArgs {
  const positional: string[] = [];
  const options: Record<string, string | boolean> = {};

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i] as string;
    if (arg.startsWith("--")) {
      const eq = arg.indexOf("=");
      if (eq !== -1) {
        options[arg.slice(2, eq)] = arg.slice(eq + 1);
        continue;
      }
      const key = arg.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith("--")) {
        options[key] = next;
        i++;
      } else {
        options[key] = true;
      }
      continue;
    }
    positional.push(arg);
  }

  return { positional, options };
}

export function optionString(options: Record<string, string | boolean>, key: string): string | undefined {
  const value = options[key];
  if (value === undefined) return undefined;
  if (typeof value === "boolean") {
    throw new Error(`Option --${key} requires a value`);
  }
  return value;
}

export function optionFlag(options: Record<string, string | boolean>, key: string): boolean {
  return options[key] !== undefined && options[key] !== false;
}

export function optionNumber(options: Record<string, string | boolean>, key: string): number | undefined {
  const raw = optionString(options, key);
  if (raw === undefined) return undefined;
  const num = Number(raw);
  if (Number.isNaN(num)) {
    throw new Error(`Option --${key} expects a number, got '${raw}'`);
  }
  return num;
}
