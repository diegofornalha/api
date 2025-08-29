#!/usr/bin/env python3
"""
Teste direto do ClaudeHandler para verificar se está funcionando
"""
import asyncio
import sys
import uuid
sys.path.append('.')
from claude_handler import ClaudeHandler

async def test_claude_handler():
    print("🧪 TESTE DIRETO DO CLAUDE HANDLER")
    print("=" * 50)
    
    try:
        # Inicializar handler
        print("🚀 Inicializando ClaudeHandler...")
        handler = ClaudeHandler()
        print("✅ ClaudeHandler criado com sucesso")
        
        # Criar uma sessão
        session_id = str(uuid.uuid4())
        print(f"\n🆕 Criando sessão: {session_id}")
        await handler.create_session(session_id)
        print("✅ Sessão criada")
        
        # Enviar uma mensagem simples
        test_message = "Responda apenas: 'Claude funcionando!'"
        print(f"\n💬 Enviando mensagem: '{test_message}'")
        
        full_response = ""
        chunk_count = 0
        
        print("📥 Resposta: ", end="")
        async for response in handler.send_message(session_id, test_message):
            if response.get('type') == 'content':
                content = response.get('content', '')
                print(content, end='', flush=True)
                full_response += content
                chunk_count += 1
            elif response.get('type') == 'done':
                print(f"\n✅ Resposta completa: '{full_response}'")
                print(f"📊 Chunks recebidos: {chunk_count}")
                break
            elif response.get('type') == 'error':
                print(f"\n❌ Erro: {response.get('error')}")
                return False
        
        # Verificar se recebeu conteúdo
        if len(full_response.strip()) > 0:
            print("✅ TESTE PASSOU: Claude está respondendo!")
            return True
        else:
            print("❌ TESTE FALHOU: Resposta vazia")
            print("🔍 Possíveis causas:")
            print("   - Chave API não configurada")
            print("   - Problema de conectividade")
            print("   - Claude SDK não configurado corretamente")
            return False
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            if 'session_id' in locals():
                await handler.destroy_session(session_id)
                print("🗑️ Sessão deletada")
        except:
            pass

async def test_claude_info():
    """Verifica informações do Claude SDK"""
    print("\n" + "=" * 50)
    print("🔍 INFORMAÇÕES DO CLAUDE SDK")
    print("=" * 50)
    
    try:
        from claude_handler import get_claude_version
        print(f"📦 Versão do SDK: {get_claude_version()}")
        
        # Verificar caminho do SDK
        import os
        sdk_path = "/home/suthub/.claude/cc-sdk-chat/api/claude-code-sdk-python"
        if os.path.exists(sdk_path):
            print(f"✅ Caminho do SDK existe: {sdk_path}")
            
            # Listar alguns arquivos
            files = os.listdir(sdk_path)[:5]  # Primeiros 5 arquivos
            print(f"📁 Alguns arquivos no SDK: {', '.join(files)}")
        else:
            print(f"❌ Caminho do SDK não encontrado: {sdk_path}")
        
        # Verificar se pode importar os módulos principais
        try:
            import claude_code_sdk
            print("✅ Módulo claude_code_sdk importado com sucesso")
        except ImportError as e:
            print(f"❌ Erro ao importar claude_code_sdk: {e}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar informações: {e}")

if __name__ == "__main__":
    asyncio.run(test_claude_info())
    success = asyncio.run(test_claude_handler())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CLAUDE ESTÁ FUNCIONANDO CORRETAMENTE!")
        print("✅ A API deveria estar retornando conteúdo")
        exit(0)
    else:
        print("❌ CLAUDE NÃO ESTÁ FUNCIONANDO")
        print("🔧 Verifique a configuração do SDK")
        exit(1)