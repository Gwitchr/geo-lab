import { EvalError } from "./errors.js";
import { parse } from "./parser.js";
import type { CompareOp, ExprNode, Field } from "./ast.js";

/** Maps filter-language field names to `listings` table columns. */
export const FIELD_COLUMNS: Record<Field, string> = {
  price: "price_mxn",
  m2: "m2",
  bedrooms: "bedrooms",
  type: "type",
  colonia: "colonia",
  municipio: "municipio",
  listed: "listed_date",
};

const NUMERIC_FIELDS: ReadonlySet<Field> = new Set(["price", "m2", "bedrooms"]);

export interface CompiledFilter {
  /** SQL boolean expression using positional '?' placeholders. */
  readonly sql: string;
  /** Bound parameters, in the order the '?' placeholders appear in `sql`. */
  readonly params: readonly unknown[];
}

/** Escape SQLite LIKE metacharacters so user input is matched literally. */
function escapeLike(raw: string): string {
  return raw.replace(/\\/g, "\\\\").replace(/%/g, "\\%").replace(/_/g, "\\_");
}

function compareOpSql(op: Exclude<CompareOp, ":">): string {
  switch (op) {
    case "<":
      return "<";
    case "<=":
      return "<=";
    case ">":
      return ">";
    case ">=":
      return ">=";
    case "=":
      return "=";
  }
}

function evalComparison(node: Extract<ExprNode, { kind: "comparison" }>): CompiledFilter {
  const column = FIELD_COLUMNS[node.field];
  const isNumericField = NUMERIC_FIELDS.has(node.field);

  if (node.op === ":") {
    if (isNumericField) {
      throw new EvalError(
        `Operator ':' (contains) is not valid for numeric field '${node.field}'; use <, <=, >, >=, or =`,
        node.position,
      );
    }
    const text = node.value.kind === "number" ? node.value.raw : node.value.value;
    const pattern = `%${escapeLike(text.toLowerCase())}%`;
    return { sql: `LOWER(${column}) LIKE ? ESCAPE '\\'`, params: [pattern] };
  }

  if (isNumericField) {
    let num: number;
    if (node.value.kind === "number") {
      num = node.value.value;
    } else {
      const parsed = Number(node.value.value);
      if (node.value.value.trim() === "" || Number.isNaN(parsed)) {
        const shown = node.value.quoted ? `"${node.value.value}"` : `'${node.value.value}'`;
        throw new EvalError(
          `Field '${node.field}' expects a numeric value, got ${shown}`,
          node.position,
        );
      }
      num = parsed;
    }
    return { sql: `${column} ${compareOpSql(node.op)} ?`, params: [num] };
  }

  // String field (type, colonia, municipio, listed) with <, <=, >, >=, or =.
  const text = node.value.kind === "number" ? node.value.raw : node.value.value;
  return { sql: `${column} ${compareOpSql(node.op)} ?`, params: [text] };
}

/**
 * Compile a node to SQL text without wrapping it in parens itself. AND/OR
 * chains of the same operator therefore render without redundant parens,
 * while a logical child gets parenthesized by `evalChild` wherever it is
 * actually needed to preserve the AST's grouping.
 */
function evalFragment(node: ExprNode): CompiledFilter {
  if (node.kind === "comparison") return evalComparison(node);

  const left = evalChild(node.left);
  const right = evalChild(node.right);
  const opSql = node.op === "and" ? "AND" : "OR";
  return {
    sql: `${left.sql} ${opSql} ${right.sql}`,
    params: [...left.params, ...right.params],
  };
}

/** Compile a node for use as a child of another logical node, parenthesizing it if it is itself logical. */
function evalChild(node: ExprNode): CompiledFilter {
  const compiled = evalFragment(node);
  if (node.kind === "logical") {
    return { sql: `(${compiled.sql})`, params: compiled.params };
  }
  return compiled;
}

/** Compile an already-parsed AST into a SQL WHERE fragment + bound params. */
export function compile(ast: ExprNode): CompiledFilter {
  return evalFragment(ast);
}

/** Parse and compile a filter expression in one step. */
export function compileFilter(source: string): CompiledFilter {
  return compile(parse(source));
}
