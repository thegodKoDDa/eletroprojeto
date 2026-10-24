'use client';
import {
  Children,
  cloneElement,
  createContext,
  isValidElement,
  useContext,
  type ReactNode,
  type ReactElement,
} from 'react';
import type { components } from '@/lib/api.generated';
export const CalculationScopeContext = createContext('installed');
export const RequirementsContext = createContext<
  Record<string, components['schemas']['FieldRequirement']>
>({});
type Control = {
  id?: string;
  type?: string;
  value?: unknown;
  min?: string;
  max?: string;
  step?: string;
  maxLength?: number;
  'aria-label'?: string;
  required?: boolean;
  'aria-required'?: boolean;
  'aria-invalid'?: boolean;
  'aria-describedby'?: string;
};

/** Consumes API dependencies; validates only ordinary HTML form constraints. */
export function Field({
  field,
  label,
  children,
  parameters = {},
  path = field,
  className,
}: {
  field: string;
  label: string;
  children: ReactNode;
  parameters?: Record<string, unknown>;
  path?: string;
  className?: string;
}) {
  const rule = useContext(RequirementsContext)[field];
  const operation = useContext(CalculationScopeContext);
  const required =
    !!rule &&
    (rule.required_for ?? ['installed', 'apparent', 'current', 'normative']).includes(operation) &&
    (!rule.when || Object.entries(rule.when).every(([key, value]) => parameters[key] === value));
  const controls = Children.toArray(children);
  const rendered = controls.map((child) => {
    if (!isValidElement(child)) return { node: child, error: '' };
    const control = child as ReactElement<Control>;
    if (!['input', 'select', 'textarea'].includes(String(control.type)))
      return { node: child, error: '' };
    const props = {
      ...control.props,
      ...(rule?.minimum != null ? { min: String(rule.minimum) } : {}),
      ...(rule?.maximum != null ? { max: String(rule.maximum) } : {}),
      ...(rule?.integer ? { step: '1' } : {}),
      ...(rule?.max_length != null ? { maxLength: rule.max_length } : {}),
    };
    const value = props.value;
    const empty =
      value == null ||
      String(value).trim() === '' ||
      (['load.parameters.configuration', 'project.utility'].includes(field) &&
        ['unknown', 'unconfirmed'].includes(String(value)));
    let invalid = props.maxLength != null && String(value ?? '').length > props.maxLength;
    if (props.type === 'number' && !empty) {
      const number = Number(value);
      invalid =
        !Number.isFinite(number) ||
        (props.min !== undefined && number < Number(props.min)) ||
        (props.max !== undefined && number > Number(props.max)) ||
        (props.step === '1' && !Number.isInteger(number));
    }
    const error =
      required && empty
        ? `${label}: preenchimento necessário para ${rule.purpose}.`
        : invalid
          ? `${label}: valor inválido.`
          : '';
    return {
      error,
      node: cloneElement(control, {
        min: props.min,
        max: props.max,
        step: props.step,
        maxLength: props.maxLength,
        id: path,
        'aria-label': props['aria-label'] ?? label,
        required,
        'aria-required': required,
        'aria-invalid': !!error,
        'aria-describedby':
          [props['aria-describedby'], ...(error ? [`${path}-error`] : [])]
            .filter(Boolean)
            .join(' ') || undefined,
      }),
    };
  });
  const error = rendered.find((item) => item.error)?.error;
  return (
    <label className={className} htmlFor={path}>
      {label}
      {required && (
        <span
          className="required-mark"
          aria-hidden="true"
          title={`Necessário para ${rule.purpose}`}
        >
          {' '}
          *
        </span>
      )}
      {rendered.map((item) => item.node)}
      {error && (
        <span id={`${path}-error`} className="field-error">
          {error}
        </span>
      )}
    </label>
  );
}
