'use client';

export function Pagination({
  label,
  offset,
  pageSize,
  hasNext,
  busy = false,
  onPrevious,
  onNext,
  previousLabel = 'Anterior',
  nextLabel = 'Próxima',
  caption,
}: {
  label: string;
  offset: number;
  pageSize: number;
  hasNext: boolean;
  busy?: boolean;
  onPrevious: () => void;
  onNext: () => void;
  previousLabel?: string;
  nextLabel?: string;
  caption?: string;
}) {
  return (
    <nav className="pagination" aria-label={label} aria-busy={busy}>
      <button
        type="button"
        className="btn subtle"
        disabled={busy || offset === 0}
        onClick={onPrevious}
      >
        {previousLabel}
      </button>
      <span>{caption ?? `Página ${Math.floor(offset / pageSize) + 1}`}</span>
      <button type="button" className="btn subtle" disabled={busy || !hasNext} onClick={onNext}>
        {nextLabel}
      </button>
    </nav>
  );
}
