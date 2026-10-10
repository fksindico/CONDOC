# Prompt — Fase 7: Preservação e publicação de conteúdo

Leia AGENTS.md, core/AGENTS.md e docs/prd/PRD_Mestre_v3.md integralmente. Não amplie o escopo. Não implemente votação, apuração ou quórum.

## Dependências
6.

Antes de iniciar confirme que as dependências foram concluídas com evidência; se não, registre bloqueio. Para a fase 9, a execução é opcional e exige decisão específica; não pertence ao MVP.

## Objetivo e entregas
Final de trabalho, leitura autorizada, pacote externo, relatório interno, JSON/manifesto, arquivo informativo externo, retenção/exportação.

## Execução em loop
1. Confirme ambiente de desenvolvimento, recursos disponíveis e autorização. Use dados fictícios e sandbox.
2. Inventarie o repositório e classifique requisitos como atendidos/parciais/ausentes. Preserve código compatível.
3. Atualize gap analysis, ADRs necessários e plano de tarefas desta fase.
4. Implemente incrementos, migrations SQL autoritativas e contratos compatíveis; não crie autenticação paralela.
5. Descubra comandos reais de lint/tipos/testes do repo e execute os pertinentes. Não trate scripts descritos no PRD como se já estivessem implementados.
6. Corrija falhas sem desativar segurança. Após cinco tentativas não convergentes da mesma falha registre evidência e bloqueio.
7. Atualize a matriz de rastreabilidade, docs e status. Não declare teste executado sem resultado real.

## Gate
Recuperar estrutura exportada, separar identidade do público, nenhuma deliberação formal introduzida.

Critérios de referência: CA-41, CA-42, CA-45; UI-33, UI-38.

## Restrições
Sem mensagens reais, acesso a dados reais fora do escopo, produção, mudanças destrutivas, DNS ou credenciais externas sem autorização específica. Antes de risco em ambiente existente, backup/snapshot e rollback. Não inferir permissão pela disponibilidade de shell.

## Relatório de saída
Entregue: resumo, arquivos alterados, migrations, critérios implementados, comandos/resultados dos testes, evidências, riscos/pendências, verificações de tenant/PII/escopo e condição para próxima fase. Se mock, diga que é mock; não conte como homologação da integração.
