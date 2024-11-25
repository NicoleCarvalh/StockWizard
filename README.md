# StockWizard: O Assistente de IA do StockWise

![Imagem de exemplo](stockwizard_icon.png)

## O que é o StockWizard?

O **StockWizard** é um assistente de inteligência artificial integrado ao sistema **StockWise**, projetado para otimizar o gerenciamento de estoque de micro e pequenos empreendedores. Ele utiliza processamento de linguagem natural para interagir de forma intuitiva, respondendo a perguntas tanto gerais quanto específicas relacionadas ao sistema.

## Para que serve?

O StockWizard tem como objetivo facilitar a experiência do usuário com o **StockWise**, oferecendo suporte em diversas frentes:

- **Respostas a perguntas naturais**: O usuário pode interagir com o assistente usando linguagem comum, sem necessidade de comandos técnicos.
- **Consultas específicas do sistema**: O assistente está integrado ao StockWise, permitindo responder perguntas sobre:

  - Status do inventário.
  - Relatórios de compras e vendas.
  - Movimentações de produtos e análise de desempenho.

- **Pesquisa na web**: Quando necessário, o StockWizard pode buscar informações externas para complementar sua resposta, garantindo que o usuário tenha acesso às melhores práticas ou dados adicionais relevantes.

## Objetivo do projeto

O StockWizard foi desenvolvido com o objetivo de democratizar o acesso a ferramentas inteligentes de gerenciamento de estoque, tornando-as acessíveis e práticas para usuários de diferentes níveis de conhecimento técnico. Ele é mais do que um chatbot; é um aliado estratégico para otimizar processos e melhorar a performance do negócio.

---

Essa introdução visa apresentar o conceito e a utilidade do StockWizard de forma clara e objetiva, preparando o terreno para uma explicação mais detalhada ou demonstração prática.

## Como rodar?

1. Faça o download do Ollama em https://ollama.com/
2. Em seu terminal, rode o comando:
   `ollama run llama3.2:1b`
3. Clone este repositório em sua máquina
   `https://github.com/NicoleCarvalh/StockWizard.git`
4. Crie seu Ambiente Virutal:
   `python -m venv .venv`
5. Após ativar seu ambiente virtual, faça a instalação das bibliotecas:
   `pip install -r requirements.txt`
6. Para rodar a API, use o comando:
   `uvicorn app:app --reload`

## Testar requisição com Postman

1. Acessar Postman Desktop (ou com componente Postman Agent)
2. Inserir a url com método POST: http://127.0.0.1:8000/chat
3. Selecionar: Body > raw > JSON
4. Inserir corpo da requisição conforme exemplo: `{
  "question": "Como funciona o sistema StockWise?", 
  "company_id": "12345"
}`
5. Ao enviar, após o tempo de requisição, o modelo retornará a resposta