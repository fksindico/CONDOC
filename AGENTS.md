# AGENTS.md — Instruções mandatórias para agentes de desenvolvimento

## Missão e fonte de verdade

Construir a plataforma de gestão de criação/modificação de Convenção e Regimento Interno, preservando rastreabilidade e privacidade. Ler docs/prd/PRD_Mestre_v3.md e docs/prd/PRD_Complementar_ED_OSS_2_0.md inteiros antes de implementar. Documentos de API/UI e fases são extrações; em conflito, o PRD mestre e as diretrizes mandatórias de self-hosted/open source prevalecem.

Respeitar políticas da ferramenta e autorizações do ambiente. Ordem interna do projeto: PRD vigente, AGENTS raiz, AGENTS local e ADRs compatíveis. Instrução local só adiciona detalhe; não pode relaxar proibição global. Não alegar que estes arquivos sobrepõem instruções de segurança da ferramenta.

## Proibições

- Nenhum voto, eleição, apuração, quórum, peso eleitoral ou aprovação vinculante.
- Não chamar concordância de aprovação/voto.
- Proibição estrita de pacotes @tiptap-pro, registros npm privados ou serviços externos SaaS de conversão/exportação.
- Não publicar por automação ou admin sem papel de síndico ativo.
- Não expor autoria a moradores, conselho, comissão ou jurídico sem papel administrativo explicitamente autorizado.
- Não validar residência por posse de link ou mera confirmação de e-mail.
- Não criar credencial/enviar convite ao importar cadastro.
- Não transferir concordância em mudança substancial.
- Não sobrescrever base/snapshot ou apagar histórico.
- Não acrescentar features para aproveitar biblioteca.

## Arquitetura e organização

React/TS/Vite/Tiptap Core (100% OSS MIT); Core Django/DRF; Supabase PostgreSQL/Auth/Storage; Celery/Redis; OCR/conversão isolados. Pipeline de renderização canônica local (python-docx + LibreOffice headless gerando par DOCX e PDF derivado idêntico). Auth Supabase único. Sem credenciais Django paralelas. BFF com cookie seguro; tabelas de negócio não diretamente acessíveis pelo browser.

SQL em supabase/migrations é fonte única; models domínio managed=False. Sem migrations Django criando as mesmas tabelas. Role de runtime limitado, separado de migration; contexto RLS local à transação após autenticação/autorização. Segredo administrativo não é solução de erro de política e ignora RLS.

Manter apps/web, core/domain, core/application, core/infrastructure, workers, supabase, infra, scripts e docs. Domínio não importa SDK. Controladores/serializers não contêm todas as regras de negócio. Arquivos via adaptador, não disco comum presumido. Hosts/URLs/segredos configuráveis. Não depender de mesma VPS.

## Privacidade

Serializer público omite identidade e IDs correlacionáveis. Contagens ocultas não enviadas. Identidade buscada só com permissão e auditada. Anexo privado. Logs sem token, senha, chave ou payload pessoal inteiro. Nenhum segredo em VITE_, frontend ou git. Confirmação de export pessoal e envio real obrigatórias.

## Desenvolvimento em loop

1. Ler documentação, inventariar código e ambiente.
2. Produzir gap analysis, matriz requisito→implementação→teste e ADRs.
3. Escolher fase autorizada e verificar dependências.
4. Implementar pequeno incremento compatível com contratos.
5. Rodar lint/types/unit/integration/E2E pertinentes e registrar comando/resultado.
6. Corrigir e repetir; atualizar docs/estado, sem ocultar falha.
7. Após cinco tentativas não convergentes do mesmo problema, relatar causa/evidência/bloqueio.

Autonomia só em desenvolvimento autorizado, com dados fictícios/sandbox. Não inferir ambiente seguro pelo hostname. Não desativar testes, RLS ou checks para obter verde. Mock deve ser explicitamente rotulado e não conta como integração real.

## Autorizações específicas

Exigir autorização para produção, comunicações reais, dados pessoais reais fora do escopo concedido, destruição/reescrita irreversível, reset remoto, remoção de volume, rotação produtiva, DNS/firewall/proxy/Cloudflare/plano externo e restore/migração operacional.

Antes de alteração destrutiva existente, pedir backup/snapshot e rollback. Shell disponível não autoriza tudo. Nunca contornar confirmação exigida pela ferramenta.

## Instaladores e ambientes

Scripts são implementados por fase, não presumidos prontos. Rerun preserva volumes/dados/segredos; não seedar produção. Detectar instalação existente e parar antes de overwrite. Preflight deve conferir dependências, portas, URLs, credenciais limitadas e versão.

Não criar projeto Cloud/DNS/plano SMTP automaticamente. Não divulgar segredos em stdout. Testar Cloud/selfhost e componentes separados; declarar não homologadas as plataformas sem teste.

## Testes e entrega

Testar tenant cruzado, identidade, síndico exclusivo, importação idempotente, convite e conta separados, contato sem residência presumida, versão/retirada de concordância, snapshot imutável, export limpo, Storage privado, contexto em pool, instalação repetida e restauração.

Não inventar comando executado, arquivo existente, deploy, suporte ou teste aprovado. Entregar alterações, evidências, pendências/riscos e próxima fase. Build não é homologação. Sem copiar OSS sem origem/commit/licença/avaliação. Dependências fixadas.

## Atualizações deste arquivo

Mudança material precisa atualizar PRD/ADR, instruções e testes; não manter regras divergentes em README e AGENTS. Para ferramentas com outro arquivo de instruções, usar encaminhamento ou conteúdo derivado, sem fonte normativa concorrente.
