import type { Load } from '@/lib/api';

type Classification = NonNullable<Load['energisa_demand']>;
type Props = {
  name: string;
  value: Classification;
  onChange: (patch: Partial<Classification>) => void;
};

function NumberField({
  label,
  value,
  onChange,
  ratio = false,
}: {
  label: string;
  value?: string | number | null;
  onChange: (value: string | null) => void;
  ratio?: boolean;
}) {
  return (
    <label>
      {label}
      <input
        type="number"
        min="0.000001"
        max={ratio ? 1 : undefined}
        step="any"
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value || null)}
      />
    </label>
  );
}

export function DemandLoadParameters({ name, value, onChange }: Props) {
  if (value.group === 'd6') {
    const motor = value.motor ?? {};
    const update = (patch: Partial<NonNullable<Classification['motor']>>) =>
      onChange({ motor: { ...motor, ...patch } });
    return (
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <p className="text-xs muted md:col-span-2">
          Motores e solda motor-gerador: fases e potência de eixo da placa. O método consulta a
          linha exata das Tabelas 12/13; não altera W ou FP cadastrados. Partida exige estudo
          próprio.
        </p>
        <label>
          Fases do motor de {name}
          <select
            value={motor.configuration ?? ''}
            onChange={(e) =>
              update({ configuration: (e.target.value || null) as typeof motor.configuration })
            }
          >
            <option value="">Confirmar fases</option>
            <option value="single_phase">Monofásico</option>
            <option value="three_phase">Trifásico</option>
          </select>
        </label>
        <label>
          Potência de eixo em cv de {name}
          <select
            value={motor.shaft_power_cv ?? ''}
            onChange={(e) => update({ shaft_power_cv: e.target.value || null })}
          >
            <option value="">Selecionar linha da tabela</option>
            {[
              '1/6',
              '1/4',
              '1/3',
              '1/2',
              '2/3',
              '3/4',
              '1',
              '1.5',
              '2',
              '3',
              '4',
              '5',
              '6',
              '7.5',
              '10',
              '12.5',
              '15',
              '20',
              '25',
              '30',
            ].map((cv) => (
              <option key={cv} value={cv}>
                {cv} cv
              </option>
            ))}
          </select>
        </label>
        <label className="md:col-span-2">
          Fonte das fases e potência de eixo de {name}
          <input
            maxLength={200}
            value={motor.source ?? ''}
            onChange={(e) => update({ source: e.target.value || null })}
          />
        </label>
      </div>
    );
  }
  if (value.group === 'd5' && value.air_conditioning_type === 'central_unit') {
    const central = value.central ?? {};
    const update = (patch: Partial<NonNullable<Classification['central']>>) =>
      onChange({ central: { ...central, ...patch } });
    return (
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <p className="text-xs muted md:col-span-2">
          Use corrente máxima total, tensão e FP do mesmo regime, fornecidos pelo fabricante (§9.1,
          nota I). Corrente nominal, de partida e MCA não substituem esse dado. Fator de demanda:
          100%.
        </p>
        <label>
          Configuração da central de {name}
          <select
            value={central.configuration ?? ''}
            onChange={(e) =>
              update({ configuration: (e.target.value || null) as typeof central.configuration })
            }
          >
            <option value="">Confirmar configuração</option>
            <option value="single_phase">Monofásica</option>
            <option value="balanced_three_phase">Trifásica equilibrada</option>
          </select>
        </label>
        <NumberField
          label={`Tensão da central de ${name} (V; entre fases se trifásica)`}
          value={central.voltage_v}
          onChange={(voltage_v) => update({ voltage_v })}
        />
        <NumberField
          label={`Corrente máxima total de ${name} (A por unidade)`}
          value={central.maximum_total_current_a}
          onChange={(maximum_total_current_a) => update({ maximum_total_current_a })}
        />
        <NumberField
          label={`FP da central de ${name}`}
          value={central.power_factor}
          onChange={(power_factor) => update({ power_factor })}
          ratio
        />
        <label className="md:col-span-2">
          Fonte do fabricante da central de {name}
          <input
            maxLength={200}
            value={central.source ?? ''}
            onChange={(e) => update({ source: e.target.value || null })}
          />
        </label>
      </div>
    );
  }
  if (value.group === 'd7') {
    const special = value.special ?? {};
    const update = (patch: Partial<NonNullable<Classification['special']>>) =>
      onChange({ special: { ...special, ...patch } });
    return (
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <p className="text-xs muted md:col-span-2">
          Dados elétricos absorvidos da rede, por unidade; não potência de saída. A ligação V-V
          invertida de solda tem potência duplicada para demanda (§9.1, nota VII). Solda
          motor-gerador pertence a d6.
        </p>
        <label>
          Tipo de equipamento especial de {name}
          <select
            value={special.equipment_type ?? ''}
            onChange={(e) =>
              update({ equipment_type: (e.target.value || null) as typeof special.equipment_type })
            }
          >
            <option value="">Confirmar tipo</option>
            <option value="arc_welder">Solda a arco com transformador</option>
            <option value="resistance_welder">Solda a resistência</option>
            <option value="x_ray">Raios-X</option>
            <option value="galvanization">Galvanização</option>
          </select>
        </label>
        <label>
          Ligação de {name}
          <select
            value={special.connection ?? ''}
            onChange={(e) =>
              update({ connection: (e.target.value || null) as typeof special.connection })
            }
          >
            <option value="">Confirmar ligação</option>
            <option value="standard">Solda: ligação normal</option>
            <option value="inverted_v_v">Solda: V-V invertida</option>
            <option value="not_applicable">Raios-X/galvanização: não aplicável</option>
          </select>
        </label>
        <NumberField
          label={`Potência elétrica aparente absorvida de ${name} (VA por unidade)`}
          value={special.input_apparent_power_va}
          onChange={(input_apparent_power_va) => update({ input_apparent_power_va })}
        />
        <NumberField
          label={`FP do equipamento especial de ${name}`}
          value={special.power_factor}
          onChange={(power_factor) => update({ power_factor })}
          ratio
        />
        <label className="md:col-span-2">
          Fonte dos dados elétricos e ligação de {name}
          <input
            maxLength={200}
            value={special.source ?? ''}
            onChange={(e) => update({ source: e.target.value || null })}
          />
        </label>
      </div>
    );
  }
  return null;
}
