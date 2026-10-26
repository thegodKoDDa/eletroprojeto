'use client';

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from 'react';
import {
  ExperienceContext,
  experienceProfiles,
  experienceStorageKey,
  type ExperienceProfile,
  useExperience,
} from '@/lib/experience';
import { WorkspaceIcon } from '@/components/layout/WorkspaceIcon';

const changeEvent = 'eletroprojeto:experience-change';
function subscribe(listener: () => void) {
  window.addEventListener(changeEvent, listener);
  window.addEventListener('storage', listener);
  return () => {
    window.removeEventListener(changeEvent, listener);
    window.removeEventListener('storage', listener);
  };
}
const serverSnapshot = () => null;
const profiles: ExperienceProfile[] = ['beginner', 'professional', 'explore'];

function Choices({
  current,
  onChoose,
  dialog = false,
}: {
  current: ExperienceProfile | null;
  onChoose: (profile: ExperienceProfile) => void;
  dialog?: boolean;
}) {
  const heading = dialog ? 'experience-dialog-heading' : 'experience-heading';
  return (
    <section className="experience-content" aria-labelledby={heading}>
      <header className="experience-heading">
        <p className="eyebrow">SEU ESPAÇO, DO SEU JEITO</p>
        <h1 id={heading}>Como você quer usar o EletroProjeto?</h1>
        <p>
          Escolha o que você prefere ter em destaque. Todos os recursos ficam disponíveis nas três
          opções.
        </p>
      </header>
      <div className="experience-options">
        {profiles.map((profile) => {
          const item = experienceProfiles[profile];
          return (
            <button
              key={profile}
              type="button"
              className="experience-option"
              data-profile={profile}
              aria-current={current === profile ? 'true' : undefined}
              onClick={() => onChoose(profile)}
            >
              <span className="experience-option-top">
                <span className="experience-icon">
                  <WorkspaceIcon name={item.icon} />
                </span>
                {current === profile && <span className="experience-current">Perfil atual</span>}
              </span>
              <span className="experience-label">{item.label}</span>
              <span className="experience-title">{item.title}</span>
              <span className="experience-description">{item.description}</span>
              <span className="experience-features">
                {item.features.map((feature) => (
                  <span key={feature}>
                    <span aria-hidden="true">✓</span> {feature}
                  </span>
                ))}
              </span>
              <span className="experience-action">
                {item.action}
                <span aria-hidden="true">↗</span>
              </span>
            </button>
          );
        })}
      </div>
      <p className="experience-footnote">
        A escolha muda a apresentação e pode ser alterada a qualquer momento. Seus projetos e
        valores informados são preservados.
      </p>
    </section>
  );
}

export function ExperienceBoundary({ owner, children }: { owner: string; children: ReactNode }) {
  const read = useCallback((): ExperienceProfile | null => {
    try {
      const value = sessionStorage.getItem(experienceStorageKey(owner));
      return profiles.includes(value as ExperienceProfile) ? (value as ExperienceProfile) : null;
    } catch {
      return null;
    }
  }, [owner]);
  const stored = useSyncExternalStore(subscribe, read, serverSnapshot);
  const [selected, setSelected] = useState<ExperienceProfile | null>(null);
  const profile = selected ?? stored;
  const dialog = useRef<HTMLDialogElement>(null);
  const focusFrame = useRef<number | null>(null);
  useEffect(
    () => () => {
      if (focusFrame.current !== null) window.cancelAnimationFrame(focusFrame.current);
    },
    [],
  );
  const openChooser = useCallback(() => dialog.current?.showModal(), []);
  const context = useMemo(
    () => ({ profile: profile ?? ('explore' as ExperienceProfile), openChooser }),
    [profile, openChooser],
  );
  function choose(next: ExperienceProfile) {
    setSelected(next);
    try {
      sessionStorage.setItem(experienceStorageKey(owner), next);
      window.dispatchEvent(new Event(changeEvent));
    } catch {
      /* The current selection still works when browser storage is unavailable. */
    }
    if (dialog.current?.open) dialog.current.close();
    if (!profile && window.requestAnimationFrame)
      focusFrame.current = window.requestAnimationFrame(() => {
        focusFrame.current = null;
        document.querySelector<HTMLElement>('[data-workspace-heading]')?.focus();
      });
  }
  return (
    <ExperienceContext.Provider value={context}>
      {profile ? (
        children
      ) : (
        <main className="experience-page">
          <div className="experience-brand">
            <span className="brand-mark" aria-hidden="true">
              ϟ
            </span>
            <span>
              EletroProjeto<small>Consumo e estudos elétricos residenciais</small>
            </span>
          </div>
          <Choices current={null} onChoose={choose} />
          <p className="experience-session-note">
            Seu perfil é lembrado nesta aba. Use “Alterar perfil” para experimentar outra
            apresentação.
          </p>
        </main>
      )}
      <dialog
        ref={dialog}
        className="experience-dialog"
        aria-labelledby="experience-dialog-heading"
        onKeyDown={(event) => {
          if (event.key !== 'Tab') return;
          const buttons =
            event.currentTarget.querySelectorAll<HTMLButtonElement>('button:not(:disabled)');
          const first = buttons[0];
          const last = buttons[buttons.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }}
      >
        <div className="experience-dialog-bar">
          <span className="eyebrow">ALTERAR PERFIL</span>
          <button type="button" className="btn subtle" onClick={() => dialog.current?.close()}>
            Voltar sem alterar
          </button>
        </div>
        <Choices dialog current={profile} onChoose={choose} />
      </dialog>
    </ExperienceContext.Provider>
  );
}

export function ExperienceSwitcher() {
  const { profile, openChooser } = useExperience();
  return (
    <div className="experience-switcher" data-profile={profile}>
      <span>
        <small>PERFIL DE USO</small>
        <strong>{experienceProfiles[profile].shortLabel}</strong>
      </span>
      <button type="button" className="text-action" onClick={openChooser}>
        Alterar perfil
      </button>
    </div>
  );
}
