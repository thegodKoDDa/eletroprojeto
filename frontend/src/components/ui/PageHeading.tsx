import type { ReactNode } from 'react';

export function PageHeading({
  title,
  eyebrow,
  description,
  id,
}: {
  title: string;
  eyebrow: string;
  description: ReactNode;
  id?: string;
}) {
  return (
    <div className="page-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h1 id={id} data-workspace-heading tabIndex={-1}>
        {title}
      </h1>
      <p className="page-description">{description}</p>
    </div>
  );
}
