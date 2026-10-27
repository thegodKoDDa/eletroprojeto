'use client';

import { useStableHeight } from '@/lib/use-stable-height';
import { useId, useState } from 'react';
import { useExperience } from '@/lib/experience';
import { focusField } from '@/components/calculations-notices';
import { estimateJourney } from '@/lib/journey';
import type { components } from '@/lib/api.generated';
import type { CalculationResult, ProjectInput } from '@/lib/api';

export function ExperienceGuide({
  onKnowledge,
  input,
  result,
  reviewedDigest,
  saved,
  requirements,
  loading,
  error,
  issueTarget,
}: {
  onKnowledge: () => void;
  input: ProjectInput;
  result?: CalculationResult;
  reviewedDigest?: string;
  saved: boolean;
  loading: boolean;
  error?: string;
  issueTarget?: string;
  requirements: Record<string, components['schemas']['FieldRequirement']>;
}) {
  const { profile } = useExperience();
  const heightRef = useStableHeight(profile, loading);
  const [stepsExpanded, setStepsExpanded] = useState(false);
  const stepsId = useId();
  if (profile === 'explore') return null;
  const steps = estimateJourney(input, result, reviewedDigest, saved, requirements);
  const next = steps.find((step) => !step.complete);
  const waiting = next?.id === 'energy' && loading;
  const correction = next?.id === 'energy' && !result && !loading;
  const completed = steps.filter((step) => step.complete).length;
  const firstLoadId = input.environments?.flatMap((room) => room.loads ?? [])[0]?.id;
  const progress = (
    <>
      <div className="journey-heading">
        <div>
          <p className="eyebrow">PASSO A PASSO</p>
          <h2>Seu caminho até a estimativa</h2>
        </div>
        <span className="status-pill" data-state={next ? 'neutral' : 'saved'}>
          {completed} de {steps.length} concluídas
        </span>
      </div>
      <button
        type="button"
        className="journey-toggle btn subtle"
        aria-expanded={stepsExpanded}
        aria-controls={stepsId}
        onClick={() => setStepsExpanded((value) => !value)}
      >
        {stepsExpanded ? 'Recolher etapas' : 'Ver todas as etapas'}{' '}
        <span aria-hidden="true">{stepsExpanded ? '−' : '+'}</span>
      </button>
      <ol
        id={stepsId}
        className="journey-steps"
        data-expanded={stepsExpanded}
        aria-label="Tarefas da estimativa"
      >
        {steps.map((step, index) => (
          <li
            key={step.id}
            data-state={step.complete ? 'complete' : next?.id === step.id ? 'current' : 'pending'}
          >
            <button
              type="button"
              aria-current={next?.id === step.id ? 'step' : undefined}
              disabled={step.id === 'energy' && loading}
              title={
                step.id === 'energy' && loading
                  ? 'Aguarde o cálculo das entradas atuais.'
                  : undefined
              }
              onClick={() =>
                focusField(
                  step.id === 'energy' && !result ? (issueTarget ?? 'results') : step.target,
                )
              }
            >
              <span className="journey-number" aria-hidden="true">
                {step.complete ? '✓' : index + 1}
              </span>
              <span>
                {step.title}
                <small>
                  {step.complete ? 'Concluída' : next?.id === step.id ? 'Próxima ação' : 'A fazer'}
                </small>
              </span>
            </button>
          </li>
        ))}
      </ol>
      <div className="journey-next" role="status" aria-live="polite" aria-atomic="true">
        <div>
          <span className="help-label">{next ? 'AGORA' : 'ETAPAS CONCLUÍDAS'}</span>
          <h3>{next?.title ?? 'Sua estimativa está conferida e salva'}</h3>
          <p>
            {(correction
              ? error
                ? 'O cálculo não terminou. Confira os avisos e corrija as entradas indicadas. Seus dados continuam no formulário.'
                : 'Aguarde um resultado atual antes de conferir o consumo.'
              : next?.help) ??
              'Você pode continuar editando ou exportar o relatório. Alterações nos dados reabrem as tarefas que precisam de revisão.'}
          </p>
        </div>
        {next ? (
          <button
            type="button"
            className="btn primary"
            disabled={waiting}
            onClick={() => focusField(correction ? (issueTarget ?? 'results') : next.target)}
          >
            Ir para{' '}
            {next.id === 'identity'
              ? 'identificação'
              : next.id === 'inventory'
                ? 'cadastro'
                : next.id === 'energy'
                  ? 'dados de uso'
                  : next.id === 'review'
                    ? 'conferência'
                    : 'salvamento'}{' '}
            <span aria-hidden="true">→</span>
          </button>
        ) : (
          <span className="journey-complete-action" aria-hidden="true">
            ✓
          </span>
        )}
      </div>
      <p className="experience-guide-caption">
        Progresso da estimativa, sem aprovação técnica. Dados não são presumidos nem salvos
        automaticamente.
      </p>
    </>
  );
  return (
    <section
      ref={heightRef}
      className="experience-guide"
      data-profile={profile}
      aria-label={
        profile === 'beginner' ? 'Orientação para estimar consumo' : 'Atalhos profissionais'
      }
    >
      {profile === 'beginner' ? (
        progress
      ) : (
        <>
          <div className="journey-heading">
            <div>
              <p className="eyebrow">FERRAMENTAS DO ESTUDO</p>
              <h2>Acesse o que precisa analisar</h2>
              <p>
                Os estudos são opcionais. Confira o escopo, as fontes e as pendências em cada um.
              </p>
            </div>
            <span className="status-pill">Uso profissional</span>
          </div>
          <nav className="tool-shortcuts" aria-label="Ferramentas profissionais">
            {[
              [
                'Concessionária',
                'project.utility',
                'Confirme a distribuidora e os dados do projeto.',
              ],
              ['Demanda', 'technical-demand', 'Revise inventário, condições e fontes do método.'],
              [
                'Circuitos e proteções',
                'technical-circuits',
                'Estude cabos e proteções no escopo disponível.',
              ],
              [
                'Localização',
                'technical-bathroom',
                'Informe medidas e confira os limites geométricos.',
              ],
              [
                'Território',
                'technical-territory',
                'Consulte registros oficiais sem seleção automática.',
              ],
              [
                'Resultados e memória',
                'results-memory',
                'Confira hipóteses, fórmulas e pendências.',
              ],
              ...(firstLoadId
                ? [
                    [
                      'Parâmetros dos aparelhos',
                      `load.${firstLoadId}.voltage_v`,
                      'Revise tensão, fator de potência e dados da referência.',
                    ],
                  ]
                : []),
            ].map(([label, target, help]) => (
              <button
                type="button"
                key={target}
                aria-label={label}
                onClick={() => focusField(document.getElementById(target) ? target : 'results')}
              >
                <span>{label}</span>
                <small>{help}</small>
              </button>
            ))}
            <button type="button" aria-label="Biblioteca técnica" onClick={onKnowledge}>
              <span>Biblioteca técnica</span>
              <small>Consulte fontes, referências e estado da validação.</small>
            </button>
          </nav>
          <details className="journey-disclosure">
            <summary>
              Acompanhar as etapas da estimativa · {completed} de {steps.length}
            </summary>
            {progress}
          </details>
        </>
      )}
    </section>
  );
}
