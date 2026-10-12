# AGENTS.md — Subsistema documental CONDOC, ED-OSS-2.0

Leia AGENTS raiz/Core, PRD mestre e docs/prd/PRD_Complementar_ED_OSS_2_0.md. Regras da ferramenta/ambiente sempre respeitadas. Instruções locais não relaxam segurança global.

## Mandatos atuais

Full self-hosted e componentes open source. Não instalar/importar @tiptap-pro, usar registro privado de licença ou enviar documento a conversor SaaS. Tiptap OSS não contém Pages/Conversion/notes Pro: implemente contratos próprios com schema/plugins públicos e renderer local.

Nenhum voto/apuração/quórum funcional. Texto de Convenção pode abordar esses temas. Só síndico publica sugestões; identidade restrita; notas documentais não são observações internas.

## Invariantes

UUID jurídico independe da página/rótulo. Projeção de fluxo não duplica fonte de texto. Caput único primeiro. Renumeração explícita. Corpo/regiões/layout/notas/style pertencem ao snapshot. Sem latest durante task. Modelos possuem placeholders e não são texto jurídico aprovado.

Artigo longo pode continuar; caixa indivisível maior que página exige tratamento. Tabela continua única no JSON; fragmentação visual não é alteração estrutural. Layout live próprio é opcional; editor contínuo+PDF canônico obrigatórios.

DOCX definitivo e PDF dele, pipeline local python-docx/OOXML/UNO. Note reference/map versionados e notas Word reais. Campos/sumário/fontes resolvidos antes de pronto. Público sem comments/deleted/hidden/PII residual. Renderer isolado/sem rede e arquivos privados.

## Execução

Inventário→gap→SBOM/ADR→OSS-F0…F7→testes→evidência. Licença desconhecida não vai a produção. Preserve dados/IDs; migration/rollback antes de substituir Pro. Runtime sem credencial de bypass genérica; tenant/ator também no worker.

Dados fictícios. Sem produção, envio real, dados reais fora do escopo, DNS/Proxmox/destrutivo sem autorização. Após cinco tentativas não convergentes relatar bloqueio. Não desativar testes/políticas para passar. Mock e teste não executado declarados.

Entregar código, docs, SBOM/licenças, testes/exemplares conferidos, manifests e matriz EDOSS. Não declarar exportação fiel por arquivo abrir ou hash existir.
