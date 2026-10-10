# AGENTS.md — Core e domínio

Leia /AGENTS.md e docs/prd/PRD_Mestre_v3.md. Estas regras complementam e não relaxam o escopo.

## Invariantes

1. Conta Auth, perfil por condomínio, vínculo por unidade e participante da campanha são diferentes.
2. Validação pertence ao vínculo; contato confirmado não comprova residência.
3. Análise, decisão editorial, publicação e incorporação são independentes.
4. Só síndico ativo publica versão específica.
5. Snapshot resolve revisões/estrutura exatas, nunca latest.
6. UUID do dispositivo não é número; origem é muitos-para-muitos.
7. Novo item não inventa origem; excluído permanece no histórico.
8. Concordância é consultiva e por versão, sem peso/quórum/voto.
9. Troca de vínculo não reatribui fatos anteriores.
10. JWT ainda válido não supera suspensão/role local revogado.

## Serviços, transações e adapters

Controllers validam e chamam application services. Domínio expressa invariantes. SDK, banco e Storage em infrastructure. DTO público distinto e sem autoria. Contexto RLS parametrizado local à transação, só após verificação do Core. Task revalida ator/tenant/recurso.

Transação para importação selecionada, resgate/limite, vínculo/evento, publicação/decisão, acordo/evento, incorporação/revisão/vínculo e snapshot/itens. Concorrência retorna conflito sem sobrescrita.

Models managed=False refletem SQL app versionado. Sem Auth paralelo, schema interno Supabase alterado manualmente ou role elevada em operação normal.

## Testes

Toda alteração relevante possui caso permitido e negado. Vincular CA/UI/V21/AR e evidência. Testar pool entre tenants, Storage com URL expirada e payload público sem identity IDs. Mock não equivale a integração Cloud/selfhost. Logs/erros nunca enumeram conta de outro condomínio.
