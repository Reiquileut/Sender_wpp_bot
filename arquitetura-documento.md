# Arquitetura para Escalabilidade do WhatsApp Messenger

Este documento descreve a arquitetura proposta para transformar o WhatsApp Messenger em um serviço escalável, com suporte para login permanente, containerização com Docker e sistema de tokens para cobrança.

## Visão Geral da Arquitetura

![Arquitetura do Sistema](https://via.placeholder.com/800x500?text=Diagrama+de+Arquitetura+do+Sistema)

A nova arquitetura é baseada em microserviços e contém os seguintes componentes principais:

1. **WhatsApp API Core** - Serviço principal que gerencia conexões com WhatsApp
2. **Sistema de Autenticação** - Gerencia usuários, login e tokens de acesso
3. **Fila de Processamento** - Para processamento assíncrono de mensagens
4. **Banco de Dados** - Para persistência de dados
5. **Cache Distribuído** - Para melhorar desempenho e compartilhar sessões
6. **System Monitor** - Para acompanhamento de métricas e logs
7. **CLI Distribuído** - Interface de linha de comando para interação via terminal

## Componentes da Arquitetura

### 1. WhatsApp API Core

Este é o componente central que gerencia a conexão com o WhatsApp Web através da biblioteca whatsapp-web.js. Suas responsabilidades incluem:

- Gerenciar sessões de WhatsApp
- Processar requisições de envio de mensagens
- Receber e processar callbacks e eventos do WhatsApp
- Gerenciar QR Codes e autenticação
- Controlar limites de taxa de envio

#### Escalabilidade:
- Múltiplas instâncias podem ser executadas simultaneamente
- Cada instância gerencia uma ou mais contas de WhatsApp
- Balanceamento de carga entre instâncias

### 2. Sistema de Autenticação e Tokens

Gerencia usuários, autenticação e o sistema de tokens para cobrança:

- Autenticação de usuários via JWT
- Verificação e validação de tokens
- Rastreamento de uso e consumo de tokens
- Geração de faturas e relatórios de uso
- Gestão de planos e limites

#### Usuários e Permissões:
- **Admin**: Acesso total, gerencia usuários e tokens
- **Cliente**: Pode enviar mensagens conforme saldo de tokens
- **API User**: Usuário técnico para integração via API

### 3. Sistema de Filas e Workers

Para permitir processamento em alta escala e assíncrono:

- **Filas de Mensagens**: Para processar envios em massa
- **Filas de Arquivos**: Para processar uploads de arquivos
- **Filas de Notificações**: Para processamento de webhooks e eventos
- **Workers**: Processos que consomem as filas e executam tarefas

#### Tecnologias:
- Redis para gerenciamento de filas
- Bull para agendamento e processamento
- Estratégias de retry e circuit breaker

### 4. Banco de Dados

Persiste os dados do sistema:

- **MongoDB**: Para dados não-estruturados (sessões WhatsApp, configurações)
- **PostgreSQL** (opcional): Para dados relacionais (usuários, transações, tokens)

#### Dados Armazenados:
- Informações de usuários e autenticação
- Histórico de mensagens enviadas
- Registro de consumo de tokens
- Configurações do sistema
- Metadados de sessões WhatsApp

### 5. Cache Distribuído

Utilizado para melhorar performance e compartilhar estados:

- **Redis**: Cache de sessões, limites de taxa e dados temporários
- Armazenamento de QR codes temporários
- Cache de contatos e listas frequentes

### 6. Monitoramento e Logging

Sistema completo de monitoramento:

- **Prometheus**: Coleta de métricas de performance
- **Grafana**: Visualização de dados e dashboards
- **ELK Stack** (opcional): Para logs centralizados
- Alertas e notificações

#### Métricas Monitoradas:
- Taxa de envio de mensagens
- Taxa de sucesso/falha
- Uso de recursos (CPU, memória)
- Consumo de tokens
- Tempo de resposta da API

### 7. CLI e Interfaces

Múltiplas formas de interação com o sistema:

- **CLI**: Interface de linha de comando para operações via terminal
- **API REST**: Para integração com outros sistemas
- **Web UI** (opcional): Interface administrativa web
- **Webhooks**: Para receber callbacks de eventos

## Fluxo de Dados

### Fluxo de Envio de Mensagem:
1. Cliente envia requisição via CLI ou API
2. Sistema verifica autenticação e saldo de tokens
3. Mensagem é enfileirada para processamento
4. Worker processa a mensagem
5. Conexão WhatsApp envia mensagem
6. Status é atualizado e cliente é notificado

### Fluxo de Autenticação WhatsApp:
1. Cliente solicita login via CLI ou API
2. Sistema gera QR Code
3. Cliente escaneia com WhatsApp
4. Sessão é armazenada para uso persistente
5. Múltiplos dispositivos podem ser conectados

## Escalabilidade e Alta Disponibilidade

### Estratégia de Escalabilidade Horizontal:
- Containers Docker para todos os componentes
- Kubernetes para orquestração (opcional)
- Balanceamento de carga entre instâncias API
- Escalonamento automático baseado em demanda

### Alta Disponibilidade:
- Múltiplas instâncias de cada componente
- Redundância em diferentes zonas/regiões
- Estratégias de failover automático
- Persistência de sessões entre reinicializações

## Sistema de Tokens e Cobrança

### Funcionamento:
1. Usuários adquirem pacotes de tokens
2. Cada operação consome uma quantidade específica:
   - Mensagem de texto: 1 token
   - Envio de arquivo: 2 tokens
   - Mensagem em lote: 1 token por destinatário
3. Sistema registra consumo e atualiza saldo
4. Alertas quando saldo está baixo
5. API para verificação e compra de tokens

### Implementação:
- Middleware de verificação de tokens
- Tabela de preços configurável
- Relatórios de uso e consumo
- Integração com gateway de pagamento (opcional)

## Segurança

### Medidas de Segurança:
- Autenticação JWT para API
- Encriptação de dados sensíveis
- Rate limiting para evitar abuso
- Validação de entrada em todas as APIs
- Logs de auditoria para todas as operações críticas
- Isolamento entre usuários

## Guia de Implementação

A implementação deve seguir as seguintes etapas:

1. **Fase 1: Core Services**
   - Migrar servidor atual para estrutura RESTful
   - Implementar sistema de usuários e autenticação
   - Criar CLI básico

2. **Fase 2: Escalabilidade**
   - Implementar sistema de filas
   - Containerizar aplicação com Docker
   - Configurar persistência de dados

3. **Fase 3: Sistema de Tokens**
   - Implementar contabilização de tokens
   - Criar APIs para gerenciamento de tokens
   - Desenvolver relatórios de uso

4. **Fase 4: Monitoramento e Operação**
   - Configurar sistema de monitoramento
   - Implementar logging centralizado
   - Configurar alertas

## Código e Estrutura de Diretórios

A estrutura de diretórios recomendada é:

```
whatsapp-messenger/
├── server/                  # Serviço WhatsApp API
│   ├── src/                 # Código fonte
│   │   ├── api/             # Controllers da API
│   │   ├── services/        # Serviços de negócio
│   │   ├── models/          # Modelos de dados
│   │   ├── middleware/      # Middlewares
│   │   └── utils/           # Utilitários
│   ├── config/              # Configurações
│   ├── tests/               # Testes
│   └── Dockerfile           # Container definition
│
├── worker/                  # Worker para processamento assíncrono
│   ├── src/                 # Código fonte do worker
│   ├── config/              # Configurações
│   └── Dockerfile           # Container definition
│
├── cli/                     # Interface de linha de comando
│   ├── whatsapp_cli.py      # Script principal
│   ├── src/                 # Módulos Python
│   └── config/              # Configurações
│
├── admin-ui/                # Interface administrativa (opcional)
│   ├── src/                 # Código fonte React/Vue
│   └── Dockerfile           # Container definition
│
├── monitoring/              # Configurações de monitoramento
│   ├── prometheus/          # Configurações Prometheus
│   └── grafana/             # Dashboards Grafana
│
├── nginx/                   # Configurações de proxy reverso
│   ├── nginx.conf           # Configuração principal
│   └── conf.d/              # Configurações adicionais
│
├── scripts/                 # Scripts utilitários
│   ├── setup.sh             # Script de instalação
│   └── backup.sh            # Scripts de backup
│
└── docker-compose.yml       # Definição dos serviços Docker
```

## Considerações Finais

Esta arquitetura permite que o WhatsApp Messenger seja escalado horizontalmente para suportar um grande número de usuários e mensagens, mantendo a confiabilidade e permitindo a monetização através do sistema de tokens.

A implementação modular permite adicionar novas funcionalidades de forma incremental e ajustar a escala conforme necessário, usando recursos de nuvem sob demanda.
