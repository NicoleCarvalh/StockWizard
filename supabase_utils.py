from supabase import create_client, Client
import os

# Configuração do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_to_supabase(question: str, answer: str, company_id: str):
    try:
        data = {
            "question": question,
            "answer": answer,
            "companyId": company_id
        }
        result = supabase.table("chat").insert(data).execute()
        if result.status_code == 201:
            print("Resposta salva com sucesso no Supabase!")
        else:
            print(f"Erro ao salvar: {result}")
    except Exception as e:
        print(f"Erro ao conectar ao Supabase: {e}")


def fetch_responses(company_id: str):
    try:
        # Filtrar as respostas pelo ID da empresa
        result = supabase.table("chat").select("*").eq("companyId", company_id).execute()

        # Verificar se a consulta foi bem-sucedida e se há dados retornados
        if result.data:  # Verifica se há dados no retorno
            return result.data
        else:
            return {"error": "Nenhum dado encontrado."}
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return {"error": f"Erro ao buscar dados: {e}"}


