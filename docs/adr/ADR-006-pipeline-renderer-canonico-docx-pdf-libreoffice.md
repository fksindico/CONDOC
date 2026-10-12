# ADR-006: Pipeline de Renderização Canônica Local (DOCX + PDF via python-docx e LibreOffice Headless)

## Status
Aprovado

## Data
2026-10-12

## Contexto
A plataforma CONDOC precisa exportar e apresentar documentos normativos oficiais (Convenções e Regimentos Internos) com alta fidelidade tipográfica e formatação idêntica em dois formatos essenciais:
1. **DOCX (Microsoft Word / OOXML)**: para revisão legislativa, edições controladas pelo síndico e compatibilidade com advogados e cartórios.
2. **PDF oficial assinado e selado**: para distribuição aos condôminos, registro formal e consulta pública.

No mercado, soluções comuns utilizam motores paralelos e não equivalentes (por exemplo, exportar HTML para WeasyPrint/ReportLab e paralelamente criar um DOCX via templates simples). Essa abordagem gera divergências inaceitáveis entre o que o usuário vê no PDF e o que está no DOCX (quebras de página diferentes, números de linha divergentes, cabeçalhos desencontrados). Além disso, conversores comerciais em nuvem (SaaS) violam a soberania e a privacidade do CONDOC.

## Decisão
1. **Pipeline Canônico Unificado de Fonte Única**:
   - O documento oficial é gerado primeiramente como um arquivo DOCX padrão OOXML pelo Core backend utilizando `python-docx` com personalização direta de tags XML (`w:pPr`, `w:rPr`, `w:footnote`, `w:tblPr`, etc.).
   - Em seguida, o arquivo DOCX finalizado é processado localmente em ambiente isolado via LibreOffice Headless (`soffice --headless --convert-to pdf`).
   - O PDF gerado provém **estritamente e diretamente do DOCX final**. Nenhum PDF paralelo (via HTML/CSS ou canvas) é gerado ou aceito como artefato oficial.
2. **Isolamento de Processo e Segurança**:
   - Cada renderização roda com diretório temporário exclusivo e perfil de usuário efêmero do LibreOffice (`-env:UserInstallation=file:///tmp/libreoffice_job_UUID`), evitando concorrência ou poluição entre tenants.
   - Bloqueio completo de acesso à rede durante a renderização: nenhum recurso externo, macro, script ou fonte remota é carregado em tempo de execução.
3. **Resolução Completa de Elementos de Documento**:
   - Campos de cabeçalho e rodapé (nome do condomínio, número de página `PAGE`, total de páginas `NUMPAGES`).
   - Primeira página diferenciada com cabeçalho/rodapé limpos na folha de rosto/identificação.
   - Notas de rodapé reais (`w:footnoteReference`) mapeadas no rodapé de cada página pelo motor tipográfico.
   - Sumário dinâmico e tabelas com linhas de cabeçalho repetidas em páginas subsequentes (`w:tblHeader`).
4. **Manifesto Criptográfico e Selagem**:
   - Cada par de artefatos (DOCX + PDF) é vinculado a um snapshot imutável (`DocumentSnapshot`).
   - São calculados os hashes SHA-256 de ambos os arquivos, armazenados em `ExportArtifact` com manifesto completo de versão, fontes utilizadas e timestamp determinístico.

## Consequências
- **Positivas**:
  - Paridade visual e semântica de 100% entre o DOCX e o PDF entregues.
  - Zero dependência de serviços externos SaaS de conversão de documentos.
  - Totalmente executável na arquitetura de duas LXCs (LXC 1 para Aplicação/Render e LXC 2 para Banco de Dados).
- **Compromissos**:
  - Requer a presença do binário `libreoffice` instalado no container de aplicação/renderizador.
