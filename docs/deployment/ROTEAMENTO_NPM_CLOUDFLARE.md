# Arquitetura de Roteamento e Proxy Reverso — CONDC
## Hostname: condoc.fk.adm.br

Este documento descreve a topologia de tráfego, as portas dos serviços, as regras de encaminhamento do **Nginx Proxy Manager (NPM)** e a configuração do proxy reverso interno da **LXC 1** (`192.168.10.200`).

---

## 1. Topologia Geral de Tráfego

```mermaid
flowchart LR
    User([Navegador / Usuário]) -->|HTTPS: 443| CF[Cloudflare CDN / DNS]
    CF -->|HTTPS: 443| NPM[Nginx Proxy Manager]
    
    subgraph LXC1 [LXC 1: Aplicação CONDC - 192.168.10.200]
        ProxyLocal[Proxy Reverso Interno: Caddy / Nginx - Porta 80]
        Front[Frontend SPA React: Porta 3000 / Estático]
        Core[Core Django API / BFF: Porta 8000]
        Celery[Workers Celery: Background]
        Redis[(Redis: 6379 Local)]
    end

    subgraph LXC2 [LXC 2: Supabase - 192.168.10.201]
        Postgres[(PostgreSQL 15: 5432)]
        Auth[Supabase Auth: 9999]
        Storage[Supabase Storage: 5000]
        Kong[Kong Gateway: 8000]
    end

    NPM -->|HTTP: Porta 80| ProxyLocal
    ProxyLocal -->|/ | Front
    ProxyLocal -->|/api/* | Core
    ProxyLocal -->|/static/* | Core
    Core -->|DB & RLS: 5432| Postgres
    Core -->|Auth API: 9999| Auth
    Core -->|Storage API: 5000| Storage
    Core -->|Cache / Filas: 6379| Redis
```

---

## 2. Configuração no Nginx Proxy Manager (NPM)

No painel administrativo do seu Nginx Proxy Manager, configure o Proxy Host exatamente conforme abaixo:

### Aba "Details":
* **Domain Names:** `condoc.fk.adm.br`
* **Scheme:** `http`
* **Forward Hostname / IP:** `192.168.10.200`
* **Forward Port:** `80` *(ou diretamente a porta do frontend, mas recomendamos a porta 80 da LXC 1 com o proxy unificador de `/api` e `/`)*
* **Opções a Ativar:**
  * [x] **Cache Assets** (Opcional, recomendado desativado inicialmente para evitar cache em dev)
  * [x] **Block Common Exploits** (Ativado)
  * [x] **Websockets Support** (Ativado — essencial para HMR e canais do Tiptap/notificações)

### Aba "SSL":
* **SSL Certificate:** Certificado Cloudflare Origin ou Let's Encrypt gerenciado pelo NPM.
* **Opções a Ativar:**
  * [x] **Force SSL** (Ativado)
  * [x] **HTTP/2 Support** (Ativado)
  * [x] **HSTS Enabled** (Ativado)

### Aba "Custom Locations" (Opcional se usar a Porta 80 unificada na LXC 1):
Se você preferir que o NPM faça o roteamento direto sem proxy interno na LXC 1:
1. **Location Padrão (`/`):**
   * Encaminha para `192.168.10.200` na porta `3000` (Frontend React SPA).
2. **Custom Location (`/api/`):**
   * Encaminha para `192.168.10.200` na porta `8000` (Core Django REST API).
3. **Custom Location (`/static/`):**
   * Encaminha para `192.168.10.200` na porta `8000` (Arquivos estáticos do Django).

> **Recomendação de Arquitetura (PRD Mestre v3.0, Seção 24):**  
> Recomendamos encaminhar o NPM para a **porta 80** da LXC 1. Na porta 80 da LXC 1 teremos um Caddy/Nginx unificador local. Isso garante **Same-Origin** nativo entre `/` (Frontend) e `/api` (Backend), eliminando 100% dos problemas de cookies entre domínios e complexidades de CORS/SameSite.

---

## 3. Mapeamento de Portas na LXC 1 (`192.168.10.200`)

| Serviço | Porta Interna | Porta Exposta na LXC 1 | Função |
|---|---|---|---|
| **Proxy Unificador (Caddy / Nginx)** | 80 | **80** (Recebe do NPM) | Recebe o tráfego do NPM e roteia `/` para o Frontend e `/api/` para o Core Django |
| **Frontend SPA (React / Vite)** | 3000 | 3000 (Interna/Docker) | Interface do Síndico e Portal do Morador |
| **Core Django API (BFF)** | 8000 | 8000 (Interna/Docker) | Endpoints REST v1, autenticação BFF, regras de negócio e RLS |
| **Redis Server** | 6379 | 127.0.0.1:6379 (Privada) | Broker do Celery e cache local da aplicação |
| **Celery Workers** | N/A | Processo em background | Execução de OCR (Tesseract), conversões e tarefas assíncronas |

---

## 4. Cabeçalhos HTTP Mandatórios para o NPM / Cloudflare

Para que a segurança de cookies do padrão BFF (`Secure`, `HttpOnly`, `SameSite=Lax`) e a identificação do IP real do morador/síndico funcionem com precisão:

* `Host: $host`
* `X-Real-IP: $remote_addr` (ou `CF-Connecting-IP` vindo da Cloudflare)
* `X-Forwarded-For: $proxy_add_x_forwarded_for`
* `X-Forwarded-Proto: https` (Mandatório para que o Django reconheça a requisição como HTTPS segura)
