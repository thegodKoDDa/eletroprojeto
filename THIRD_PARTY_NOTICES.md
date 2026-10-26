# Componentes de terceiros

A licença ISC do EletroProjeto se aplica ao código original deste repositório.

- A fonte DejaVu Sans Mono incorporada aos relatórios mantém a licença em [FONT-LICENSE.txt](backend/app/reports/assets/FONT-LICENSE.txt).
- Dependências Python e JavaScript mantêm suas próprias licenças. Versões são identificadas em `backend/requirements.lock` e `frontend/package-lock.json`; pacotes instalados devem conservar seus avisos de licença. A imagem usa o subconjunto `backend/requirements-runtime.lock` e conserva avisos Node/npm em `/app/licenses`, além dos metadados/licenças dos pacotes Python. Ferramentas opcionais de ingestão/OCR não são incluídas na imagem.
- Normas, manuais, documentos da biblioteca e coletas territoriais locais não estão incluídos no ZIP ou na imagem Docker. Referenciá-los não transfere licença de redistribuição nem declara validação integral.

Fontes e condições dos procedimentos estão em [docs/standards.md](docs/standards.md).
