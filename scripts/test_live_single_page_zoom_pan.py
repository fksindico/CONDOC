#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright

def main():
    url = "https://condoc.fk.adm.br/participar/vtF2RgpJUoj7xMqbDta8"
    print(f"Testando Modo 1 Pág, Enquadramento, Zoom e Pan Interativo em: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ----------------------------------------------------
        # 1. TESTE MODO 1 PÁGINA (DESKTOP SPLIT VIEW: 1366x820)
        # ----------------------------------------------------
        page = browser.new_page(viewport={"width": 1366, "height": 820})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3500)

        # Verifica se o botão 1 Pág está selecionado
        btn_1pag = page.locator("button:has-text('1 Pág')")
        print(f"[1 Pág] Botão visível: {btn_1pag.is_visible()}")
        if btn_1pag.is_visible():
            btn_1pag.click()
            page.wait_for_timeout(1000)

        # Captura tela inicial no modo 1 Pág (Pág 1)
        page.screenshot(path="f:/CONDOC/test_screenshots/12_single_page_mode_page1.png")
        print("Salvo: 12_single_page_mode_page1.png")

        # Avança para a Página 4 e 5 (caso reportado pelo usuário)
        next_btn = page.locator("button[title*='Próxima']")
        for i in range(3):
            next_btn.first.click()
            page.wait_for_timeout(500)

        page.wait_for_timeout(1000)
        input_page_val = page.locator("input[type='text'][value='4']").first.is_visible()
        print(f"[1 Pág] Página 4 ativa no seletor de texto: {input_page_val}")
        page.screenshot(path="f:/CONDOC/test_screenshots/13_single_page_mode_page4.png")
        print("Salvo: 13_single_page_mode_page4.png")

        # ----------------------------------------------------
        # 2. TESTE ZOOM IN E DRAG-TO-PAN (ARRASTO COM O MOUSE)
        # ----------------------------------------------------
        btn_zoom_in = page.locator("button[title*='Aumentar Zoom']")
        # Dá 2 cliques de zoom in (100% -> 125% -> 150%)
        btn_zoom_in.click()
        page.wait_for_timeout(300)
        btn_zoom_in.click()
        page.wait_for_timeout(600)

        zoom_text = page.locator("button:has-text('%')").inner_text()
        print(f"[Zoom In] Zoom atual: {zoom_text}")
        page.screenshot(path="f:/CONDOC/test_screenshots/14_zoom_150_before_pan.png")
        print("Salvo: 14_zoom_150_before_pan.png")

        # Realiza arrasto (pan) com o mouse sobre o visualizador
        stage = page.locator("main.bg-slate-950")
        box = stage.bounding_box()
        if box:
            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2
            print(f"[Pan Drag] Arrastando de ({center_x}, {center_y}) para ({center_x - 150}, {center_y - 120})")
            page.mouse.move(center_x, center_y)
            page.mouse.down()
            page.mouse.move(center_x - 150, center_y - 120, steps=10)
            page.mouse.up()
            page.wait_for_timeout(800)

        page.screenshot(path="f:/CONDOC/test_screenshots/15_zoom_150_after_pan.png")
        print("Salvo: 15_zoom_150_after_pan.png")

        # ----------------------------------------------------
        # 3. TESTE AJUSTAR PÁGINA INTEIRA (FIT-TO-PAGE)
        # ----------------------------------------------------
        btn_fit = page.locator("button[title*='Ajustar Página Inteira']")
        btn_fit.click()
        page.wait_for_timeout(800)
        zoom_after_fit = page.locator("button:has-text('%')").inner_text()
        print(f"[Fit-to-Page] Zoom após ajustar: {zoom_after_fit}")
        page.screenshot(path="f:/CONDOC/test_screenshots/16_fit_to_page_reset.png")
        print("Salvo: 16_fit_to_page_reset.png")

        # ----------------------------------------------------
        # 4. TESTE AJUSTAR LARGURA (FIT-TO-WIDTH)
        # ----------------------------------------------------
        btn_fit_width = page.locator("button[title*='Ajustar à Largura']")
        if btn_fit_width.is_visible():
            btn_fit_width.click()
            page.wait_for_timeout(800)
            zoom_after_fit_w = page.locator("button:has-text('%')").inner_text()
            print(f"[Fit-to-Width] Zoom após ajustar à largura: {zoom_after_fit_w}")
            page.screenshot(path="f:/CONDOC/test_screenshots/17_fit_to_width.png")
            print("Salvo: 17_fit_to_width.png")

        # ----------------------------------------------------
        # 5. TESTE MODO 2 PÁGINAS (DOUBLE SPREAD)
        # ----------------------------------------------------
        btn_2pag = page.locator("button:has-text('2 Págs')")
        btn_2pag.click()
        page.wait_for_timeout(1500)
        page.screenshot(path="f:/CONDOC/test_screenshots/18_double_page_mode.png")
        print("Salvo: 18_double_page_mode.png")

        # ----------------------------------------------------
        # 6. RETORNO AO MODO 1 PÁGINA
        # ----------------------------------------------------
        btn_1pag.click()
        page.wait_for_timeout(1000)
        page.screenshot(path="f:/CONDOC/test_screenshots/19_back_to_single_page.png")
        print("Salvo: 19_back_to_single_page.png")

        browser.close()
        print("\n[SUCESSO COMPLETO] Todos os testes de 1 Página, Zoom, Pan e Enquadramento foram executados com êxito!")

if __name__ == '__main__':
    main()
