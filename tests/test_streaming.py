#!/usr/bin/env python3
"""
Teste específico para verificar se o streaming está funcionando corretamente
"""
import requests
import json
import time

def test_streaming_with_real_content():
    """Testa streaming com uma mensagem que deve gerar conteúdo real"""
    API_BASE_URL = "http://localhost:8991"
    
    print("🧪 TESTE DE STREAMING COM CONTEÚDO REAL")
    print("=" * 50)
    
    # 1. Criar sessão
    print("\n🆕 Criando nova sessão...")
    response = requests.post(f"{API_BASE_URL}/api/new-session")
    if response.status_code != 200:
        print(f"❌ Falha ao criar sessão: {response.status_code}")
        return False
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ Sessão criada: {session_id}")
    
    # 2. Enviar mensagem que deve gerar resposta longa
    test_message = "Explique em detalhes o que é Python e liste 5 vantagens principais da linguagem. Seja detalhado na explicação."
    
    print(f"\n💬 Enviando mensagem: '{test_message}'")
    print("📥 Aguardando resposta via streaming...")
    
    payload = {
        "message": test_message,
        "session_id": session_id
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=payload,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
        
        print("---")
        
        full_response = ""
        chunk_count = 0
        start_time = time.time()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])  # Remove 'data: '
                        
                        if data['type'] == 'content':
                            content = data.get('content', '')
                            print(content, end='', flush=True)
                            full_response += content
                            chunk_count += 1
                            
                        elif data['type'] == 'done':
                            end_time = time.time()
                            duration = end_time - start_time
                            
                            print("\n---")
                            print(f"✅ Streaming completo!")
                            print(f"📊 Estatísticas:")
                            print(f"   - Chunks recebidos: {chunk_count}")
                            print(f"   - Caracteres totais: {len(full_response)}")
                            print(f"   - Tempo total: {duration:.2f}s")
                            print(f"   - Velocidade média: {len(full_response)/duration:.1f} chars/s")
                            
                            # Verifica se realmente recebeu conteúdo
                            if len(full_response) > 10:  # Pelo menos 10 caracteres
                                print("✅ TESTE PASSOU: Conteúdo real recebido via streaming")
                                return True
                            else:
                                print("❌ TESTE FALHOU: Pouco ou nenhum conteúdo recebido")
                                print(f"   Conteúdo recebido: '{full_response}'")
                                return False
                                
                        elif data['type'] == 'error':
                            print(f"\n❌ Erro no streaming: {data.get('error')}")
                            return False
                            
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️ Erro ao parsear JSON: {e}")
                        continue
        
        print("\n⚠️ Stream terminou sem 'done'")
        if len(full_response) > 10:
            print(f"✅ Mas conteúdo foi recebido: {len(full_response)} chars")
            return True
        else:
            print(f"❌ Pouco conteúdo: '{full_response}'")
            return False
            
    except Exception as e:
        print(f"❌ Erro no streaming: {e}")
        return False
    
    finally:
        # 3. Limpar - deletar sessão
        print(f"\n🗑️ Limpando sessão...")
        try:
            requests.delete(f"{API_BASE_URL}/api/session/{session_id}")
            print("✅ Sessão deletada")
        except:
            print("⚠️ Erro ao deletar sessão (não crítico)")

def test_quick_response():
    """Testa com uma mensagem que deve ter resposta rápida"""
    API_BASE_URL = "http://localhost:8991"
    
    print("\n" + "=" * 50)
    print("🧪 TESTE DE RESPOSTA RÁPIDA")
    print("=" * 50)
    
    # Criar sessão
    response = requests.post(f"{API_BASE_URL}/api/new-session")
    session_data = response.json()
    session_id = session_data["session_id"]
    
    test_message = "Responda apenas: 'Teste OK'"
    print(f"\n💬 Mensagem: '{test_message}'")
    
    payload = {
        "message": test_message,
        "session_id": session_id
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=payload,
            stream=True,
            timeout=30
        )
        
        print("📥 Resposta: ", end="")
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        
                        if data['type'] == 'content':
                            content = data.get('content', '')
                            print(content, end='', flush=True)
                            full_response += content
                            
                        elif data['type'] == 'done':
                            print(f"\n✅ Resposta recebida: '{full_response.strip()}'")
                            return len(full_response.strip()) > 0
                            
                    except json.JSONDecodeError:
                        continue
        
        return False
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    finally:
        try:
            requests.delete(f"{API_BASE_URL}/api/session/{session_id}")
        except:
            pass

if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DE STREAMING DETALHADOS")
    
    # Teste 1: Resposta longa e detalhada
    result1 = test_streaming_with_real_content()
    
    # Teste 2: Resposta rápida
    result2 = test_quick_response()
    
    print("\n" + "=" * 50)
    print("📊 RESULTADO FINAL")
    print("=" * 50)
    print(f"Teste de conteúdo longo: {'✅ PASSOU' if result1 else '❌ FALHOU'}")
    print(f"Teste de resposta rápida: {'✅ PASSOU' if result2 else '❌ FALHOU'}")
    
    if result1 and result2:
        print("\n🎉 TODOS OS TESTES PASSARAM - STREAMING FUNCIONANDO!")
        print("✅ A API está pronta para uso com frontend HTML")
        exit(0)
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM")
        print("🔍 Verifique se o Claude está respondendo corretamente")
        exit(1)