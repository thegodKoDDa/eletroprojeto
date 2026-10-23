import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';
import { RoomEquipmentPicker } from '@/components/equipment/RoomEquipmentPicker';
import type { CatalogItem, Environment } from '@/lib/api';
import catalog from './fixtures/catalog.json';
import { selectionCatalog } from '@/lib/equipment';
afterEach(cleanup);
const choices = selectionCatalog(catalog as CatalogItem[]);
test.each(['bedroom', 'kitchen', 'living', 'laundry', 'office', 'bathroom', 'other'] as const)(
  'recommendations and general search for %s',
  (type) => {
    const room = { name: 'Ambiente', type, id: 'room' } as Environment;
    const { rerender } = render(
      <RoomEquipmentPicker room={room} choices={choices} onAdd={() => {}} />,
    );
    const shower = () =>
      within(screen.getByRole('combobox')).queryByRole('option', { name: 'Chuveiro elétrico' });
    if (['bathroom', 'other'].includes(type)) expect(shower()).not.toBeNull();
    else expect(shower()).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Buscar em todos os equipamentos' }));
    expect(shower()).not.toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Mostrar sugestões do ambiente' }));
    rerender(
      <RoomEquipmentPicker
        room={{ ...room, type: 'bathroom' }}
        choices={choices}
        onAdd={() => {}}
      />,
    );
    expect(shower()).not.toBeNull();
  },
);
