# 📋 Sistema de Controle e Emissão de Recibos de Materiais

> Aplicação web desenvolvida em Python e Streamlit para gestão de fluxo de materiais, numeração sequencial contínua, geração de minutas timbradas em padrão A4 para assinatura física, controle estrito de pendências e arquivamento digital de comprovantes.
> 
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)

  
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)

  
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

  
![Status](https://img.shields.io/badge/Status-Em%20Produ%C3%A7%C3%A3o-success)
---

## 📌 O Problema que o Sistema Resolve

Em ambientes operacionais, logísticos e administrativos com alta rotatividade de materiais e equipamentos (como ferramentas, EPIs, suprimentos de TI e materiais de consumo), a entrega física demanda frequentemente um **comprovante assinado** para salvaguarda de responsabilidade. 

Na prática, as organizações enfrentam problemas críticos:
1. **Perda de Rastreabilidade:** Materiais são entregues e os comprovantes em papel se perdem antes de serem arquivados.
2. **Quebra de Numeração Sequencial:** Múltiplas pessoas emitindo recibos sem sincronização central geram furos de numeração ou duplicidade de números.
3. **Falta de Padronização Visual:** Documentos impressos sem formatação uniforme, dificultando auditorias e conferências.
4. **Ausência de Controle de Pendências:** Dificuldade em identificar rapidamente quais materiais já foram entregues mas ainda estão com termo de assinatura pendente de retorno.

**A Solução:** Um sistema centralizado, de interface ágil e amigável, que automatiza a numeração sequencial, gera minutas prontas para impressão no formato padrão A4, acompanha o status de cada entrega em tempo real e permite anexar a via digitalizada assinada para baixar a pendência.

---

## ✨ Funcionalidades Principais

- **🔢 Numeração Sequencial Automática e Anti-Duplicidade:**
  - Identificação e cálculo dinâmico do próximo número sequencial.
  - Bloqueio inteligente de cliques múltiplos e prevenção de duplicidades consecutivas para o mesmo destinatário/assunto.
  - Em caso de cancelamento de documento gerado por engano, o sequencial é recalculado automaticamente.

- **🖨️ Emissão de Minuta Padrão A4 Auto-Contida:**
  - Gera minutas elegantes formatadas para folha A4 com cabeçalho, corpo e quadro de assinaturas.
  - **Paginação Dinâmica:** Listas com até 20 itens são consolidadas em folha única com assinaturas na base; listas extensas realizam quebra de página automática com cabeçalhos de continuação e termo de assinatura na folha final.
  - Suporte a impressão direta via navegador (`Ctrl+P` ou botão dedicado) e exportação em HTML/PDF.

- **📊 Grade Estruturada vs. Lista Livre de Materiais:**
  - **Modo Tabela / Grade:** Editor interativo de tabela com colunas de Quantidade e Discriminação do Material, com suporte a título em destaque.
  - **Modo Texto Livre:** Campo de texto livre para descrições detalhadas e especificações técnicas complexas.

- **✍️ Flexibilidade de Preenchimento:**
  - Preenchimento digital completo de fornecedor e recebedor (com pré-definição de setores e cargos).
  - Opção **"Preencher Fisicamente"**: permite emitir o termo com os campos do recebedor em branco para preenchimento manuscrito no momento da retirada.

- **📤 Devolução de Documento Assinado (Baixa de Pendência):**
  - Módulo dedicado para recepção do documento digitalizado (PDF, PNG ou JPG) após a coleta das assinaturas físicas.
  - **Renomeação Automática Padronizada:** O arquivo é automaticamente renomeado seguindo a convenção oficial (ex.: `001.MATERIAL DE ESCRITORIO Analista 20002-Y CICLANO DA SILVA.pdf`).
  - Ao confirmar o upload, o status é alterado de `🔴 Pendência de Assinatura` para `✅ Assinado / Devolvido`.

- **📋 Histórico Geral, Filtros e Ações Rápidas:**
  - Tabela consolidada com busca textual instantânea por qualquer campo (número, data, responsável, destinatário ou assunto).
  - Filtro segmentado por status: *Todos*, *Pendência de Assinatura* e *Assinados*.
  - Ações rápidas por registro: reimpressão da minuta, download do documento assinado arquivado, edição e exclusão.
  - Exportação completa de toda a base de dados em arquivo CSV estruturado.

- **🎨 Interface Moderna com Padrão Glassmorphism:**
  - Tema escuro elegante com efeito de vidro translúcido, alta legibilidade e elementos ergonômicos de alta visibilidade.

---

## 📸 Espaço para Capturas de Tela

> *As capturas de tela abaixo utilizam dados 100% fictícios para demonstração.*

### 1. Painel Principal e Métricas

<img width="1421" height="728" alt="dashboard" src="https://github.com/user-attachments/assets/59e80a68-1694-4a99-823f-29c8be58f054" />

### 2. Formulário de Elaboração de Recibo

<img width="1429" height="736" alt="formulario" src="https://github.com/user-attachments/assets/b13433e9-f7e4-4dfb-965e-5b5057d68b3b" />

### 3. Minuta Oficial Formatada para Impressão A4

<img width="1422" height="736" alt="impressao_a4" src="https://github.com/user-attachments/assets/d8bbcfac-90bc-4ee4-88d9-ea40a654d515" />

### 4. Gestão de Devoluções e Baixa de Pendências

<img width="1423" height="734" alt="devolucao" src="https://github.com/user-attachments/assets/bb694254-69ce-46da-8b94-f753f76dac4f" />



---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Finalidade |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.10+ | Lógica de negócios e backend da aplicação |
| **Interface / Framework** | Streamlit | Interface reativa, componentes interativos e formulários |
| **Manipulação de Dados** | Pandas | Estruturação de dados, histórico tabular e persistência CSV |
| **Estilização Visual** | CSS3 & HTML5 | Glassmorphism, overlay de imagem e regras de impressão `@media print` |
| **Processamento de Imagem** | Pillow (PIL) | Conversão e manipulação de assets visuais em Base64 |
| **Configuração de Ambiente** | python-dotenv | Leitura e suporte a variáveis de ambiente opcionais |

---

## 📂 Estrutura do Repositório

```text
recibo-portfolio/
│
├── .env.example                 # Exemplo de configuração de variáveis de ambiente
├── .gitignore                   # Regras de exclusão do Git (sem credenciais nem arquivos temporários)
├── README.md                    # Documentação completa do projeto
├── requirements.txt             # Dependências Python do projeto
├── app.py                       # Ponto de entrada da aplicação Streamlit
├── documentos.py                # Módulo principal (regras de negócio, minuta A4 e persistência)
├── visual_theme.py              # Motor visual com Glassmorphism e estilos customizados
├── dados_exemplo.json           # Conjunto de dados fictícios para demonstração imediata
├── gerar_dados_exemplo.py       # Script utilitário para recriar/resetar a base de exemplo
│
├── .streamlit/
│   └── config.toml              # Configurações do tema e servidor Streamlit
│
├── dados/
│   └── recibos/
│       ├── controle_recibos.csv # Base de dados local em formato CSV
│       └── digitalizados/       # Diretório de armazenamento dos comprovantes assinados
│           └── .gitkeep
│
└── visual/
    └── fundo.jpg                # Imagem de fundo utilizada na interface
```

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
- **Python 3.10** ou superior instalado.
- Gerenciador de pacotes **pip** configurado.

### Passo 1: Clonar ou Acessar a Pasta do Projeto
```bash
cd recibo-portfolio
```

### Passo 2: Criar e Ativar um Ambiente Virtual (Recomendado)
No Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

No Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar as Dependências
```bash
pip install -r requirements.txt
```

### Passo 4: Inicializar os Dados Fictícios de Exemplo (Opcional)
O repositório já inclui registros fictícios por padrão. Caso queira resetar a base inicial a qualquer momento:
```bash
python gerar_dados_exemplo.py
```

### Passo 5: Executar a Aplicação
```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no seu navegador padrão no endereço:
`http://localhost:8501`

---

## ⚙️ Variáveis de Ambiente (Opcional)

Por padrão, a aplicação roda **100% offline e localmente**, sem necessidade de qualquer configuração adicional.

Caso deseje personalizar caminhos de armazenamento, copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

| Variável | Descrição | Padrão |
| :--- | :--- | :--- |
| `DIR_DADOS_RECIBOS` | Diretório customizado para os arquivos CSV e digitalizados | `./dados/recibos` |
| `SECRET_KEY` | Chave de segurança da aplicação | Vazio |

---

## 🔒 Segurança e Dados Sensíveis

Este repositório foi **estritamente auditado e sanitizado**:
- Não contém credenciais de acesso, chaves de API, senhas ou tokens.
- Não contém nomes reais de pessoas, números de documentos, matrículas funcionais ou endereços de e-mail institucionais.
- Todos os registros, responsáveis, setores e numerações presentes nos arquivos de dados são puramente **fictícios e concebidos exclusivamente para demonstração de portfólio**.
- As rotinas de rede corporativa e acessos a planilhas externas foram desacopladas para garantir que o projeto execute de forma autônoma e segura em qualquer ambiente.

---

## 👨‍💻 Autor

Desenvolvido por **Thiago Guimarães**.  
Disponível para fins de estudo, demonstração de portfólio e evolução de projetos de automação operacional.

---

## 📄 Licença

Este projeto está sob a licença [MIT](https://opensource.org/licenses/MIT). Sinta-se à vontade para utilizar, modificar e distribuir conforme as diretrizes da licença.

