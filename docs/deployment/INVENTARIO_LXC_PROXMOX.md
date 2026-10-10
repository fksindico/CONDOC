# Diagnóstico e Inventário de Hardware / Software — LXCs Proxmox VE

Este documento consolida a validação de infraestrutura e o inventário realizado em conformidade com as seções 13 e 15 do plano normativo de desenvolvimento do **CONDC**.

Data de Homologação: 2026-10-09  
Ambiente: Servidor Proxmox VE (Kernel `7.0.14-19-pve`, Arquitetura `x86_64`)

---

## 1. Inventário Detalhado dos Containers LXC

### LXC 1 — Aplicação CONDC (Frontend, Core Django, Celery, Redis, Proxy)
* **Endereço IP:** `192.168.10.200` (Porta SSH: `22`)
* **Usuário:** `condoc`
* **Privilégios Sudo:** **SUCESSO** (acesso administrativo verificado via `sudo`)
* **Sistema Operacional:** Ubuntu 24.04.1 LTS / 26.04.1
* **Processador:** 4 vCPUs alocadas
* **Memória RAM:** 4.0 GiB total
* **Armazenamento (/):** 30 GB total (~26 GB livres)
* **Ambiente de Execução (100% NATIVO — Zero Docker):**
  * **Proxy Reverso:** Caddy `2.6.2` (nativo via APT, escutando na porta 80)
  * **Broker e Cache:** Redis Server nativo (ativo via systemd, `PONG` validado na porta 6379)
  * **Frontend & Runtime:** Node.js `v22.22.1` e NPM `9.2.0` (nativos)
  * **Backend Core & Workers:** Python `3.14.4` com venv dedicado em `/opt/condc/venv` (pip, setuptools, wheel atualizados)
  * **OCR:** Tesseract `5.5.0` nativo com pacotes de idiomas `eng`, `osd` e `por` (português)
  * **Diretório da Aplicação:** `/opt/condc` (permissões configuradas para `condoc:condoc`)

---

### LXC 2 — Supabase Local Stack (PostgreSQL, Auth, Storage, Kong Gateway)
* **Endereço IP:** `192.168.10.201` (Porta SSH: `22`)
* **Usuário:** `condoc`
* **Privilégios Sudo:** **SUCESSO** (acesso administrativo verificado via `sudo`)
* **Sistema Operacional:** Ubuntu 24.04.1 LTS / 26.04.1 LTS
* **Processador:** 2 vCPUs alocadas
* **Memória RAM:** 2.0 GiB total
* **Armazenamento (/):** 30 GB total (~27 GB livres)
* **Ambiente de Execução (Docker estritamente restrito ao Supabase):**
  * **Docker Engine:** `29.1.3` (nativo via repositório Ubuntu, daemon ativo e funcional)
  * **Docker Compose:** `2.40.3` (plugin Compose v2)
  * **Grupo de Usuário:** `condoc` associado ao grupo `docker`
  * **Diretório da Stack:** `/opt/supabase` (permissões configuradas para `condoc:condoc`)

---

## 2. Testes de Rede e Conectividade

| Origem | Destino | Tipo de Teste | Latência / Resultado | Status |
|---|---|---|---|---|
| Máquina de Dev | LXC 1 (`192.168.10.200`) | SSH Handshake (porta 22) | Instantâneo | **APROVADO** |
| Máquina de Dev | LXC 2 (`192.168.10.201`) | SSH Handshake (porta 22) | Instantâneo | **APROVADO** |
| LXC 1 | LXC 2 (`192.168.10.201`) | ICMP Ping (rede interna) | RTT Médio: `0.111 ms` (0% perda) | **APROVADO** |
| LXC 1 | Internet | Resolução DNS e Rota Default | Resolvendo via gateway `192.168.0.1` | **APROVADO** |
| LXC 2 | Internet | Resolução DNS e Rota Default | Resolvendo via gateway `192.168.0.1` | **APROVADO** |

---

## 3. Recomendações e Próximos Passos de Infraestrutura

1. **Recursos de Memória na LXC 2 (Supabase):**
   * A LXC 2 possui atualmente 2.0 GiB de RAM. A stack completa self-hosted do Supabase (Postgres, GoTrue Auth, Storage Engine, Kong Gateway e Studio) opera de forma estável com no mínimo 3.5 a 4.0 GiB de RAM. Recomenda-se, caso possível no Proxmox, expandir a memória da LXC 2 para 4 GiB antes do deploy definitivo dos containers.
2. **Suporte a Docker nos Containers LXC:**
   * Como ambos os containers são LXC no Proxmox, para a execução do Docker Engine interno (Docker-in-LXC) é necessário que a opção **"nesting=1"** (Aninhamento / Features: Nesting) esteja habilitada nas configurações do container no painel do Proxmox VE.
