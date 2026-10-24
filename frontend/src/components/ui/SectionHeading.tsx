import type { ReactNode, Ref } from 'react';

export function SectionHeading({
  eyebrow,
  title,
  description,
  id,
  headingRef,
  tabIndex,
}: {
  eyebrow: string;
  title: string;
  description?: ReactNode;
  id?: string;
  headingRef?: Ref<HTMLHeadingElement>;
  tabIndex?: number;
}) {
  return (
    <div className="section-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h2 id={id} ref={headingRef} tabIndex={tabIndex}>
        {title}
      </h2>
      {description && <p className="section-description">{description}</p>}
    </div>
  );
}
