from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from supabase_utils import save_to_supabase, fetch_responses
from fastapi import Request
from serpapi import search
from dotenv import load_dotenv
import uvicorn
import asyncio
import os

# Carregar variáveis de ambiente
load_dotenv()
APIKEY = os.getenv("SERPAPIKEY")

# Configuração do modelo e do prompt
template = """
Você é o StockWizard, um assistente de IA especializado em controle de estoque do sistema StockWise. Sua missão é responder de maneira concisa e objetiva sobre controle de estoque, gerenciamento de inventário e estratégias de otimização.

Pergunta: {question}

Resposta:
"""

model = OllamaLLM(model="llama3.2:1b")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Função para realizar pesquisas na web usando SerpAPI (assíncrona)
async def search_web_serpapi(query: str):
    try:
        params = {
            "q": query,
            "api_key": APIKEY,
            "engine": "google"
        }
        results = await asyncio.to_thread(search, params)
        
        # Filtra os 7 primeiros resultados orgânicos
        if results and "organic_results" in results:
            filtered_results = [
                {
                    "title": result.get("title", "Sem título"),
                    "link": result.get("link", "Sem link"),
                    "snippet": result.get("snippet", "Sem snippet")
                }
                for result in results["organic_results"][:7]
            ]
            return filtered_results
        else:
            return [{"title": "Nenhum resultado encontrado", "link": "", "snippet": ""}]
    except Exception as e:
        print(f"Erro ao realizar pesquisa: {e}")
        return [{"title": "Erro ao realizar pesquisa", "link": "", "snippet": str(e)}]

# Criação do app FastAPI
app = FastAPI()

# Estrutura para os dados de entrada
class ChatRequest(BaseModel):
    question: str
    company_id: str

# Função assíncrona para invocar o modelo
async def invoke_model_async(question):
    prompt_value = prompt.format(question=question)
    result = await asyncio.to_thread(model.invoke, prompt_value)
    return result

@app.get("/")
async def root():
    return {"message": "Oi, gente!"}

# Endpoint para processar perguntas
@app.api_route("/chat", methods=["POST", "GET"])
async def chat_endpoint(request: Request):
    if request.method == "POST":
        try:
            # Obter o corpo da requisição como um dicionário
            body = await request.json()
            
            # Criar uma instância de ChatRequest a partir do corpo da requisição
            chat_request = ChatRequest(**body)
            
            question_lower = chat_request.question.lower()
            company_id = chat_request.company_id

            # Verificar se a pergunta contém a solicitação de pesquisa
            if "pesquise" in question_lower:
                web_search_results = await search_web_serpapi(chat_request.question)
                return {"response": "Resultados da pesquisa na web", "search_results": web_search_results}

            # Invocar o modelo com contexto e pergunta
            result = await invoke_model_async(chat_request.question)

            # Caso a resposta seja insatisfatória, podemos retornar uma resposta padrão
            if not result:
                return {"response": result or "Desculpe, não consegui responder à sua pergunta."}

            print("Resposta do modelo:", result)

            # Salvar no Supabase
            save_to_supabase(chat_request.question, result,  chat_request.company_id,)

            return {"response": result}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

    elif request.method == "GET":
        try:
            # Obter o `company_id` da query string
            company_id = request.query_params.get("company_id")
            if not company_id:
                raise HTTPException(status_code=400, detail="O campo 'company_id' é obrigatório.")

            # Buscar as respostas no Supabase
            responses = fetch_responses(company_id)
            
            # Caso haja um erro na busca, levantamos uma exceção
            if "error" in responses:
                raise HTTPException(status_code=404, detail=responses["error"])

            # Retornar as respostas formatadas
            return {"responses": responses}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

if __name__ == "__main__":
    # Obtenha a porta a partir da variável de ambiente ou use uma porta padrão
    port = int(os.environ.get("PORT", 8000))
    # Inicie o servidor na interface 0.0.0.0
    uvicorn.run(app, host="0.0.0.0", port=port)