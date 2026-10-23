'use client';
import { useState } from 'react';
import type { CatalogItem, Environment } from '@/lib/api';

export function RoomEquipmentPicker({
  room,
  choices,
  onAdd,
}: {
  room: Environment;
  choices: CatalogItem[];
  onAdd: (item: CatalogItem) => void;
}) {
  return <EquipmentOptions key={room.type} room={room} choices={choices} onAdd={onAdd} />;
}

function EquipmentOptions({
  room,
  choices,
  onAdd,
}: {
  room: Environment;
  choices: CatalogItem[];
  onAdd: (item: CatalogItem) => void;
}) {
  const [all, setAll] = useState(false);
  const relevant = choices.filter(
    (item) =>
      all ||
      !item.recommended_environments?.length ||
      item.recommended_environments.includes(room.type),
  );
  return (
    <div className="min-w-0 max-w-sm flex-1">
      <select
        aria-label={`Adicionar equipamento em ${room.name}`}
        value=""
        onChange={(e) => {
          const template = choices.find((item) => item.id === e.target.value);
          if (template) onAdd(template);
        }}
      >
        <option value="">Adicionar equipamento…</option>
        {relevant.map((item) => (
          <option key={item.id} value={item.id}>
            {item.selection_name ?? item.name}
          </option>
        ))}
      </select>
      <button
        className="picker-toggle"
        aria-pressed={all}
        onClick={() => setAll((value) => !value)}
      >
        {all ? 'Mostrar sugestões do ambiente' : 'Buscar em todos os equipamentos'}
      </button>
    </div>
  );
}
