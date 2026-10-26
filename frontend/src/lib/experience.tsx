'use client';

import { createContext, useContext } from 'react';

export type ExperienceProfile = 'beginner' | 'professional' | 'explore';
export const experienceStorageKey = (owner: string) =>
  `eletroprojeto:experience:v1:${encodeURIComponent(owner)}`;
export const experienceProfiles = {
  beginner: {
    label: 'USUÁRIO LEIGO',
    shortLabel: 'Leigo',
    title: 'Entenda o consumo da sua casa.',
    description:
      'Um caminho guiado, com os dados essenciais em destaque e explicações em linguagem simples.',
    features: ['Ambientes e aparelhos', 'Consumo e custo mensal', 'Ajuda para completar os dados'],
    action: 'Começar com orientação',
    icon: 'home',
  },
  professional: {
    label: 'USUÁRIO PROFISSIONAL',
    shortLabel: 'Profissional',
    title: 'Aprofunde o seu estudo.',
    description:
      'Dados elétricos, memória de cálculo e estudos técnicos em destaque, junto da estimativa de consumo.',
    features: [
      'Parâmetros elétricos e referências',
      'Demanda, circuitos e proteções',
      'Memória de cálculo e relatórios',
    ],
    action: 'Abrir espaço profissional',
    icon: 'project',
  },
  explore: {
    label: 'ESTOU APENAS DANDO UMA OLHADA',
    shortLabel: 'Exploração',
    title: 'Explore no seu ritmo.',
    description:
      'A organização atual do EletroProjeto, com consumo em primeiro plano e estudos técnicos recolhidos.',
    features: ['Consumo em primeiro plano', 'Estudos técnicos recolhidos', 'Navegação original'],
    action: 'Conhecer o EletroProjeto',
    icon: 'library',
  },
} as const;

export const ExperienceContext = createContext<{
  profile: ExperienceProfile;
  openChooser: () => void;
}>({ profile: 'explore', openChooser: () => {} });
export const useExperience = () => useContext(ExperienceContext);

/** Presentation only. This never changes calculation inputs, access or validation. */
export function fieldEmphasis(field: string, profile: ExperienceProfile, required: boolean) {
  if (profile === 'beginner') {
    if (required) return 'essential';
    if (
      field === 'project.energy_tariff_brl_per_kwh' ||
      field.startsWith('load.parameters.usage_') ||
      field === 'load.parameters.monthly_energy_kwh'
    )
      return 'recommended';
  }
  if (
    profile === 'professional' &&
    (field === 'project.utility' ||
      (field.startsWith('environment.') &&
        !['environment.name', 'environment.type'].includes(field)) ||
      ['load.voltage_v', 'load.power_factor'].includes(field) ||
      (field.startsWith('load.parameters.') &&
        !field.includes('usage_') &&
        !field.includes('monthly_energy')))
  )
    return 'technical';
  return undefined;
}
