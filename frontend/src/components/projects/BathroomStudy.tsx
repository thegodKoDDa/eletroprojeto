import type { CalculationResult, Environment, ProjectInput } from '@/lib/api';
import { format } from '@/lib/format';
import { SectionHeading } from '@/components/ui/SectionHeading';

type Geometry = NonNullable<Environment['bathroom_geometry']>;
type Point = NonNullable<Geometry['points']>[number];
const coordinates = ['x_min_m', 'x_max_m', 'y_min_m', 'y_max_m', 'z_min_m', 'z_max_m'] as const;
const labels = ['X mínimo', 'X máximo', 'Y mínimo', 'Y máximo', 'Z mínimo', 'Z máximo'];

type Props = {
  input: ProjectInput;
  result?: CalculationResult;
  onChange: (id: string, patch: Partial<Environment>) => void;
};
export function BathroomStudy({ input, result, onChange }: Props) {
  const rooms = (input.environments ?? []).filter(
    (room) => room.type === 'bathroom' || room.bathroom_geometry,
  );
  return (
    <section className="panel mt-4" aria-label="Localização de componentes no banheiro">
      <SectionHeading
        eyebrow="ESTUDO / LOCALIZAÇÃO"
        title="Volumes do chuveiro"
        description="Estudo opcional do chuveiro sem piso-boxe, rebaixo ou delimitação clara; piso único no mesmo nível, sem paredes ou divisórias intermediárias. Informe metros no mesmo referencial, com Z=0 no piso de banho. Não abrange banheira ou cabine pré-fabricada."
      />
      {!rooms.length && (
        <p className="mt-3 muted">
          Cadastre um ambiente do tipo banheiro para estudar seus componentes.
        </p>
      )}
      {rooms.map((room) => {
        const geometry = room.bathroom_geometry;
        const rows = result?.bathroom_geometry_results?.find(
          (row) => row.environment_id === room.id,
        );
        const update = (patch: Partial<Geometry>) =>
          onChange(room.id!, {
            bathroom_geometry: { scope_confirmed: false, points: [], ...geometry, ...patch },
          });
        const updatePoint = (id: string, patch: Partial<Point>) =>
          update({
            points: geometry?.points?.map((point) =>
              point.id === id ? { ...point, ...patch } : point,
            ),
          });
        return (
          <fieldset key={room.id} className="mt-4">
            <legend>{room.name}</legend>
            <label className="mt-2 flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!geometry}
                onChange={(e) =>
                  onChange(room.id!, {
                    bathroom_geometry: e.target.checked
                      ? { scope_confirmed: false, points: [] }
                      : null,
                  })
                }
              />
              Estudar localização em {room.name}
            </label>
            {geometry && (
              <>
                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  {(['shower_x_m', 'shower_y_m'] as const).map((field) => (
                    <label key={field}>
                      {field === 'shower_x_m' ? 'X' : 'Y'} da saída do chuveiro (m)
                      <input
                        type="number"
                        min="0"
                        step="any"
                        value={geometry[field] ?? ''}
                        onChange={(e) => update({ [field]: e.target.value || null })}
                      />
                    </label>
                  ))}
                  <label>
                    Fonte das medidas de {room.name}
                    <input
                      maxLength={200}
                      value={geometry.measurement_source ?? ''}
                      onChange={(e) => update({ measurement_source: e.target.value || null })}
                    />
                  </label>
                </div>
                <label className="mt-3 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={geometry.scope_confirmed ?? false}
                    onChange={(e) => update({ scope_confirmed: e.target.checked })}
                  />
                  Conferi chuveiro sem delimitação, piso único no mesmo nível e ausência de
                  paredes/divisórias intermediárias em {room.name}
                </label>
                <p className="mt-2 text-xs muted">
                  Cadastre o envelope externo completo de cada componente; não apenas seu centro. As
                  fronteiras recebem o volume mais restritivo. Nenhuma posição é presumida.
                </p>
                {(geometry.points ?? []).map((point, index) => {
                  const pointResult = rows?.points.find((p) => p.point_id === point.id);
                  return (
                    <fieldset key={point.id} className="mt-3 demand-load">
                      <legend>
                        Componente {index + 1} · {room.name}
                      </legend>
                      <div className="grid gap-3 md:grid-cols-3">
                        <label>
                          Nome do componente
                          <input
                            maxLength={200}
                            value={point.name}
                            onChange={(e) => updatePoint(point.id!, { name: e.target.value })}
                          />
                        </label>
                        <label>
                          Tipo do componente
                          <select
                            value={point.kind ?? 'other'}
                            onChange={(e) =>
                              updatePoint(point.id!, { kind: e.target.value as Point['kind'] })
                            }
                          >
                            <option value="socket">Tomada comum</option>
                            <option value="switch">Interruptor comum</option>
                            <option value="water_heater">Aquecedor de água</option>
                            <option value="luminaire">Luminária</option>
                            <option value="other">Outro componente</option>
                          </select>
                        </label>
                        {coordinates.map((field, i) => (
                          <label key={field}>
                            {labels[i]} de {point.name} (m)
                            <input
                              type="number"
                              min="0"
                              step="any"
                              value={point[field] ?? ''}
                              onChange={(e) =>
                                updatePoint(point.id!, { [field]: e.target.value || null })
                              }
                            />
                          </label>
                        ))}
                      </div>
                      <button
                        type="button"
                        className="mt-3"
                        onClick={() =>
                          update({ points: geometry.points?.filter((p) => p.id !== point.id) })
                        }
                      >
                        Remover {point.name}
                      </button>
                      {pointResult && (
                        <div className="mt-2" role="status">
                          <p>
                            {pointResult.volume
                              ? pointResult.volume === 'outside'
                                ? 'Fora dos volumes deste modelo'
                                : `Volume ${pointResult.volume}`
                              : 'Localização pendente'}{' '}
                            · distância horizontal mínima:{' '}
                            {format(pointResult.nearest_horizontal_distance_m)} m
                          </p>
                          {pointResult.pending_checks.map((message) => (
                            <p key={message}>{message}</p>
                          ))}
                        </div>
                      )}
                    </fieldset>
                  );
                })}
                <button
                  type="button"
                  className="mt-3"
                  onClick={() =>
                    update({
                      points: [
                        ...(geometry.points ?? []),
                        { id: crypto.randomUUID(), name: 'Novo componente', kind: 'other' },
                      ],
                    })
                  }
                >
                  Adicionar componente em {room.name}
                </button>
                {rows && (
                  <div className="mt-3 text-sm" role="status">
                    {rows.pending_checks.map((message) => (
                      <p key={message}>{message}</p>
                    ))}
                    <p>{rows.reference}</p>
                    {rows.limitations.map((message) => (
                      <p key={message}>{message}</p>
                    ))}
                  </div>
                )}
              </>
            )}
          </fieldset>
        );
      })}
    </section>
  );
}
