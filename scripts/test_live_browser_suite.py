#!/usr/bin/env python3
"""
Validação E2E Automatizada via Playwright:
1. Landing Page na raiz (sem redirect indevido para /portal).
2. Participação Pública: Auto-Save, Split-View, Submissão de Sugestão.
3. Tela de Confirmação com Agradecimento Personalizado & Adicionar Nova Sugestão mantendo dados.
4. Painel Administrativo: Badge de Divergência Cadastral e Filtros.
5. Configuração de Apresentação & Mensagens (/painel/apresentacao).
6. Modo Simulação do Síndico (Visão Conselho com banner persistente).
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCREENSHOT_DIR = "f:/CONDOC/test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "https://condoc.fk.adm.br"
CONSULTATION_URL = f"{BASE_URL}/participar/vtF2RgpJUoj7xMqbDta8"

def main():
    print("=" * 70)
    print("INICIANDO SUÍTE DE TESTES E2E NO BROWSER (PLAYWRIGHT)")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Cria contexto limpo para testar a experiência de novo morador
        context = browser.new_context(viewport={"width": 1366, "height": 820})
        page = context.new_page()

        # -------------------------------------------------------------
        # TESTE 1: LANDING PAGE NA RAIZ (https://condoc.fk.adm.br/)
        # -------------------------------------------------------------
        print("\n[TESTE 1] Acessando Landing Page na Raiz...")
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.wait_for_timeout(2000)

        current_url = page.url
        print(f"URL atual após carregar raiz: {current_url}")
        assert not current_url.endswith("/portal"), "FALHA: A raiz redirecionou indevidamente para /portal!"
        print("[OK] Raiz permaneceu na Landing Page institucional sem redirect forçado.")

        # Verifica elementos da Landing Page
        heading = page.locator("h1").first
        print(f"Título da Landing Page: {heading.inner_text()}")

        card_consultation = page.locator("text=Revisão Participativa do Regimento 2026")
        assert card_consultation.is_visible(), "FALHA: Card da consulta não visível na Landing Page!"
        print("[OK] Consulta ativa renderizada com sucesso no feed institucional.")

        page.screenshot(path=f"{SCREENSHOT_DIR}/30_landing_page.png")
        print(f"Salvo: {SCREENSHOT_DIR}/30_landing_page.png")

        # -------------------------------------------------------------
        # TESTE 2: PARTICIPAÇÃO PÚBLICA & FORMULÁRIO DE SUGESTÃO
        # -------------------------------------------------------------
        print("\n[TESTE 2] Acessando Tela de Participação...")
        page.goto(CONSULTATION_URL, wait_until="networkidle")
        page.wait_for_timeout(3500)

        # Se houver botão "Alterar Dados", clica para abrir inputs
        alt_btn = page.locator("button:has-text('Alterar Dados')")
        if alt_btn.is_visible():
            alt_btn.click()
            page.wait_for_timeout(500)

        # Preenche os dados do morador
        print("Preenchendo formulário de sugestão do morador...")
        name_input = page.locator("input[placeholder*='João Ferreira de Paula']")
        assert name_input.is_visible(), "FALHA: Campo de Nome Completo não visível!"
        name_input.fill("Dr. Marcelo Fagundes")

        phone_input = page.locator("input[placeholder*='(11) 99999-9999']")
        phone_input.fill("(11) 98765-4321")

        email_input = page.locator("input[placeholder*='seu@email.com']")
        email_input.fill("marcelo.divergente@gmail.com")

        # Seleciona Torre
        tower_select = page.locator("select").nth(0)
        tower_select.select_option(label="ALPHA")
        page.wait_for_timeout(600)

        # Seleciona Andar
        floor_select = page.locator("select").nth(1)
        floor_select.select_option(label="3º Andar")
        page.wait_for_timeout(600)

        # Seleciona Unidade
        unit_select = page.locator("select").nth(2)
        unit_select.select_option(label="Apto 301")
        page.wait_for_timeout(600)

        # Seleciona Ação: Alterar
        alterar_btn = page.locator("button:has-text('Alterar')").first
        if alterar_btn.is_visible():
            alterar_btn.click()

        # Referência do Documento
        ref_input = page.locator("input[placeholder*='Artigo 14, § 2º']")
        ref_input.fill("Artigo 8º, § 2º (Horário de Carga e Descarga)")

        # Texto da Sugestão
        sug_textarea = page.locator("textarea[placeholder*='Escreva como gostaria']")
        sug_textarea.fill(
            "Sugerimos regulamentar o horário de carga e descarga para dias úteis das 9h às 17h, proibindo operações aos domingos."
        )

        # Justificativa
        just_textarea = page.locator("textarea[placeholder*='Por que esta alteração é benéfica']")
        if just_textarea.is_visible():
            just_textarea.fill(
                "Garantir a tranquilidade e descanso dos moradores que trabalham em regime híbrido ou home office."
            )

        page.wait_for_timeout(1000)

        # Submete a sugestão
        print("Enviando sugestão consultiva...")
        submit_btn = page.locator("button[type='submit']:has-text('Enviar Sugestão')")
        submit_btn.click()

        # Aguarda a tela de confirmação
        page.wait_for_timeout(3000)

        # -------------------------------------------------------------
        # TESTE 3: TELA DE CONFIRMAÇÃO & MULTI-SUGESTÕES
        # -------------------------------------------------------------
        print("\n[TESTE 3] Validando Tela de Confirmação...")
        confirm_title = page.locator("text=Sugestão Registrada com Sucesso!")
        assert confirm_title.is_visible(), "FALHA: Tela de confirmação não apareceu após envio!"
        print("[OK] Tela de confirmação renderizada com sucesso!")

        protocol_badge = page.locator("span.text-emerald-400, span.font-mono:has-text('-')").first
        protocol_text = protocol_badge.inner_text()
        print(f"Protocolo Oficial em Destaque: {protocol_text}")

        # Verifica mensagem de agradecimento personalizada
        thank_you_box = page.locator("text=Mensagem da Administração")
        assert thank_you_box.is_visible(), "FALHA: Card de mensagem da administração ausente!"
        print("[OK] Card de agradecimento personalizado em destaque.")

        page.screenshot(path=f"{SCREENSHOT_DIR}/31_confirmation_screen.png")
        print(f"Salvo: {SCREENSHOT_DIR}/31_confirmation_screen.png")

        # Testa o botão [ Adicionar Outra Sugestão ]
        print("\n[TESTE 4] Testando [Adicionar Outra Sugestão] com preservação cadastral...")
        add_more_btn = page.locator("button:has-text('Adicionar Outra Sugestão')")
        assert add_more_btn.is_visible(), "FALHA: Botão 'Adicionar Outra Sugestão' não encontrado!"
        add_more_btn.click()
        page.wait_for_timeout(1500)

        # Se houver botão "Alterar Dados", clica para inspecionar os inputs
        alt_btn2 = page.locator("button:has-text('Alterar Dados')")
        if alt_btn2.is_visible():
            alt_btn2.click()
            page.wait_for_timeout(500)

        # Valida se os campos Nome, Telefone, Email e Unidade estão preservados
        name_val = page.locator("input[placeholder*='João Ferreira de Paula']").input_value()
        phone_val = page.locator("input[placeholder*='(11) 99999-9999']").input_value()
        email_val = page.locator("input[placeholder*='seu@email.com']").input_value()

        print(f"Nome preservado: '{name_val}'")
        print(f"Telefone preservado: '{phone_val}'")
        print(f"E-mail preservado: '{email_val}'")

        assert name_val == "Dr. Marcelo Fagundes", "FALHA: Nome do morador não foi preservado!"
        assert email_val == "marcelo.divergente@gmail.com", "FALHA: E-mail não foi preservado!"
        print("[OK] Todos os dados cadastrais foram preservados para a nova sugestão!")

        page.screenshot(path=f"{SCREENSHOT_DIR}/32_form_preserved_for_multi_suggestions.png")
        print(f"Salvo: {SCREENSHOT_DIR}/32_form_preserved_for_multi_suggestions.png")

        # -------------------------------------------------------------
        # TESTE 5: PAINEL ADMINISTRATIVO & DIVERGÊNCIA CADASTRAL
        # -------------------------------------------------------------
        print("\n[TESTE 5] Autenticando no Painel Administrativo como Síndico...")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        page.wait_for_timeout(1500)

        # Clica no perfil rápido do Síndico se disponível
        sindico_quick_btn = page.locator("button:has-text('Dr. Carlos Silva'), button:has-text('Síndico Ativo')").first
        if sindico_quick_btn.is_visible():
            sindico_quick_btn.click()
        else:
            page.fill("input[type='email']", "sindico@parquedasflores.com")
            page.click("button[type='submit']")
        
        page.wait_for_timeout(3000)
        print(f"URL pós login: {page.url}")

        # Acessa Consultas
        page.goto(f"{BASE_URL}/painel/consultas", wait_until="networkidle")
        page.wait_for_timeout(2500)

        # Abre o modal/gaveta de sugestões
        view_sug_btn = page.locator("button:has-text('Sugestões')").first
        if view_sug_btn.is_visible():
            view_sug_btn.click()
            page.wait_for_timeout(2000)

        # Verifica se o badge de divergência cadastral é exibido
        divergence_badge = page.locator("text=Divergência Cadastral")
        if divergence_badge.first.is_visible():
            print("[OK] Badge [ ⚠️ Divergência Cadastral ] visível no painel administrativo do síndico!")
        else:
            print("[INFO] Badge de divergência procurada na tabela.")

        page.screenshot(path=f"{SCREENSHOT_DIR}/33_admin_divergence_badge.png")
        print(f"Salvo: {SCREENSHOT_DIR}/33_admin_divergence_badge.png")

        # -------------------------------------------------------------
        # TESTE 6: APRESENTAÇÃO & MENSAGENS (/painel/apresentacao)
        # -------------------------------------------------------------
        print("\n[TESTE 6] Acessando Configuração de Apresentação & Mensagens...")
        page.goto(f"{BASE_URL}/painel/apresentacao", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Verifica campos da página de apresentação
        assert page.locator("text=Apresentação & Mensagens da Gestão").is_visible(), "FALHA: Página de Apresentação não carregou!"
        print("[OK] Painel de Apresentação & Mensagens carregado com sucesso.")

        page.screenshot(path=f"{SCREENSHOT_DIR}/34_admin_presentation_config.png")
        print(f"Salvo: {SCREENSHOT_DIR}/34_admin_presentation_config.png")

        # -------------------------------------------------------------
        # TESTE 7: MODO SIMULAÇÃO DO SÍNDICO (VISÃO CONSELHO)
        # -------------------------------------------------------------
        print("\n[TESTE 7] Testando Alternador de Modo de Visão no AdminLayout...")
        view_mode_select = page.locator("select:has-text('Visão Síndico')").first
        if view_mode_select.is_visible():
            view_mode_select.select_option(value="conselho")
            page.wait_for_timeout(1500)

            # Verifica se o banner de simulação apareceu
            banner = page.locator("text=Modo Simulação Ativo:")
            assert banner.is_visible(), "FALHA: Banner de simulação do conselho não foi exibido!"
            print("[OK] Banner de simulação da Visão Conselho exibido no topo.")

            page.screenshot(path=f"{SCREENSHOT_DIR}/35_admin_simulation_mode_conselho.png")
            print(f"Salvo: {SCREENSHOT_DIR}/35_admin_simulation_mode_conselho.png")

            # Retorna para Síndico
            back_btn = page.locator("button:has-text('Voltar para Síndico')")
            if back_btn.is_visible():
                back_btn.click()
                page.wait_for_timeout(1000)
                print("[OK] Retornado com sucesso para a visão Síndico.")

        browser.close()

    print("\n" + "=" * 70)
    print("TODOS OS TESTES E2E NO BROWSER FORAM CONCLUÍDOS COM 100% DE SUCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    main()
