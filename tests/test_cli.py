#!/usr/bin/env python3
"""
Script CLI para testar a API Claude Chat
"""
import requests
import json
import time
import sys
from typing import Optional

API_BASE_URL = "http://localhost:8991"

class APITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.current_session_id: Optional[str] = None
        
    def test_health(self) -> bool:
        """Testa o health check da API"""
        print("🔍 Testando Health Check...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Online: {data['service']} - {data['status']}")
                return True
            else:
                print(f"❌ Health Check falhou: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
    
    def create_new_session(self) -> bool:
        """Cria uma nova sessão"""
        print("\n🆕 Criando nova sessão...")
        try:
            response = requests.post(f"{self.base_url}/api/new-session", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.current_session_id = data["session_id"]
                print(f"✅ Sessão criada: {self.current_session_id}")
                return True
            else:
                print(f"❌ Erro ao criar sessão: HTTP {response.status_code}")
                print(f"   Resposta: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erro ao criar sessão: {e}")
            return False
    
    def create_session_with_config(self) -> bool:
        """Cria uma sessão com configurações específicas"""
        print("\n⚙️ Criando sessão com configurações...")
        try:
            config = {
                "system_prompt": "Você é um assistente especializado em testes de API. Seja conciso e direto.",
                "allowed_tools": ["Read", "Write", "Bash"],
                "max_turns": 5,
                "permission_mode": "acceptEdits",
                "cwd": "/home/suthub/.claude/cc-sdk-chat/api"
            }
            
            response = requests.post(
                f"{self.base_url}/api/session-with-config", 
                json=config,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_session_id = data["session_id"]
                print(f"✅ Sessão com config criada: {self.current_session_id}")
                return True
            else:
                print(f"❌ Erro ao criar sessão com config: HTTP {response.status_code}")
                print(f"   Resposta: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erro ao criar sessão com config: {e}")
            return False
    
    def send_message_streaming(self, message: str) -> bool:
        """Envia mensagem e recebe resposta via streaming"""
        if not self.current_session_id:
            print("❌ Nenhuma sessão ativa")
            return False
            
        print(f"\n💬 Enviando mensagem: '{message}'")
        try:
            payload = {
                "message": message,
                "session_id": self.current_session_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return False
            
            print("📥 Recebendo resposta via streaming:")
            print("---")
            
            full_response = ""
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
                                
                            elif data['type'] == 'done':
                                print("\n---")
                                print(f"✅ Resposta completa recebida ({len(full_response)} chars)")
                                return True
                                
                            elif data['type'] == 'error':
                                print(f"\n❌ Erro no streaming: {data.get('error')}")
                                return False
                                
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️ Erro ao parsear JSON: {e}")
                            continue
            
            print("\n⚠️ Stream terminou sem 'done'")
            return len(full_response) > 0
            
        except Exception as e:
            print(f"❌ Erro no streaming: {e}")
            return False
    
    def get_session_info(self) -> bool:
        """Obtém informações da sessão atual"""
        if not self.current_session_id:
            print("❌ Nenhuma sessão ativa")
            return False
            
        print(f"\n📊 Obtendo info da sessão: {self.current_session_id}")
        try:
            response = requests.get(f"{self.base_url}/api/session/{self.current_session_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Informações da sessão:")
                print(f"   - Session ID: {data['session_id']}")
                print(f"   - Ativa: {data['active']}")
                print(f"   - Config: {json.dumps(data['config'], indent=2)}")
                return True
            else:
                print(f"❌ Erro ao obter info: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao obter info: {e}")
            return False
    
    def clear_session(self) -> bool:
        """Limpa o contexto da sessão"""
        if not self.current_session_id:
            print("❌ Nenhuma sessão ativa")
            return False
            
        print(f"\n🧹 Limpando sessão: {self.current_session_id}")
        try:
            payload = {"session_id": self.current_session_id}
            response = requests.post(f"{self.base_url}/api/clear", json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✅ Sessão limpa com sucesso")
                return True
            else:
                print(f"❌ Erro ao limpar: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao limpar: {e}")
            return False
    
    def interrupt_session(self) -> bool:
        """Interrompe a sessão"""
        if not self.current_session_id:
            print("❌ Nenhuma sessão ativa")
            return False
            
        print(f"\n⏹️ Interrompendo sessão: {self.current_session_id}")
        try:
            payload = {"session_id": self.current_session_id}
            response = requests.post(f"{self.base_url}/api/interrupt", json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✅ Sessão interrompida")
                return True
            else:
                print(f"❌ Erro ao interromper: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao interromper: {e}")
            return False
    
    def delete_session(self) -> bool:
        """Deleta a sessão"""
        if not self.current_session_id:
            print("❌ Nenhuma sessão ativa")
            return False
            
        print(f"\n🗑️ Deletando sessão: {self.current_session_id}")
        try:
            response = requests.delete(f"{self.base_url}/api/session/{self.current_session_id}", timeout=10)
            
            if response.status_code == 200:
                print("✅ Sessão deletada")
                old_session = self.current_session_id
                self.current_session_id = None
                return True
            else:
                print(f"❌ Erro ao deletar: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao deletar: {e}")
            return False
    
    def list_sessions(self) -> bool:
        """Lista todas as sessões"""
        print("\n📋 Listando todas as sessões...")
        try:
            response = requests.get(f"{self.base_url}/api/sessions", timeout=10)
            if response.status_code == 200:
                sessions = response.json()
                print(f"✅ Encontradas {len(sessions)} sessões:")
                for i, session in enumerate(sessions, 1):
                    print(f"   {i}. {session['session_id']} ({'ativa' if session['active'] else 'inativa'})")
                return True
            else:
                print(f"❌ Erro ao listar: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao listar: {e}")
            return False

def run_full_test():
    """Executa bateria completa de testes"""
    print("🧪 INICIANDO TESTES DA API CLAUDE CHAT")
    print("=" * 50)
    
    tester = APITester()
    results = []
    
    # 1. Health Check
    results.append(("Health Check", tester.test_health()))
    
    if not results[0][1]:
        print("\n❌ API não está disponível. Verifique se o servidor está rodando.")
        return False
    
    # 2. Criar sessão simples
    results.append(("Criar Sessão Simples", tester.create_new_session()))
    
    # 3. Testar mensagem simples
    if results[1][1]:
        results.append(("Mensagem Simples", tester.send_message_streaming("Olá! Diga apenas 'Oi, teste funcionando!'")))
        
        # 4. Obter info da sessão
        results.append(("Info da Sessão", tester.get_session_info()))
        
        # 5. Limpar sessão
        results.append(("Limpar Sessão", tester.clear_session()))
        
        # 6. Teste após limpeza
        results.append(("Mensagem Pós-Limpeza", tester.send_message_streaming("Confirme se o contexto foi limpo")))
        
        # 7. Deletar sessão
        results.append(("Deletar Sessão", tester.delete_session()))
    
    # 8. Criar sessão com config
    results.append(("Sessão com Config", tester.create_session_with_config()))
    
    if results[-1][1]:
        # 9. Teste com configuração
        results.append(("Teste com Config", tester.send_message_streaming("Liste os arquivos do diretório atual usando ls")))
        
        # 10. Listar sessões
        results.append(("Listar Sessões", tester.list_sessions()))
        
        # 11. Limpeza final
        results.append(("Limpeza Final", tester.delete_session()))
    
    # Relatório final
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    success_rate = (passed / len(results)) * 100
    print(f"\nTaxa de sucesso: {passed}/{len(results)} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 API está funcionando corretamente!")
        return True
    else:
        print("⚠️ API apresenta problemas. Verifique os logs.")
        return False

def interactive_mode():
    """Modo interativo para testes manuais"""
    print("🎮 MODO INTERATIVO - TESTE MANUAL DA API")
    print("=" * 50)
    
    tester = APITester()
    
    # Primeiro, health check
    if not tester.test_health():
        print("❌ API não disponível")
        return
    
    while True:
        print("\n" + "-" * 30)
        print("Opções disponíveis:")
        print("1. Criar nova sessão simples")
        print("2. Criar sessão com configurações")
        print("3. Enviar mensagem")
        print("4. Obter info da sessão")
        print("5. Limpar sessão")
        print("6. Interromper sessão")
        print("7. Deletar sessão")
        print("8. Listar todas as sessões")
        print("9. Health check")
        print("0. Sair")
        
        if tester.current_session_id:
            print(f"\nSessão atual: {tester.current_session_id}")
        else:
            print("\nNenhuma sessão ativa")
        
        try:
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                tester.create_new_session()
            elif choice == "2":
                tester.create_session_with_config()
            elif choice == "3":
                if tester.current_session_id:
                    message = input("Digite sua mensagem: ").strip()
                    if message:
                        tester.send_message_streaming(message)
                else:
                    print("❌ Crie uma sessão primeiro")
            elif choice == "4":
                tester.get_session_info()
            elif choice == "5":
                tester.clear_session()
            elif choice == "6":
                tester.interrupt_session()
            elif choice == "7":
                tester.delete_session()
            elif choice == "8":
                tester.list_sessions()
            elif choice == "9":
                tester.test_health()
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n\n👋 Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_mode()
    else:
        success = run_full_test()
        sys.exit(0 if success else 1)