from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from supabase_utils import save_to_supabase, fetch_responses
from serpapi import search
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
APIKEY = os.getenv("SERPAPIKEY")

# Configuração do modelo e do prompt
template = """
Você é o StockWizard, assistente de IA do StockWise, especializado em controle de estoque do sistema StockWise. Responda de forma concisa e objetiva sobre gerenciamento de inventário, otimização de processos e dúvidas sobre o sistema. Use o contexto fornecido, sempre que disponível, para adaptar suas respostas. Também pode realizar pesquisas na web, caso solicitado.

Contexto: {context}
Pergunta: {question}

Resposta:
"""

model = OllamaLLM(model="llama3.2:1b")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Configuração para o PDF
PDF_PATH = "./data/StockWise.pdf" 
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = None

# Função para carregar e indexar o PDF
def load_and_index_pdf(pdf_path):
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        return FAISS.from_documents(documents, embedding_model) # Conversão para vetores
    except Exception as e:
        print(f"Erro ao carregar o PDF: {e}")
        return None

# Carrega e indexa o PDF na inicialização
vectorstore = load_and_index_pdf(PDF_PATH)

# Busca contexto no PDF
def get_context_from_pdf(query):
    if vectorstore is None:
        return ""
    retriever = vectorstore.as_retriever()
    docs = retriever.invoke(query)
    return "\n".join([doc.page_content for doc in docs[:2]])  # Retorna os 2 trechos mais relevantes

# SerpAPI
async def search_web_serpapi(query: str):
    try:
        params = {
            "q": query,
            "api_key": APIKEY,
            "engine": "google"
        }
        results = await asyncio.to_thread(search, params)
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

# FastAPI App
app = FastAPI()

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://stockwise-self.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
)

# Estrutura dos dados de entrada
class ChatRequest(BaseModel):
    question: str
    company_id: str

# Função principal para processar perguntas
async def invoke_model_async(question, context=""):
    prompt_value = prompt.format(context=context, question=question)
    result = await asyncio.to_thread(model.invoke, prompt_value)
    return result

@app.get("/")
async def root():
    return {"message": "Oi, sou o StockWizard!"}

# Endpoint para processar perguntas
@app.post("/chat")
async def post_chat(request: Request):
    body = await request.json()
    chat_request = ChatRequest(**body)
    question_lower = chat_request.question.lower()

    # Verificar se a palavra "stockwise" está na pergunta
    use_pdf_context = "stockwise" in question_lower
    pdf_context = get_context_from_pdf(chat_request.question) if use_pdf_context else ""

    # Caso inclua pesquisa na web
    if "pesquise" in question_lower:
        web_search_results = await search_web_serpapi(chat_request.question)
        search_results_text = "\n".join(
            f"{result['title']} - {result['link']}: {result['snippet']}"
            for result in web_search_results
        )
        save_to_supabase(chat_request.question, search_results_text, chat_request.company_id)
        return {"response": web_search_results}

    # Invocar o modelo com ou sem contexto
    result = await invoke_model_async(chat_request.question, context=pdf_context if use_pdf_context else "")
    if not result:
        return {"response": "Desculpe, não consegui responder à sua pergunta."}

    # Salvar a resposta no banco de dados
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
