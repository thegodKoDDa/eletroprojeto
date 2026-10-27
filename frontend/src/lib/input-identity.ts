import defaults from './input-defaults.generated.json';

type Node = {
  defaults: Record<string, unknown>;
  objects: Record<string, string>;
  arrays: Record<string, string>;
};
const nodes: Record<string, Node> = defaults;

function canonical(value: unknown, schema?: string): unknown {
  if (Array.isArray(value)) return value.map((item) => canonical(item, schema));
  if (value === null || typeof value !== 'object') return value;
  const node = schema ? nodes[schema] : undefined;
  const input = Object.fromEntries(
    Object.entries(value).filter(([, entry]) => entry !== undefined),
  );
  const object = { ...node?.defaults, ...input };
  return Object.fromEntries(
    Object.keys(object)
      .sort()
      .map((key) => [
        key,
        canonical(object[key], Array.isArray(object[key]) ? node?.arrays[key] : node?.objects[key]),
      ]),
  );
}

/** Preserve explicit null/zero/false and array order. Only contract defaults and key order normalize. */
export function inputIdentity(
  value: unknown,
  schema: 'ProjectInput' | 'CalculationInput' = 'ProjectInput',
) {
  return JSON.stringify(canonical(value, schema));
}
