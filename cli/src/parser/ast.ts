/**
 * AST types for the geoq filter language.
 *
 * Grammar (see docs/filter-language.md for the full reference):
 *
 *   expr    := orExpr
 *   orExpr  := andExpr (("or") andExpr)*
 *   andExpr := clause (("and") clause)*
 *   clause  := field op value | "(" expr ")"
 *   field   := price | m2 | bedrooms | type | colonia | municipio | listed
 *   op      := "<" | "<=" | ">" | ">=" | "=" | ":"
 *   value   := number | quoted string | bare word
 *
 * "and" binds tighter than "or"; parentheses override.
 */

export const FIELDS = [
  "price",
  "m2",
  "bedrooms",
  "type",
  "colonia",
  "municipio",
  "listed",
] as const;

export type Field = (typeof FIELDS)[number];

export const COMPARE_OPS = ["<", "<=", ">", ">=", "=", ":"] as const;

export type CompareOp = (typeof COMPARE_OPS)[number];

export type LogicalOp = "and" | "or";

export interface NumberValue {
  readonly kind: "number";
  readonly value: number;
  /** Original source text, e.g. "2500000" or "-3.5". */
  readonly raw: string;
}

export interface StringValue {
  readonly kind: "string";
  readonly value: string;
  /** True when the source used quotes ("..." or '...'); false for bare words. */
  readonly quoted: boolean;
}

export type Value = NumberValue | StringValue;

export interface ComparisonNode {
  readonly kind: "comparison";
  readonly field: Field;
  readonly op: CompareOp;
  readonly value: Value;
  /** Character offset of the field token, for error reporting. */
  readonly position: number;
}

export interface LogicalNode {
  readonly kind: "logical";
  readonly op: LogicalOp;
  readonly left: ExprNode;
  readonly right: ExprNode;
  readonly position: number;
}

export type ExprNode = ComparisonNode | LogicalNode;

export function isField(value: string): value is Field {
  return (FIELDS as readonly string[]).includes(value);
}
