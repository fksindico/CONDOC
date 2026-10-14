#!/usr/bin/env python3
import sys
from playwright.sync_api import sync_playwright

def main():
    url = "http://192.168.10.200/participar/vtF2RgpJUoj7xMqbDta8"
    print(f"Navegando para {url} e monitorando console/erros...")

    console_logs = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(4000)
        except Exception as e:
            print(f"Erro de navegação: {e}")

        # Tira screenshot da tela atual
        screenshot_path = "f:/CONDOC/test_screenshots/diagnostico_flipbook.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot salvo em {screenshot_path}")

        print("\n=== CONSOLE LOGS ===")
        for log in console_logs:
            print(log)

        print("\n=== PAGE ERRORS ===")
        for err in page_errors:
            print(err)

        browser.close()

if __name__ == '__main__':
    main()
