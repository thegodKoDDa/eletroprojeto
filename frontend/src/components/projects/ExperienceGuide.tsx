'use client';

import { useExperience } from '@/lib/experience';
import { focusField } from '@/components/calculations-notices';

export function ExperienceGuide({ onKnowledge }: { onKnowledge: () => void }) {
  const { profile } = useExperience();
  if (profile === 'explore') return null;
  return (
    <section
      className="experience-guide"
      data-profile={profile}
      aria-label={
        profile === 'beginner' ? 'Orientação para estimar consumo' : 'Atalhos profissionais'
      }
    >
      <div>
        <p className="eyebrow">
          {profile === 'beginner' ? 'COMECE PELO ESSENCIAL' : 'FERRAMENTAS DO ESTUDO'}
        </p>
        <p>
          {profile === 'beginner'
            ? 'Cadastre os aparelhos e informe os kWh da etiqueta ou a potência e os horários de uso. A tarifa permite estimar o custo.'
            : 'Acesse dados elétricos, referências e verificações condicionadas. Os estudos não substituem a revisão técnica da instalação.'}
        </p>
      </div>
      <nav
        aria-label={profile === 'beginner' ? 'Caminho da estimativa' : 'Ferramentas profissionais'}
      >
        {(profile === 'beginner'
          ? [
              ['01 · Identificar projeto', 'project.name'],
              ['02 · Cadastrar aparelhos', 'add-environment'],
              ['03 · Conferir estimativa', 'results'],
            ]
          : [
              ['Dados elétricos', 'project.utility'],
              ['Demanda', 'technical-demand'],
              ['Circuitos e proteções', 'technical-circuits'],
              ['Localização', 'technical-bathroom'],
              ['Território', 'technical-territory'],
              ['Resultados e memória', 'results'],
            ]
        ).map(([label, target]) => (
          <button type="button" key={target} onClick={() => focusField(target)}>
            {label}
          </button>
        ))}
        {profile === 'professional' && (
          <button type="button" onClick={onKnowledge}>
            Biblioteca técnica
          </button>
        )}
      </nav>
      {profile === 'beginner' && (
        <p className="experience-guide-caption">
          Campos necessários à operação atual recebem destaque. Os dados complementares e todos os
          estudos técnicos continuam disponíveis abaixo.
        </p>
      )}
    </section>
  );
}
