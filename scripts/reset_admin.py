import sys
import os
import asyncio
from sqlalchemy import select, update

# Adicionar diretorio raiz ao path para importar modulos do backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import AsyncSessionLocal
from backend.app.models import User
from backend.app.auth_utils import get_password_hash

async def reset_password(email, new_password):
    if not new_password or len(new_password) < 6:
        print("❌ A senha deve ter no minimo 6 caracteres.")
        return

    print(f"🔄 Tentando resetar senha para: {email}")
    
    try:
        async with AsyncSessionLocal() as session:
            # Verificar se usuario existe
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ Usuario '{email}' não encontrado.")
                return

            # Atualizar senha
            hashed = get_password_hash(new_password)
            await session.execute(
                update(User).where(User.email == email).values(hashed_password=hashed)
            )
            await session.commit()
            
            print(f"✅ SUCESSO! Senha de '{email}' atualizada.")
            print(f"🔑 Nova senha: {new_password}")

    except Exception as e:
        print(f"❌ Erro ao atualizar banco de dados: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python reset_admin.py <email> <nova_senha>")
        print("Exemplo: python reset_admin.py admin@example.com 123456")
        
        # Modo interativo se nao passar argumentos
        print("\n--- Modo Interativo ---")
        email_in = input("Email do Admin: ")
        pass_in = input("Nova Senha: ")
        asyncio.run(reset_password(email_in, pass_in))
    else:
        asyncio.run(reset_password(sys.argv[1], sys.argv[2]))
