from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from supabase_utils import save_to_supabase, fetch_responses
from fastapi import Request
from serpapi import search
from dotenv import load_dotenv
import asyncio
import os

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

# SerpAPI 
async def search_web_serpapi(query: str):
    try:
        params = {
            "q": query,
            "api_key": APIKEY,
            "engine": "google"
        }
        results = await asyncio.to_thread(search, params)
        
        # 7 primeiros resultados
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
        return

# Criação do app FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://stockwise-self.vercel.app"],  # Permitir o frontend rodando no port 5173
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Métodos permitidos
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"],  # Cabeçalhos permitidos
)

# Estrutura dados de entrada
class ChatRequest(BaseModel):
    question: str
    company_id: str

# Invocar o modelo
async def invoke_model_async(question):
    prompt_value = prompt.format(question=question)
    result = await asyncio.to_thread(model.invoke, prompt_value)
    return result

@app.get("/")
async def root():
    return {"message": "Oi, gente!"}

# Endpoint para processar perguntas
@app.post("/chat")
async def post_chat(request: Request):
    body = await request.json()
    chat_request = ChatRequest(**body)
    question_lower = chat_request.question.lower()

    if "pesquise" in question_lower:
        web_search_results = await search_web_serpapi(chat_request.question)
    
        # Transforma resultados da pesquisa web em string para salvar no bd
        search_results_text = "\n".join(
            f"{result['title']} - {result['link']}: {result['snippet']}"
            for result in web_search_results
        )
        
        # Salvar no banco de dados
        save_to_supabase(chat_request.question, search_results_text, chat_request.company_id)
        
        return {"response": web_search_results}

    result = await invoke_model_async(chat_request.question)
    if not result:
        return {"response": result or "Desculpe, não consegui responder à sua pergunta."}

    save_to_supabase(chat_request.question, result, chat_request.company_id)
    return {"response": result}

@app.get("/chat")
async def get_chat(request: Request):
    company_id = request.query_params.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="O campo 'company_id' é obrigatório.")

    responses = fetch_responses(company_id)
    if "error" in responses:
        raise HTTPException(status_code=404, detail=responses["error"])

    return {"responses": responses}
