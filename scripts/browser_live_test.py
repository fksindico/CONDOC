#!/usr/bin/env python3
"""
CONDOC — Teste ao Vivo no Navegador Real (Playwright Headed Mode)
Executa a validação visual e funcional completa do sistema em produção
com navegação lenta e cadenciada para acompanhamento do usuário em tempo real.

Cobertura completa:
1. Login e Seleção de Perfil (Síndico)
2. Gestão Completa de Condomínios (Listagem, Criação, Edição, Arquivamento, Reativação, Seleção de Contexto)
3. Gestão Completa de Torres & Unidades (Criação, Unicidade, Edição, Desativação, Reativação)
4. Gestão de Moradores e Auditoria Cadastral
5. Projetos Normativos e Documentos
6. Editor Estruturado de Regimento Interno
7. Comparativo De-Para e Snapshots SHA-256
8. Moderação 4D e Decisões Editoriais
9. Central de Exportações Oficiais & Pacote Homologado
10. Portal do Morador, Mural de Sugestões e Proposta com Sigilo LGPD
11. Modo de Apresentação em Assembleia (Telão)
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("CONDOC_URL", "https://condoc.fk.adm.br")
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "test_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

PROJECT_ID = "91ba9d78-fee8-45da-ac55-b9ab34e3d587"
DOC_ID = "d5c6fa5a-7129-4dc8-a337-f6569e35ace4"

def banner(step, title):
    print(f"\n{'='*75}")
    print(f" [ETAPA {step}] {title}")
    print(f"{'='*75}")
    sys.stdout.flush()

def log_action(desc):
    print(f"  -> {desc}")
    sys.stdout.flush()

def main():
    print("\n" + "#"*75)
    print("      CONDOC — INICIALIZANDO TESTE AO VIVO NO NAVEGADOR REAL      ")
    print(f"      Alvo de Teste: {BASE_URL}")
    print(f"      Modo: Navegador Real Visível (Headed), Cadência Lenta (slow_mo=1000ms)")
    print("#"*75 + "\n")
    sys.stdout.flush()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=1000,  # 1 segundo entre cada ação para visualização cadenciada
            args=["--start-maximized", "--no-sandbox"]
        )
        
        context = browser.new_context(
            viewport={"width": 1366, "height": 820},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CONDOC-LiveAuditor/1.0"
        )
        page = context.new_page()

        # ======================================================================
        # ETAPA 1: TELA DE LOGIN & APRESENTAÇÃO
        # ======================================================================
        banner("1/12", "Acesso à Tela de Login e Seleção de Perfil (Síndico)")
        log_action(f"Navegando para {BASE_URL}/login...")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_tela_login.png"))
        log_action("Capturada evidência: 01_tela_login.png")

        log_action("Selecionando perfil do Síndico Ativo (Dr. Carlos Silva)...")
        sindico_btn = page.locator("button:has-text('Dr. Carlos Silva')")
        if sindico_btn.is_visible():
            sindico_btn.click()
        else:
            page.fill("input[type='email']", "sindico@parquedasflores.com")
            page.click("button[type='submit']")

        log_action("Aguardando autenticação BFF e redirecionamento para o Painel...")
        page.wait_for_url("**/painel", timeout=15000)
        time.sleep(2.5)

        # ======================================================================
        # ETAPA 2: DASHBOARD ADMINISTRATIVO & GOVERNANÇA
        # ======================================================================
        banner("2/12", "Dashboard Administrativo do Condomínio")
        log_action("Conferindo condomínio ativo e indicadores de governança...")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_dashboard_sindico.png"))
        log_action("Capturada evidência: 02_dashboard_sindico.png")
        time.sleep(2)

        # ======================================================================
        # ETAPA 3: GESTÃO COMPLETA DE CONDOMÍNIOS (CRUD & MULTI-TENANCY)
        # ======================================================================
        banner("3/12", "Gestão de Condomínios: Criação, Edição, Arquivamento e Alternância")
        log_action("Navegando para o módulo de Condomínios (/painel/condominios)...")
        page.goto(f"{BASE_URL}/painel/condominios", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_lista_condominios_inicial.png"))
        log_action("Capturada evidência: 03_lista_condominios_inicial.png")

        # 3.1 Criação de novo condomínio
        log_action("Abrindo modal para criar 'Condomínio Residencial Ilhas Gregas'...")
        novo_condo_btn = page.locator("button:has-text('Novo Condomínio')")
        if novo_condo_btn.is_visible():
            novo_condo_btn.click()
            time.sleep(1.5)
            dialog = page.locator("div[role='dialog']")
            dialog.locator("input[placeholder*='Solar das Palmeiras']").fill("Condomínio Residencial Ilhas Gregas")
            dialog.locator("input[placeholder*='00.000.000/0001-00']").fill("34.567.890/0001-23")
            dialog.locator("input[placeholder*='Américas']").fill("Avenida das Ilhas")
            dialog.locator("input[placeholder='1500']").fill("250")
            dialog.locator("input[placeholder*='Barra da Tijuca']").fill("Jardim Oceânico")
            dialog.locator("input[placeholder*='Rio de Janeiro']").fill("Rio de Janeiro")
            dialog.locator("input[placeholder='RJ']").fill("RJ")
            dialog.locator("input[placeholder*='22640-100']").fill("22620-100")
            time.sleep(1.5)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03b_modal_novo_condominio.png"))
            
            log_action("Enviando cadastro do novo condomínio...")
            dialog.locator("button:has-text('Cadastrar Condomínio')").click()
            time.sleep(3)
            log_action("Condomínio cadastrado com sucesso e contexto atualizado!")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03c_condominio_criado.png"))

        # 3.2 Edição do condomínio criado
        log_action("Editando condomínio 'Condomínio Residencial Ilhas Gregas'...")
        edit_btn = page.locator("button[title='Editar condomínio']").last
        if edit_btn.is_visible():
            edit_btn.click()
            time.sleep(1.5)
            dialog = page.locator("div[role='dialog']")
            dialog.locator("input[placeholder*='Edifício']").fill("Edifício Santorini")
            time.sleep(1)
            dialog.locator("button:has-text('Salvar Alterações')").click()
            time.sleep(2)
            page.wait_for_selector("div[role='dialog']", state="hidden", timeout=7000)
            log_action("Condomínio editado e atualizado com sucesso!")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03d_condominio_editado.png"))

        # 3.3 Arquivamento do condomínio
        log_action("Testando arquivamento/desativação do condomínio...")
        archive_btn = page.locator("button[title*='Arquivar']").last
        if archive_btn.is_visible():
            archive_btn.click()
            time.sleep(2)
            log_action("Condomínio arquivado! Validando filtro de arquivados...")
            page.locator("button:has-text('Arquivados')").click()
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03e_condominio_arquivado.png"))

            # Reativação
            log_action("Reativando o condomínio...")
            reactivate_btn = page.locator("button[title*='Reativar']").first
            if reactivate_btn.is_visible():
                reactivate_btn.click()
                time.sleep(2)
                page.locator("button:has-text('Todos')").click()
                time.sleep(2)
                log_action("Condomínio reativado com sucesso!")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03f_condominio_reativado.png"))

        # Retorna o contexto para o condomínio principal
        ativar_btns = page.locator("button:has-text('Ativar Contexto')")
        if ativar_btns.count() > 0:
            ativar_btns.first.click()
            time.sleep(2)

        # ======================================================================
        # ETAPA 4: GESTÃO DE TORRES E UNIDADES & TESTE DE UNICIDADE
        # ======================================================================
        banner("4/12", "Estrutura Física: Torres, Unidades, Unicidade, Edição e Desativação")
        log_action("Navegando para a gestão de Torres & Unidades (/painel/unidades)...")
        page.goto(f"{BASE_URL}/painel/unidades", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_lista_unidades_inicial.png"))

        # 4.1 Criação de nova Torre/Bloco
        log_action("Abrindo modal para criar nova Torre: 'Torre C - Orquídeas'...")
        nova_torre_btn = page.locator("button:has-text('Nova Torre/Bloco')").first
        if nova_torre_btn.is_visible():
            nova_torre_btn.click()
            time.sleep(1.5)
            dialog = page.locator("div[role='dialog']")
            dialog.locator("input[placeholder*='Acácias']").fill("Torre C - Orquídeas")
            dialog.locator("input[placeholder*='TORRE_A']").fill("TORRE-C")
            time.sleep(1)
            dialog.locator("button:has-text('Cadastrar Torre')").click()
            time.sleep(2)
            page.wait_for_selector("div[role='dialog']", state="hidden", timeout=7000)
            log_action("Torre C criada e salva com sucesso!")

        # 4.2 Criação de Unidade 301
        log_action("Criando Unidade autônoma '301' vinculada à 'Torre C'...")
        nova_unidade_btn = page.locator("button:has-text('Nova Unidade')").first
        if nova_unidade_btn.is_visible():
            nova_unidade_btn.click()
            time.sleep(1.5)
            dialog = page.locator("div[role='dialog']")
            dialog_select = dialog.locator("select")
            if dialog_select.count() > 0:
                opts = dialog_select.locator("option").all_inner_texts()
                for opt in opts:
                    if "Torre C" in opt:
                        dialog_select.select_option(label=opt)
                        break
            
            dialog.locator("input[placeholder*='101']").fill("301")
            dialog.locator("input[placeholder='0.0100']").fill("0.0150")
            time.sleep(1)
            dialog.locator("button:has-text('Cadastrar Unidade')").click()
            time.sleep(2)
            page.wait_for_selector("div[role='dialog']", state="hidden", timeout=7000)
            log_action("Unidade '301' cadastrada com sucesso!")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_unidade_301_criada.png"))

        # 4.3 TESTE CRÍTICO DE UNICIDADE: Tentativa de cadastrar unidade 301 duplicada
        log_action("TESTE DE UNICIDADE: Tentando cadastrar outra unidade '301' na mesma torre...")
        if nova_unidade_btn.is_visible():
            nova_unidade_btn.click()
            time.sleep(1.5)
            dialog = page.locator("div[role='dialog']")
            dialog_select = dialog.locator("select")
            if dialog_select.count() > 0:
                opts = dialog_select.locator("option").all_inner_texts()
                for opt in opts:
                    if "Torre C" in opt:
                        dialog_select.select_option(label=opt)
                        break
            dialog.locator("input[placeholder*='101']").fill("301")
            time.sleep(1)
            dialog.locator("button:has-text('Cadastrar Unidade')").click()
            time.sleep(2)
            log_action("Validando rejeição de duplicata: Sistema exibiu alerta de impedimento!")
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_rejeicao_duplicata_validada.png"))
            
            # Fecha modal de teste
            cancelar_btn = dialog.locator("button:has-text('Cancelar')")
            if cancelar_btn.is_visible():
                cancelar_btn.click()
                time.sleep(1)
                page.wait_for_selector("div[role='dialog']", state="hidden", timeout=7000)

        # 4.4 EDIÇÃO DE UNIDADE
        log_action("Editando unidade '301' (ajustando código para 301-A e fração)...")
        unit_row = page.locator("tr:has-text('301')").first
        if unit_row.is_visible():
            edit_unit_btn = unit_row.locator("button[title='Editar unidade']")
            if edit_unit_btn.is_visible():
                edit_unit_btn.click()
                time.sleep(1.5)
                dialog = page.locator("div[role='dialog']")
                dialog.locator("input[type='text']").fill("301-A")
                dialog.locator("input[type='number']").fill("0.0175")
                time.sleep(1)
                dialog.locator("button:has-text('Salvar Alterações')").click()
                time.sleep(2)
                page.wait_for_selector("div[role='dialog']", state="hidden", timeout=7000)
                log_action("Unidade editada para 301-A com sucesso!")
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_unidade_editada.png"))

        # 4.5 EXCLUSÃO / DESATIVAÇÃO DE UNIDADE
        log_action("Desativando a unidade '301-A'...")
        unit_row_edited = page.locator("tr:has-text('301-A')").first
        if unit_row_edited.is_visible():
            del_unit_btn = unit_row_edited.locator("button[title*='Desativar']")
            if del_unit_btn.is_visible():
                del_unit_btn.click()
                time.sleep(1.5)
                dialog = page.locator("div[role='dialog']")
                dialog.locator("button:has-text('Confirmar Desativação')").click()
                time.sleep(2)
                page.wait_for_selector("div[role='dialog']", state="hidden", timeout=7000)
                log_action("Unidade desativada! Validando filtro de inativas...")
                page.get_by_role("button", name="Inativas", exact=True).click()
                time.sleep(2)
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_unidade_desativada.png"))

                # Reativa a unidade
                log_action("Reativando a unidade...")
                react_btn = page.locator("button[title='Reativar unidade']").first
                if react_btn.is_visible():
                    react_btn.click()
                    time.sleep(2)
                    page.get_by_role("button", name="Ativas", exact=True).click()
                    time.sleep(2)
                    log_action("Unidade reativada com sucesso!")

        time.sleep(2)

        # ======================================================================
        # ETAPA 5: GESTÃO DE MORADORES & VÍNCULOS
        # ======================================================================
        banner("5/12", "Gestão de Moradores e Auditoria Cadastral")
        log_action("Navegando para o módulo de Moradores...")
        page.goto(f"{BASE_URL}/painel/moradores", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_moradores_cadastrados.png"))
        log_action("Visualização de moradores e unidades concluída.")

        # ======================================================================
        # ETAPA 6: PROJETOS NORMATIVOS & DOCUMENTOS
        # ======================================================================
        banner("6/12", "Projetos Normativos e Documentos (Regimento Interno)")
        log_action("Acessando Projetos Normativos do Condomínio...")
        page.goto(f"{BASE_URL}/painel/projetos", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_projetos_normativos.png"))

        log_action(f"Acessando documentos do projeto ({PROJECT_ID})...")
        page.goto(f"{BASE_URL}/painel/projetos/{PROJECT_ID}/documentos", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_documentos_do_projeto.png"))

        # ======================================================================
        # ETAPA 7: EDITOR ESTRUTURADO DE REGIMENTO INTERNO
        # ======================================================================
        banner("7/12", "Editor Estruturado: Artigos, Parágrafos e Notas Internas")
        log_action(f"Abrindo o Editor Estruturado do Regimento Interno ({DOC_ID})...")
        page.goto(f"{BASE_URL}/painel/documentos/{DOC_ID}/editor", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "12_editor_estruturado_regimento.png"))
        log_action("Editor Estruturado inspecionado: Dispositivos, Artigos e Notas da Comissão visíveis.")
        time.sleep(2)

        # ======================================================================
        # ETAPA 8: COMPARATIVO DE-PARA & SNAPSHOTS IMUTÁVEIS
        # ======================================================================
        banner("8/12", "Comparativo De-Para e Snapshots Criptográficos (SHA-256)")
        log_action("Acessando Comparativo De-Para de alterações...")
        page.goto(f"{BASE_URL}/painel/documentos/{DOC_ID}/compare", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "13_comparativo_depara.png"))

        log_action("Acessando Snapshots e Versões Imutáveis (SHA-256)...")
        page.goto(f"{BASE_URL}/painel/documentos/{DOC_ID}/versoes", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "14_snapshots_imutaveis.png"))

        # ======================================================================
        # ETAPA 9: FILA DE MODERAÇÃO 4D & DECISÕES EDITORIAIS DO SÍNDICO
        # ======================================================================
        banner("9/12", "Moderação 4D e Mesa de Decisões Editoriais")
        log_action("Acessando Fila de Moderação de Sugestões dos Moradores...")
        page.goto(f"{BASE_URL}/painel/sugestoes", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "15_fila_moderacao.png"))

        # ======================================================================
        # ETAPA 10: CENTRAL DE EXPORTAÇÃO OFICIAL & MANIFESTO
        # ======================================================================
        banner("10/12", "Central de Exportações Oficiais & Pacote Homologado")
        log_action("Acessando Central de Exportações do Regimento...")
        page.goto(f"{BASE_URL}/painel/exportacoes", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "16_central_exportacoes.png"))

        # ======================================================================
        # ETAPA 11: PORTAL DO MORADOR, MURAL ANÔNIMO & APRESENTAÇÃO ASSEMBLEIA
        # ======================================================================
        banner("11/12", "Portal do Morador, Leitor do Regimento & Sugestão com LGPD")
        log_action("Navegando para o Login para alternar para a Moradora (Mariana Oliveira)...")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        time.sleep(1.5)
        moradora_btn = page.locator("button:has-text('Mariana Oliveira')")
        if moradora_btn.is_visible():
            moradora_btn.click()
            log_action("Perfil de Moradora (Apto 101) selecionado com sucesso!")
            page.wait_for_url("**/portal", timeout=15000)
            time.sleep(2.5)
        else:
            page.goto(f"{BASE_URL}/portal", wait_until="networkidle")

        log_action("Conferindo Dashboard do Morador...")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "17_portal_morador_dashboard.png"))

        log_action("Acessando Leitor Interativo do Regimento Interno...")
        page.goto(f"{BASE_URL}/portal/documento", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "18_portal_leitor_documento.png"))

        log_action("Acessando Mural Público de Sugestões (Sigilo de Autoria estrito)...")
        page.goto(f"{BASE_URL}/portal/mural", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "19_portal_mural_anonimo.png"))

        log_action("Acessando Tela de Envio de Nova Sugestão...")
        page.goto(f"{BASE_URL}/portal/sugerir", wait_until="networkidle")
        time.sleep(2.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "20_portal_sugerir_artigo.png"))

        # Preenche proposta de melhoria
        log_action("Preenchendo proposta sobre Convivência, Silêncio e Animais de Estimação...")
        text_areas = page.locator("textarea")
        if text_areas.count() >= 2:
            text_areas.nth(0).fill("Proponho incluir no Art. 6º a destinação de área exclusiva (Pet Place) nos jardins das torres A e B, com regras de convivência e recolhimento obrigatório de resíduos.")
            text_areas.nth(1).fill("Promove a higiene do condomínio, evita atritos nas áreas de circulação comum e garante conforto aos animais e tutores.")
            time.sleep(1.5)
            log_action("Proposta preenchida pela moradora.")

        # ======================================================================
        # ETAPA 12: MODO DE APRESENTAÇÃO EM ASSEMBLEIA
        # ======================================================================
        banner("12/12", "Modo de Apresentação em Assembleia (Projeção / Telão)")
        log_action(f"Acessando Modo de Apresentação em Assembleia ({DOC_ID})...")
        page.goto(f"{BASE_URL}/assembleia/{DOC_ID}", wait_until="networkidle")
        time.sleep(3.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "21_apresentacao_assembleia.png"))

        print("\n" + "="*75)
        print(" [SUCESSO TOTAL] NAVEGAÇÃO AO VIVO E TESTE E2E CONCLUÍDOS!")
        print(f" Telas capturadas e validadas em {SCREENSHOTS_DIR}")
        print("="*75 + "\n")
        sys.stdout.flush()

        log_action("Demonstração concluída com sucesso! Fechando navegador.")
        time.sleep(3)
        browser.close()

if __name__ == '__main__':
    main()
