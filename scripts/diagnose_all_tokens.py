#!/usr/bin/env python3
import urllib.request
from playwright.sync_api import sync_playwright

tokens = [
    "TkFR0KZuBYubJ0oqZSEJ",
    "xbXrFAeqpTSiDygPkaAX",
    "vtF2RgpJUoj7xMqbDta8",
    "h7ISqnfDpAycloAe017T"
]

def check_token(p, token):
    url = f"http://192.168.10.200/participar/{token}"
    print(f"\n==========================================")
    print(f"Testando Token: {token} -> {url}")
    
    # Primeiro verifica se o endpoint do PDF responde 200
    pdf_url = f"http://192.168.10.200/api/v1/public/consultations/{token}/pdf"
    try:
        resp = urllib.request.urlopen(pdf_url)
        content_len = len(resp.read())
        print(f"  [API PDF] Status {resp.status}, Content-Length: {content_len} bytes")
    except Exception as e:
        print(f"  [API PDF ERRO]: {e}")

    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    console_logs = []
    page_errors = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"  [Navegação Erro]: {e}")

    # Verifica se a mensagem de erro está na tela
    error_element = page.locator("text='Não foi possível carregar o PDF'")
    if error_element.count() > 0 and error_element.is_visible():
        print(f"  [ALERTA]: Mensagem 'Não foi possível carregar o PDF' ESTÁ VISÍVEL na tela!")
        error_p = page.locator("div:has-text('Não foi possível carregar o PDF') p").all_inner_texts()
        print(f"  Texto do erro na tela: {error_p}")
    else:
        print(f"  [OK]: PDF carregado sem mensagem de erro!")

    if console_logs:
        print("  Logs do Console:")
        for log in console_logs:
            print(f"    {log}")
    if page_errors:
        print("  Erros de Página:")
        for err in page_errors:
            print(f"    {err}")

    page.screenshot(path=f"f:/CONDOC/test_screenshots/teste_{token}.png")
    browser.close()

def main():
    with sync_playwright() as p:
        for t in tokens:
            check_token(p, t)

if __name__ == '__main__':
    main()
