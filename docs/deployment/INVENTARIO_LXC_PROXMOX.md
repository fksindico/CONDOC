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
* **Sistema Operacional:** Ubuntu 24.04.1 LTS (Noble Numbat)
* **Processador:** 4 vCPUs alocadas
* **Memória RAM:** 4.0 GiB total (40 MiB em uso, ~4.0 GiB disponíveis)
* **Armazenamento (/):** 30 GB total (865 MB em uso, 28 GB livres — 4% utilizado)
* **Ambiente de Execução:** Fresh container limpo
  * Python: `3.12.3` / `3.14.4`
  * Docker / Compose: *Pendente de instalação via script de provisionamento*
  * Node.js / Git: *Pendente de instalação*

---

### LXC 2 — Supabase Local Stack (PostgreSQL, Auth, Storage, Kong Gateway)
* **Endereço IP:** `192.168.10.201` (Porta SSH: `22`)
* **Usuário:** `condoc`
* **Privilégios Sudo:** **SUCESSO** (acesso administrativo verificado via `sudo`)
* **Sistema Operacional:** Ubuntu 24.04.1 LTS (Noble Numbat)
* **Processador:** 2 vCPUs alocadas
* **Memória RAM:** 2.0 GiB total (38 MiB em uso, ~2.0 GiB disponíveis)
* **Armazenamento (/):** 30 GB total (865 MB em uso, 28 GB livres — 4% utilizado)
* **Ambiente de Execução:** Fresh container limpo
  * Docker / Compose: *Pendente de instalação via script de provisionamento*

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
