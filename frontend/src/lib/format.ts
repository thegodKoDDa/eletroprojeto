export const format = (value: unknown) =>
  value === null || value === undefined || value === '' || !Number.isFinite(Number(value))
    ? '—'
    : Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 3 });

export const BRASILIA_TIME_ZONE = 'America/Sao_Paulo';
export const formatDate = (value?: string | Date | null) =>
  value
    ? new Date(value).toLocaleString('pt-BR', {
        dateStyle: 'short',
        timeStyle: 'short',
        timeZone: BRASILIA_TIME_ZONE,
      })
    : 'Data indisponível';

export const formatCurrency = (value: unknown) =>
  value == null || value === '' || !Number.isFinite(Number(value))
    ? '—'
    : Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
