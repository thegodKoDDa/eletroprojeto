export function exportFilename(name: string, extension: 'pdf' | 'json') {
  const base =
    name
      .replace(/[\u0000-\u001f\u007f/\\:*?"<>|]/g, '_')
      .trim()
      .replace(/^[. ]+|[. ]+$/g, '')
      .slice(0, 120) || 'Projeto sem nome';
  return `${base}.${extension}`;
}
