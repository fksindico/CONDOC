#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright

def main():
    url = "https://condoc.fk.adm.br/participar/vtF2RgpJUoj7xMqbDta8"
    print(f"Testando Animação 3D de Virada de Página em Modo 1 Pág em: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 820})
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3500)

        # 1. Modo 1 Página Inicial (Pág 1)
        page.screenshot(path="f:/CONDOC/test_screenshots/20_mode_1pag_initial.png")
        print("Salvo: 20_mode_1pag_initial.png")

        # 2. Clica no botão de próxima página e captura durante a animação de virada (flip)
        next_btn = page.locator("button[title*='Folhear próxima']")
        if next_btn.first.is_visible():
            next_btn.first.click()
            # Captura a meio caminho da animação (200ms após clique, duração total 450ms)
            page.wait_for_timeout(200)
            page.screenshot(path="f:/CONDOC/test_screenshots/21_mode_1pag_flipping.png")
            print("Salvo: 21_mode_1pag_flipping.png")

            # Aguarda terminar a virada
            page.wait_for_timeout(450)
            page.screenshot(path="f:/CONDOC/test_screenshots/22_mode_1pag_after_flip_page2.png")
            print("Salvo: 22_mode_1pag_after_flip_page2.png")

        # 3. Folheia até a Página 4
        if next_btn.first.is_visible():
            next_btn.first.click()
            page.wait_for_timeout(500)
            next_btn.first.click()
            page.wait_for_timeout(600)
            page.screenshot(path="f:/CONDOC/test_screenshots/23_mode_1pag_page4.png")
            print("Salvo: 23_mode_1pag_page4.png")

        # 4. Testa folheamento para trás (Pág 4 -> Pág 3)
        prev_btn = page.locator("button[title*='Folhear página anterior']")
        if prev_btn.first.is_visible():
            prev_btn.first.click()
            page.wait_for_timeout(200)
            page.screenshot(path="f:/CONDOC/test_screenshots/24_mode_1pag_flip_back.png")
            print("Salvo: 24_mode_1pag_flip_back.png")
            page.wait_for_timeout(450)

        # 5. Testa dobradura de canto (hover no canto inferior direito)
        stage = page.locator("main.bg-slate-950")
        box = stage.bounding_box()
        if box:
            # Move o mouse para o canto inferior direito da folha
            corner_x = box["x"] + box["width"] * 0.65
            corner_y = box["y"] + box["height"] * 0.75
            page.mouse.move(corner_x, corner_y)
            page.wait_for_timeout(300)
            page.screenshot(path="f:/CONDOC/test_screenshots/25_corner_hover.png")
            print("Salvo: 25_corner_hover.png")

        browser.close()
        print("\n[SUCESSO] Teste de animação 3D de folheamento em 1 página concluído!")

if __name__ == '__main__':
    main()
