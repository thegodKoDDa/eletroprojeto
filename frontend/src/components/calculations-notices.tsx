'use client';
import type { components } from '@/lib/api.generated';
type Notice = components['schemas']['Notification'];
const groups: { category: Notice['category']; label: string; color: string }[] = [
  { category: 'error', label: 'Dados necessários ao cálculo selecionado', color: 'text-red-300' },
  { category: 'technical', label: 'Alertas técnicos', color: 'text-amber-200' },
  { category: 'normative', label: 'Cobertura normativa do sistema', color: 'text-amber-200' },
  { category: 'estimate', label: 'Valores estimados', color: 'muted' },
  { category: 'info', label: 'Informações', color: 'muted' },
];
export function focusField(id: string) {
  const field = document.getElementById(id);
  if (!field) return;
  let ancestor = field.parentElement;
  while (ancestor) {
    if (ancestor instanceof HTMLDetailsElement) ancestor.open = true;
    ancestor = ancestor.parentElement;
  }
  if (window.location.hash !== '#project') {
    window.history.replaceState(null, '', '#project');
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  }
  field.setAttribute('data-correction-target', 'true');
  field.scrollIntoView?.({
    behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
      ? 'instant'
      : 'smooth',
    block: 'center',
  });
  field.focus({ preventScroll: true });
  field.addEventListener('blur', () => field.removeAttribute('data-correction-target'), {
    once: true,
  });
}
export function CalculationNotices({ notices, stale }: { notices: Notice[]; stale: boolean }) {
  if (stale) return <p className="text-xs muted">Revalidando avisos para as entradas atuais…</p>;
  return (
    <div className="space-y-2" aria-label="Avisos do cálculo">
      {groups.map((group) => {
        const items = [
          ...new Map(
            notices
              .filter((item) => item.category === group.category)
              .map((item) => [item.id, item]),
          ).values(),
        ];
        if (!items.length) return null;
        return (
          <details key={group.category} open={group.category === 'error' ? true : undefined}>
            <summary className={`cursor-pointer text-xs ${group.color}`}>
              {group.label} ({items.length})
            </summary>
            <ul className="mt-2 space-y-3">
              {items.map((item) => (
                <li key={item.id} className="text-xs leading-5">
                  <p className={group.color}>
                    {item.location.join(' → ')} · {item.problem}
                  </p>
                  <p className="muted">
                    Afeta: {item.affected_results.join(', ')}. {item.solution}
                  </p>
                  {item.target_id && (
                    <button
                      className="text-emerald-300 underline"
                      aria-label={`Corrigir informação: ${item.location.join(' → ')} · ${item.problem}`}
                      onClick={() => focusField(item.target_id!)}
                    >
                      Corrigir informação
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </details>
        );
      })}
    </div>
  );
}
