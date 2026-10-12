# ADR-007: Modelo de Dados DB-1.0 para Núcleo Normativo, Dispositivos, Regiões e Notas

## Status
Aprovado

## Data
2026-10-12

## Contexto
O PRD Mestre e o complemento ED-OSS-2.0 exigem um núcleo documental robusto e auditável que trate dispositivos legais como entidades de primeira classe com identidades estáveis, histórico append-only de revisões, concorrência otimista, notas de rodapé documentais separadas de anotações internas privadas e snapshots imutáveis.

## Decisão
1. **Identidade Estável de Dispositivos (`DocumentNode` / `Provision`)**:
   - Cada dispositivo possui um UUID estável permanente que não se altera durante renumerações ou movimentações de hierarquia.
   - O conteúdo e propriedades residem em revisões imutáveis (`NodeRevision` / `ProvisionRevision`), com numeração incremental por dispositivo.
2. **Concorrência Otimista (ETag)**:
   - Toda atualização exige a passagem do `ETag` da revisão anterior conhecida no cabeçalho `If-Match`. Se houver modificação por outro usuário, o sistema rejeita com HTTP 409 Conflito sem sobrescrever dados.
3. **Segregação Estrita de Notas**:
   - **Notas Documentais (`DocumentNote` / `NoteRevision`)**: pertencem ao documento público ou minuta (Footnotes/Endnotes), possuem referência no texto e são impressas no documento final.
   - **Anotações Internas (`InternalNote` / `internal_annotations`)**: pertencem ao processo de elaboração privada (visibilidade restrita a síndico, jurídico e comissão), nunca vazando para DTOs públicos, consultas de moradores ou artefatos exportados.
4. **Regiões de Layout e Configurações Versionadas**:
   - Cabeçalhos e rodapés são tratados como `RegionRevision` com estados controlados (`template`, `explicit`, `cleared`) e variantes (`default`, `first`, `odd`, `even`).
   - Perfis de estilo e layout são versionados independentemente do texto em `ConfigurationVersion`.
5. **Snapshots Imutáveis (`DocumentSnapshot`)**:
   - O congelamento de um snapshot fixa o ponteiro de revisão exato de cada nó, nota e região.
   - O hash SHA-256 do conteúdo consolidado é gerado de forma determinística e congelado. Triggers de banco e validações de serviço bloqueiam qualquer alteração ou exclusão subsequente.

## Consequências
- Rastreabilidade legislativa completa (de-para de origem, histórico de revisões).
- Preservação de integridade referencial e auditoria perpétua.
- Conformidade total com a Lei Geral de Proteção de Dados (LGPD) e regras de sigilo editorial do síndico.
