'use client';
import { useEffect, useRef } from 'react';
import { Feedback, type FeedbackTone } from './Feedback';

export function OperationNotice({
  text,
  tone,
  onClose,
}: {
  text: string;
  tone: FeedbackTone;
  onClose: () => void;
}) {
  const origin = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (
      text &&
      document.activeElement instanceof HTMLElement &&
      document.activeElement !== document.body &&
      !document.activeElement.closest('.operation-notice')
    )
      origin.current = document.activeElement;
  }, [text]);
  if (!text) return null;
  return (
    <aside className="operation-notice" aria-label="Aviso da operação">
      <Feedback tone={tone} data-testid="project-message">
        <span>{text}</span>
      </Feedback>
      <button
        type="button"
        className="notice-close"
        aria-label="Fechar aviso da operação"
        onClick={() => {
          const target = origin.current;
          onClose();
          if (target?.isConnected && !target.matches(':disabled'))
            target.focus({ preventScroll: true });
          else
            document
              .querySelector<HTMLElement>('[data-workspace-heading]')
              ?.focus({ preventScroll: true });
        }}
      >
        ×
      </button>
    </aside>
  );
}
