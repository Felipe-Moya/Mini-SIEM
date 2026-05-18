# 🛡 Mini SIEM

Sistema de monitoramento de segurança composto por um site Flask para autenticação de usuários e um dashboard desktop em PySide6 para visualização e gerenciamento de eventos em tempo real.

---


## 🚀 Funcionalidades

### Site (Flask)
- Cadastro e login de usuários
- Hash de senha com SHA-256
- Bloqueio progressivo por tentativas incorretas:
  - 3 erros → bloqueio de 15 minutos
  - 3 erros novamente → bloqueio de 1 hora
  - 2 erros novamente → bloqueio permanente
- Registro de todos os eventos no banco de dados

### Dashboard (PySide6)
- **Visão Geral** — cards com totais de eventos, falhas, logins, IPs únicos e contas bloqueadas + gráfico de atividade dos últimos 30 dias
- **Logs** — tabela paginada com filtros por usuário, evento, resultado e período
- **Alertas** — monitoramento em tempo real com polling a cada 5s, som de alerta, detecção de IPs suspeitos e bloqueios
- **Desbloquear Contas** — gerenciamento de contas bloqueadas temporária ou permanentemente
- **Configurações** — gerenciamento da conta do painel, intervalo de polling e som

---

## 🛠 Tecnologias

| Camada | Tecnologia |
|---|---|
| Site | Python, Flask |
| Dashboard | Python, PySide6 |
| Banco de dados | PostgreSQL |
| Conector DB | psycopg3 |

---

## 📁 Estrutura

```
Mini-SIEM/
├── config.py
├── requirements.txt
├── .gitignore
├── Site/
│   ├── main.py
│   ├── models.py
│   ├── views.py
│   └── templates/
│       ├── index.html
│       ├── login.html
│       ├── cadastro.html
│       └── cadastro_sucesso.html
└── Software/
    ├── main.py
    ├── dashboard.py
    ├── models.py
    ├── views.py
    ├── assets/
    │   └── alerta.wav
    └── pages/
        ├── home.py
        ├── logs.py
        ├── alertas.py
        └── configuracoes.py
```

---

## ⚙️ Como rodar

### Pré-requisitos
- Python 3.10+
- PostgreSQL rodando localmente

### 1. Clonar o repositório
```bash
git clone https://github.com/Felipe-Moya/Mini-SIEM.git
cd Mini-SIEM
```

### 2. Criar e ativar o ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar o banco de dados

Crie o banco e o usuário no PostgreSQL:
```sql
CREATE DATABASE siem;
CREATE USER siem_user WITH PASSWORD 'testes';
GRANT ALL PRIVILEGES ON DATABASE siem TO siem_user;
```

As tabelas são criadas automaticamente na primeira execução.

### 5. Rodar o site
```bash
python Site/main.py
```
Acesse em `http://localhost:5000`

### 6. Rodar o dashboard
```bash
python Software/main.py
```

> **Variáveis de ambiente opcionais** — para sobrescrever as configurações padrão do banco:
> ```
> SIEM_DB_HOST, SIEM_DB_PORT, SIEM_DB_NAME, SIEM_DB_USER, SIEM_DB_PASS
> SIEM_SECRET_KEY
> ```

---

## 📚 O que aprendi

- Estruturar uma aplicação Python em múltiplos módulos independentes
- Implementar autenticação com bloqueio progressivo do zero
- Construir interfaces desktop modernas com PySide6 e QCharts
- Integrar aplicações distintas via banco de dados compartilhado
- Organizar um projeto para portfólio com boas práticas (`.gitignore`, `requirements.txt`, variáveis de ambiente)

---

## ⚠️ Observações

- Este projeto foi desenvolvido para fins de estudo e portfólio
- As credenciais no `config.py` são para ambiente local de desenvolvimento
- Não recomendado para uso em produção sem ajustes de segurança adicionais
