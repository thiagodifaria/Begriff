import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Any, Dict

# Importa as funções do gerador de dados e os modelos
from .data_generator import get_or_create_user_data
from .models import Account

app = FastAPI(
    title="Mock Open Banking Provider",
    description="Um servidor simulado que gera dados bancários dinâmicos por usuário.",
    version="2.0.0"
)

class ConexaoRequest(BaseModel):
    id_usuario: str
    id_banco: str # Mantido para compatibilidade da interface, mas a lógica agora é centrada no usuário.

@app.post("/conectar-conta", status_code=200)
def conectar_conta(request: ConexaoRequest):
    """
    Endpoint para simular a conexão de uma conta.
    Na prática, apenas garante que os dados mock para o usuário sejam criados.
    """
    try:
        user_id_int = int(request.id_usuario)
        get_or_create_user_data(user_id_int)
        return {"message": f"Contas simuladas para o usuário {user_id_int} estão prontas para acesso."}
    except ValueError:
        raise HTTPException(status_code=400, detail="id_usuario deve ser um inteiro.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar dados: {e}")

@app.get("/accounts", response_model=List[Account])
def get_accounts(id_usuario: str = Query(..., description="ID do usuário para buscar as contas conectadas")):
    """
    Retorna as contas simuladas para um usuário específico.
    """
    try:
        user_id_int = int(id_usuario)
        user_data = get_or_create_user_data(user_id_int)
        # Retorna a lista de contas do usuário a partir do nosso banco de dados em memória (MOCK_DB)
        return user_data.get("accounts", [])
    except ValueError:
        raise HTTPException(status_code=400, detail="id_usuario deve ser um inteiro.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar contas: {e}")


@app.get("/accounts/{account_id}/transactions")
def get_transactions(account_id: str):
    """
    Retorna as transações para uma conta específica.
    Esta função agora busca em todos os usuários no MOCK_DB para encontrar a conta correspondente.
    """
    try:
        # Acessa a MOCK_DB diretamente do data_generator
        from .data_generator import MOCK_DB

        for user_id, user_data in MOCK_DB.items():
            if account_id in user_data.get("transactions", {}):
                return user_data["transactions"][account_id]
        
        # Se o loop terminar e não encontrar, a conta não existe.
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar transações: {e}")