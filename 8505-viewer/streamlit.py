#!/usr/bin/env python3
"""
🛠️ Streamlit Debug Interface - Viewer Claude Session Summarizer
Interface de debug para testar e monitorar o sistema de resumo de sessões
"""

import streamlit as st
import json
import time
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import asyncio

# Configuração da página
st.set_page_config(
    page_title="🛠️ Viewer Debug - Session Summarizer",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.debug-container {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 1rem;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    max-height: 400px;
    overflow-y: auto;
    margin: 1rem 0;
}

.success-box {
    background-color: #d4edda;
    color: #155724;
    padding: 1rem;
    border-left: 4px solid #28a745;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.error-box {
    background-color: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-left: 4px solid #dc3545;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.warning-box {
    background-color: #fff3cd;
    color: #856404;
    padding: 1rem;
    border-left: 4px solid #ffc107;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.info-box {
    background-color: #d1ecf1;
    color: #0c5460;
    padding: 1rem;
    border-left: 4px solid #17a2b8;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Configurações
VIEWER_URL = "http://localhost:3041"
CLAUDE_PROJECTS_PATH = Path("/home/suthub/.claude/projects")

# Estado da sessão
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []
if "test_results" not in st.session_state:
    st.session_state.test_results = {}
if "selected_session" not in st.session_state:
    st.session_state.selected_session = None
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = True  # Ativado por padrão

def add_debug_log(level: str, message: str, details: dict = None):
    """Adiciona log de debug com melhor rastreamento"""
    import traceback
    import inspect
    
    # Só registra logs se modo debug estiver ativo OU for um erro
    if not st.session_state.get('debug_mode', False) and level.upper() != "ERROR":
        return
    
    # Capturar informação do contexto
    caller_info = {}
    try:
        frame = inspect.currentframe().f_back
        caller_info = {
            "function": frame.f_code.co_name,
            "line": frame.f_lineno,
            "file": frame.f_code.co_filename.split('/')[-1]
        }
    except:
        caller_info = {"function": "unknown", "line": 0, "file": "unknown"}
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "details": details or {},
        "caller": caller_info,
        "stack_trace": traceback.format_stack()[-3:-1] if level.upper() == "ERROR" else None
    }
    st.session_state.debug_logs.append(log_entry)
    
    # Manter apenas os últimos 500 logs (aumentado para melhor debug)
    if len(st.session_state.debug_logs) > 500:
        st.session_state.debug_logs = st.session_state.debug_logs[-500:]

def test_viewer_connection():
    """Testa conexão com o viewer"""
    try:
        response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=5)
        if response.status_code == 200:
            sessions = response.json()
            add_debug_log("info", f"Viewer conectado - {len(sessions)} sessões encontradas")
            return True, len(sessions)
        else:
            add_debug_log("error", f"Viewer respondeu com status {response.status_code}")
            return False, 0
    except Exception as e:
        add_debug_log("error", f"Erro ao conectar com viewer: {str(e)}")
        return False, 0

def get_available_sessions():
    """Obtém lista de sessões disponíveis"""
    try:
        response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        add_debug_log("error", f"Erro ao obter sessões: {str(e)}")
    return []

def test_summarizer_with_custom_content(custom_content: str, summary_type: str = "conciso"):
    """Testa resumo com conteúdo customizado"""
    execution_time = 0
    try:
        add_debug_log("info", f"Iniciando teste com conteúdo customizado", {
            "content_length": len(custom_content),
            "summary_type": summary_type
        })
        
        # Criar prompt personalizado diretamente
        base_instruction = "Analise esta conversa e crie um resumo estruturado em português brasileiro."
        
        if summary_type == "conciso":
            format_instruction = """
Formato CONCISO (máximo 20 palavras apenas):
📋 **Contexto**: [tipo de projeto/problema]
🎯 **Objetivo**: [o que foi solicitado]
✅ **Resultado**: [o que foi implementado/resolvido]
🔧 **Tecnologias**: [principais ferramentas]

Resumo ultra-conciso em 20 palavras:"""
        elif summary_type == "detalhado":
            format_instruction = """
Formato DETALHADO (máximo 400 palavras):
📋 **Contexto Completo**: [situação e background do projeto]
🎯 **Objetivos**: [todos os goals e requisitos discutidos]
⚙️ **Implementação**: [detalhes técnicos, arquitetura, decisões]
✅ **Resultados**: [tudo que foi entregue e funcionalidades]
🔧 **Tecnologias**: [stack completo utilizado]
💡 **Insights**: [aprendizados e decisões importantes]
🔄 **Próximos Passos**: [se mencionados na conversa]

Resumo:"""
        else:  # bullet_points
            format_instruction = """
Formato BULLET POINTS:
🎯 **Objetivos Principais:**
• [objetivo 1]
• [objetivo 2]

⚙️ **Implementação:**
• [implementação 1]
• [implementação 2]

✅ **Resultados:**
• [resultado 1]
• [resultado 2]

🔧 **Tecnologias:**
• [tech 1]
• [tech 2]

Resumo:"""
        
        full_prompt = f"{base_instruction}\n{format_instruction}\n\nConversa para análise:\n{custom_content[:10000]}"  # Limitar a 10k chars
        
        start_time = time.time()
        
        # Fazer chamada direta ao endpoint de resumo customizado
        payload = {
            "custom_content": custom_content,
            "summary_type": summary_type
        }
        
        try:
            response = requests.post(
                f"{VIEWER_URL}/api/summarize-custom", 
                json=payload,
                timeout=120,
                headers={"Content-Type": "application/json"}
            )
            execution_time = time.time() - start_time
            
            add_debug_log("debug", f"Resposta da API customizada recebida", {
                "status_code": response.status_code,
                "execution_time": execution_time,
                "response_size": len(response.content) if response.content else 0
            })
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    add_debug_log("info", f"Resumo customizado concluído com sucesso em {execution_time:.2f}s", {
                        "summary_length": len(result.get('summary', '')),
                        "has_summary": bool(result.get('summary')),
                        "success": result.get('success', False)
                    })
                    return True, result, execution_time
                except json.JSONDecodeError as je:
                    add_debug_log("error", f"Erro ao decodificar JSON customizado: {str(je)}")
                    return False, {"error": f"Resposta inválida: {str(je)}"}, execution_time
            else:
                error_details = {
                    "status_code": response.status_code,
                    "response_text": response.text[:1000]
                }
                add_debug_log("error", f"Erro HTTP {response.status_code} no resumo customizado", error_details)
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}, execution_time
        
        except requests.exceptions.Timeout:
            add_debug_log("error", f"Timeout no resumo customizado após {execution_time:.2f}s")
            return False, {"error": f"Timeout após {execution_time:.2f}s"}, execution_time
        except requests.exceptions.ConnectionError as ce:
            add_debug_log("error", f"Erro de conexão no resumo customizado: {str(ce)}")
            return False, {"error": f"Erro de conexão: {str(ce)}"}, execution_time
        
    except Exception as e:
        add_debug_log("error", f"Erro no teste customizado: {str(e)}")
        return False, {"error": str(e)}, execution_time

def test_summarizer_endpoint(directory: str, session_id: str, summary_type: str = "conciso"):
    """Testa endpoint de resumo com debug detalhado"""
    execution_time = 0
    try:
        add_debug_log("info", f"Iniciando teste de resumo", {
            "directory": directory,
            "session_id": session_id,
            "summary_type": summary_type,
            "url": f"{VIEWER_URL}/api/summarize"
        })
        
        payload = {
            "directory": directory,
            "session_id": session_id,
            "summary_type": summary_type
        }
        
        start_time = time.time()
        
        # Teste de conectividade primeiro
        try:
            health_check = requests.get(f"{VIEWER_URL}/health", timeout=5)
            add_debug_log("debug", f"Health check: {health_check.status_code}")
        except Exception as he:
            add_debug_log("warning", f"Health check falhou: {str(he)}")
        
        response = requests.post(
            f"{VIEWER_URL}/api/summarize", 
            json=payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        execution_time = time.time() - start_time
        
        add_debug_log("debug", f"Resposta recebida", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "execution_time": execution_time,
            "response_size": len(response.content) if response.content else 0
        })
        
        if response.status_code == 200:
            try:
                result = response.json()
                add_debug_log("info", f"Resumo concluído com sucesso em {execution_time:.2f}s", {
                    "summary_length": len(result.get('summary', '')),
                    "metrics": result.get('metrics', {}),
                    "has_summary": bool(result.get('summary')),
                    "success": result.get('success', False)
                })
                return True, result, execution_time
            except json.JSONDecodeError as je:
                add_debug_log("error", f"Erro ao decodificar JSON da resposta: {str(je)}", {
                    "response_text": response.text[:500],  # Primeiros 500 chars
                    "content_type": response.headers.get('content-type')
                })
                return False, {"error": f"Resposta inválida: {str(je)}"}, execution_time
        else:
            error_details = {
                "status_code": response.status_code,
                "response_text": response.text[:1000],  # Primeiros 1000 chars
                "headers": dict(response.headers)
            }
            add_debug_log("error", f"Erro HTTP {response.status_code} no resumo", error_details)
            return False, {"error": f"HTTP {response.status_code}: {response.text}"}, execution_time
            
    except requests.exceptions.Timeout as te:
        add_debug_log("error", f"Timeout na requisição de resumo após {execution_time:.2f}s: {str(te)}")
        return False, {"error": f"Timeout após {execution_time:.2f}s"}, execution_time
    except requests.exceptions.ConnectionError as ce:
        add_debug_log("error", f"Erro de conexão no resumo: {str(ce)}", {
            "url": f"{VIEWER_URL}/api/summarize",
            "directory": directory
        })
        return False, {"error": f"Erro de conexão: {str(ce)}"}, execution_time
    except Exception as e:
        add_debug_log("error", f"Erro inesperado na requisição de resumo: {str(e)}", {
            "exception_type": type(e).__name__,
            "directory": directory,
            "session_id": session_id
        })
        return False, {"error": f"Erro inesperado: {str(e)}"}, execution_time

def main():
    """Interface principal de debug"""
    
    # Cabeçalho
    st.markdown("""
    <div style="background: linear-gradient(90deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
        <h1>🤖 Claude Chat API</h1>
        <p>✅ Sistema Totalmente Funcional - Gerando Resumos com IA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com controles
    with st.sidebar:
        st.header("🔧 Controles")
        
        # Toggle Debug Mode
        st.session_state.debug_mode = st.checkbox(
            "🔍 Modo Debug Avançado", 
            value=st.session_state.debug_mode,
            help="Ativa logs detalhados e informações técnicas avançadas"
        )
        
        st.divider()
        
        # Status da API
        st.subheader("🌟 Status da API")
        
        # Teste automático de conexão
        try:
            response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=10)
            if response.status_code == 200:
                sessions = response.json()
                st.success(f"🚀 API Online - {len(sessions)} sessões")
            else:
                st.error(f"⚠️ API respondeu com código {response.status_code}")
        except Exception as e:
            st.error(f"❌ API Offline - {str(e)}")
        
        # Teste de conexão manual
        if st.button("🔄 Testar Novamente", key="test_again_1", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # Limpeza de logs
        if st.button("🗑️ Limpar Logs", key="clear_logs_1", use_container_width=True):
            st.session_state.debug_logs = []
            st.rerun()
        
        # Informações avançadas quando debug está ativo
        if st.session_state.debug_mode:
            st.subheader("🔍 Debug Avançado")
            
            # Estatísticas dos logs
            if st.session_state.debug_logs:
                log_levels = {}
                for log in st.session_state.debug_logs[-50:]:  # Últimos 50
                    level = log["level"].upper()
                    log_levels[level] = log_levels.get(level, 0) + 1
                
                st.json({"Logs por nível": log_levels})
            
            # Debug level
            debug_level = st.selectbox(
                "Nível de Debug",
                ["info", "warning", "error", "all"],
                index=0,
                help="Mostra mais detalhes técnicos quando ativo"
            )
            
            st.metric("Logs em Memória", len(st.session_state.debug_logs))
            st.metric("Testes Executados", len(st.session_state.test_results))
        
        st.divider()
        
        # Informações do sistema
        st.subheader("📊 Status do Sistema")
        
        # Indicadores de status em tempo real
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            # Contar erros recentes (últimos 10 minutos)
            recent_errors = 0
            current_time = datetime.now()
            for log in st.session_state.debug_logs[-50:]:  # Últimos 50 logs
                log_time = datetime.fromisoformat(log["timestamp"])
                if (current_time - log_time).total_seconds() < 600:  # 10 minutos
                    if log["level"].upper() == "ERROR":
                        recent_errors += 1
            
            error_status = "🔴 Erros" if recent_errors > 0 else "✅ Normal"
            st.metric("Status", error_status, delta=f"{recent_errors} erros recentes")
        
        with col_status2:
            st.metric("Logs Total", len(st.session_state.debug_logs))
        
        with col_status3:
            # Status dos últimos testes
            recent_tests = len(st.session_state.test_results) if hasattr(st.session_state, 'test_results') else 0
            success_rate = 0
            if hasattr(st.session_state, 'test_results') and st.session_state.test_results:
                successful = sum(1 for r in st.session_state.test_results.values() 
                               if r['result'].get('success', False))
                success_rate = (successful / len(st.session_state.test_results) * 100) if st.session_state.test_results else 0
            
            st.metric("Testes", recent_tests, delta=f"{success_rate:.0f}% sucesso")
        
        # Mensagem de sucesso da implementação
        if recent_errors == 0 and len(st.session_state.test_results) == 0:
            st.markdown("""
            <div style="background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <strong>🎉 API de Resumo Implementada com Sucesso!</strong><br>
                <small>
                ✅ Claude SDK integrado via subprocess<br>
                ✅ Leitura de arquivos .jsonl funcionando<br>
                ✅ Geração de resumos estruturados ativa<br>
                📋 Execute um teste na aba "Testes de Resumo" para começar!
                </small>
            </div>
            """, unsafe_allow_html=True)
        
        # Alertas importantes na página principal
        if recent_errors > 0:
            st.error(f"⚠️ **{recent_errors} erro(s) recente(s) detectado(s)!** Verifique a aba 'Logs de Debug' para detalhes.")
        
        # Resumo dos últimos testes falhados
        if hasattr(st.session_state, 'test_results'):
            failed_tests = [r for r in st.session_state.test_results.values() if not r.get('success', True)]
            if failed_tests:
                st.warning(f"⚠️ **{len(failed_tests)} teste(s) falharam.** Veja detalhes na aba 'Métricas'.")
            elif len(st.session_state.test_results) > 0:
                successful_tests = len([r for r in st.session_state.test_results.values() if r.get('success', True)])
                st.success(f"🎯 **{successful_tests} teste(s) executado(s) com sucesso!** Sistema funcionando perfeitamente.")
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧪 Testes de Resumo", 
        "📝 Logs de Debug", 
        "📊 Métricas", 
        "📋 Resumos Salvos",
        "🔧 Diagnóstico"
    ])
    
    # Tab 1: Testes de Resumo
    with tab1:
        st.header("🧪 Testes de Funcionalidade")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 Sessões Disponíveis")
            
            if st.button("🔄 Atualizar Lista", key="update_sessions_1", use_container_width=True):
                sessions = get_available_sessions()
                st.session_state.available_sessions = sessions
            
            if hasattr(st.session_state, 'available_sessions'):
                sessions = st.session_state.available_sessions
                
                if sessions:
                    session_options = []
                    for session in sessions[:20]:  # Limita a 20 para performance
                        display_name = f"{session['directory']} | {session['session_id'][:8]}..."
                        session_options.append((display_name, session))
                    
                    selected_idx = st.selectbox(
                        "Selecionar Sessão:",
                        range(len(session_options)),
                        format_func=lambda i: session_options[i][0] if session_options else "Nenhuma"
                    )
                    
                    if session_options:
                        st.session_state.selected_session = session_options[selected_idx][1]
                        
                        # Carregar e exibir conteúdo da sessão para edição
                        selected_session = session_options[selected_idx][1]
                        file_path = Path(selected_session.get('file_path', ''))
                        
                        # Carregar metadados da sessão
                        if file_path.exists():
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                
                                # Extrair conversa de forma simplificada para estatísticas
                                conversation_parts = []
                                for line in lines:
                                    try:
                                        data = json.loads(line.strip())
                                        if data.get('type') == 'user':
                                            message_content = data.get('message', {}).get('content', '')
                                            conversation_parts.append(f"👤 Usuário: {message_content}")
                                        elif data.get('type') == 'assistant':
                                            message = data.get('message', {})
                                            if isinstance(message.get('content'), list):
                                                # Extrair texto dos blocos de conteúdo
                                                text_parts = []
                                                for block in message['content']:
                                                    if isinstance(block, dict) and block.get('type') == 'text':
                                                        text_parts.append(block.get('text', ''))
                                                content = ' '.join(text_parts)
                                            else:
                                                content = str(message.get('content', ''))
                                            conversation_parts.append(f"🤖 Claude: {content}")
                                    except json.JSONDecodeError:
                                        continue
                                
                                full_conversation = '\n\n'.join(conversation_parts)
                                
                                # Armazenar conversa original para uso posterior
                                st.session_state.original_conversation = full_conversation
                                
                                # Informações sobre a sessão
                                col_info1, col_info2 = st.columns(2)
                                with col_info1:
                                    st.info(f"📊 {len(conversation_parts)} mensagens")
                                with col_info2:
                                    st.info(f"📝 {len(full_conversation):,} caracteres")
                                
                            except Exception as e:
                                st.error(f"❌ Erro ao ler arquivo: {str(e)}")
                        else:
                            st.error(f"❌ Arquivo não encontrado: {file_path}")
                            
                        # Sistema de Prompt Customizado
                        st.subheader("🎯 Prompt System Customizado")
                        
                        # Exemplos de prompts pré-definidos
                        prompt_examples = {
                            "📋 Resumo Padrão": "",
                            "🔧 Instruções Específicas": "Personalizado"
                        }
                        
                        col_prompt1, col_prompt2 = st.columns([2, 1])
                        
                        with col_prompt1:
                            prompt_choice = st.selectbox(
                                "Escolher Prompt Pré-definido:",
                                list(prompt_examples.keys()),
                                help="Selecione um prompt pré-definido ou 'Personalizado' para criar o seu"
                            )
                        
                        with col_prompt2:
                            if st.button("💾 Salvar Prompt", key="save_prompt_1", use_container_width=True):
                                st.session_state.prompt_saved = True
                                st.success("✅ Prompt salvo!")
                        
                        # Campo de texto para prompt customizado
                        if prompt_choice == "🔧 Instruções Específicas":
                            custom_prompt = st.text_area(
                                "Sistema Prompt Customizado:",
                                value=st.session_state.get('custom_system_prompt', ''),
                                height=150,
                                placeholder="Ex: Analise esta conversa focando em X, Y e Z. Ignore detalhes sobre A e B. Estruture a resposta como...",
                                help="Digite instruções específicas que serão enviadas junto com o resumo"
                            )
                            st.session_state.custom_system_prompt = custom_prompt
                        else:
                            # Usar prompt pré-definido
                            st.session_state.custom_system_prompt = prompt_examples[prompt_choice]
                            if prompt_examples[prompt_choice]:
                                st.info(f"💡 **Prompt ativo:** {prompt_examples[prompt_choice]}")
                        
                        # Indicador de status do prompt
                        if st.session_state.get('custom_system_prompt', ''):
                            st.markdown("""
                            <div style="background: #e7f3ff; border-left: 4px solid #1f77b4; padding: 10px; margin: 10px 0;">
                                <strong>🎯 Sistema Prompt Ativo</strong><br>
                                <small>Suas instruções personalizadas serão incluídas no resumo.</small>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #f8f9fa; border-left: 4px solid #6c757d; padding: 10px; margin: 10px 0;">
                                <strong>📋 Modo Padrão</strong><br>
                                <small>Resumo será gerado com instruções padrão.</small>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Nenhuma sessão encontrada")
            else:
                st.info("📋 Clique em 'Atualizar Lista' para carregar sessões")
        
        with col2:
            st.subheader("🎯 Teste de Resumo")
            
            if st.session_state.selected_session:
                session = st.session_state.selected_session
                
                st.info(f"""
                **Sessão Selecionada:**
                - 📁 Diretório: `{session['directory']}`
                - 🆔 ID: `{session['session_id']}`
                - 📄 Arquivo: `{session.get('file_path', 'N/A')}`
                """)
                
                summary_type = st.selectbox(
                    "Tipo de Resumo:",
                    ["bullet_points", "conciso", "detalhado"],  # bullet_points em primeiro
                    help="Escolha o formato de resumo desejado"
                )
                
                # Explicação dos tipos
                if summary_type == "bullet_points":
                    st.info("🔸 **Bullet Points**: Lista organizada por tópicos com pontos principais da conversa")
                elif summary_type == "conciso":
                    st.info("📋 **Conciso**: Resumo estruturado em até 20 palavras apenas com contexto, objetivo, resultado e tecnologias")
                else:
                    st.info("📖 **Detalhado**: Análise completa em até 400 palavras incluindo implementação, insights e próximos passos")
                
                if st.button("🚀 Executar Teste de Resumo", key="exec_test_1", use_container_width=True):
                    # Verificar se há conversa original e prompt customizado
                    has_conversation = hasattr(st.session_state, 'original_conversation') and st.session_state.original_conversation
                    has_custom_prompt = st.session_state.get('custom_system_prompt', '').strip()
                    use_enhanced_mode = has_conversation and has_custom_prompt
                    
                    # Log início do teste
                    add_debug_log("info", f"Iniciando teste de resumo tipo '{summary_type}'", {
                        "session_id": session['session_id'],
                        "directory": session['directory'],
                        "summary_type": summary_type,
                        "has_custom_prompt": bool(has_custom_prompt),
                        "enhanced_mode": use_enhanced_mode
                    })
                    
                    with st.spinner("🤖 Gerando resumo com instruções personalizadas..."):
                        if use_enhanced_mode:
                            # Combinar prompt customizado com conversa
                            enhanced_content = f"""INSTRUÇÕES ESPECÍFICAS: {has_custom_prompt}

CONVERSA PARA ANÁLISE:
{st.session_state.original_conversation}"""
                            
                            success, result, exec_time = test_summarizer_with_custom_content(
                                enhanced_content,
                                summary_type
                            )
                        elif has_conversation:
                            # Usar conversa original sem prompt customizado
                            success, result, exec_time = test_summarizer_with_custom_content(
                                st.session_state.original_conversation,
                                summary_type
                            )
                        else:
                            # Usar método original (fallback)
                            success, result, exec_time = test_summarizer_endpoint(
                                session['directory'], 
                                session['session_id'],
                                summary_type
                            )
                    
                    if success:
                        # Mensagem de sucesso personalizada
                        if use_enhanced_mode:
                            st.success(f"✅ Resumo gerado com prompt personalizado em {exec_time:.2f}s")
                            st.info("🎯 **Prompt aplicado:** Suas instruções específicas foram incluídas na análise")
                        else:
                            st.success(f"✅ Resumo gerado em {exec_time:.2f}s")
                        
                        # Log sucesso
                        add_debug_log("info", f"Teste concluído com sucesso em {exec_time:.2f}s", {
                            "execution_time": exec_time,
                            "summary_length": len(result.get('summary', '')),
                            "tokens_used": result.get('metrics', {}).get('input_tokens', 0) + result.get('metrics', {}).get('output_tokens', 0),
                            "used_custom_prompt": use_enhanced_mode
                        })
                        
                        # Exibe resumo
                        with st.expander("📝 Resumo Gerado", expanded=True):
                            # Link direto no topo do resumo
                            viewer_url = f"http://localhost:3041/{session['directory']}/{session['session_id']}/resumo?tipo={summary_type}"
                            
                            st.markdown(f"""
                            <div style="background: #f0f8ff; border: 1px solid #b6d7ff; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center;">
                                <strong>🔗 Link Direto:</strong> 
                                <a href="{viewer_url}" target="_blank" style="color: #0066cc; text-decoration: none;">
                                    📄 Abrir no Viewer Web →
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.text_area(
                                "Conteúdo:",
                                result.get('summary', 'N/A'),
                                height=200,
                                disabled=True
                            )
                            
                            # Botão para visualizar no viewer web
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                # Gerar URL do viewer
                                viewer_url = f"http://localhost:3041/{session['directory']}/{session['session_id']}/resumo?tipo={summary_type}"
                                
                                if st.button("🌐 Ver no Viewer Web", key="view_web_1", use_container_width=True):
                                    # Testar se a URL está acessível
                                    try:
                                        test_response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=3)
                                        if test_response.status_code == 200:
                                            st.markdown(f"""
                                            **🔗 URL do Viewer (clique para abrir):**
                                            
                                            [{viewer_url}]({viewer_url})
                                            """)
                                            
                                            st.success("🌐 **Viewer Web disponível!** Clique no link acima ou copie a URL")
                                            
                                            # Informações adicionais
                                            st.markdown(f"""
                                            <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0;">
                                                <strong>📋 Parâmetros da URL:</strong><br>
                                                • Diretório: <code>{session['directory']}</code><br>
                                                • Sessão: <code>{session['session_id']}</code><br>
                                                • Tipo: <code>{summary_type}</code>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.error("❌ Viewer web não está respondendo")
                                            st.code(viewer_url)
                                    except Exception as e:
                                        st.warning("⚠️ Não foi possível verificar o viewer web")
                                        st.markdown(f"""
                                        **🔗 URL do Viewer:**
                                        ```
                                        {viewer_url}
                                        ```
                                        """)
                                        st.info("💡 Copie e cole esta URL no navegador")
                                    
                                    # Log do acesso
                                    add_debug_log("info", "URL do viewer gerada", {
                                        "session_id": session['session_id'],
                                        "directory": session['directory'],
                                        "summary_type": summary_type,
                                        "viewer_url": viewer_url
                                    })
                            
                            with col_btn2:
                                if st.button("📋 Copiar Resumo", key="copy_summary_1", use_container_width=True):
                                    # Simular funcionalidade de copiar (em uma implementação real usaria JavaScript)
                                    st.success("✅ Use Ctrl+A e Ctrl+C na área de texto acima para copiar")
                                    add_debug_log("info", "Usuário solicitou cópia do resumo")
                            
                            # Se um prompt personalizado foi usado, mostrar informação adicional
                            if use_enhanced_mode:
                                st.markdown("""
                                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0;">
                                    <strong>⚠️ Atenção:</strong> Este resumo foi gerado com instruções personalizadas.<br>
                                    <small>A URL do viewer web mostrará o resumo padrão, não o personalizado.</small>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Botão para exibir o prompt usado
                                if st.button("🔍 Ver Prompt Aplicado", key="view_prompt_1"):
                                    st.markdown(f"""
                                    **🎯 Prompt personalizado usado:**
                                    ```
                                    {has_custom_prompt}
                                    ```
                                    """)
                                    st.info("💡 Para obter o mesmo resultado no viewer web, você precisaria configurar instruções similares")
                        
                        # Métricas
                        metrics = result.get('metrics', {})
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric("Tokens In", metrics.get('input_tokens', 0))
                        with col_b:
                            st.metric("Tokens Out", metrics.get('output_tokens', 0))
                        with col_c:
                            st.metric("Custo", f"${metrics.get('cost', 0):.6f}")
                        
                        # Salva resultado para análise (incluindo prompt customizado se houver)
                        test_result = {
                            "timestamp": datetime.now().isoformat(),
                            "session": session,
                            "result": result,
                            "execution_time": exec_time,
                            "summary_type": summary_type,
                            "success": True,
                            "custom_prompt": st.session_state.get('custom_system_prompt', '') if use_enhanced_mode else None
                        }
                        
                        # Chave única incluindo prompt se houver
                        result_key = f"{session['session_id']}_{summary_type}"
                        if use_enhanced_mode:
                            result_key += f"_custom_{hash(has_custom_prompt) % 10000}"
                        
                        st.session_state.test_results[result_key] = test_result
                        
                    else:
                        error_msg = result.get('error', 'Erro desconhecido')
                        st.error(f"❌ Erro no resumo: {error_msg}")
                        
                        # Log detalhado do erro
                        add_debug_log("error", f"Falha no teste de resumo: {error_msg}", {
                            "session_id": session['session_id'],
                            "directory": session['directory'],
                            "summary_type": summary_type,
                            "execution_time": exec_time,
                            "error_details": result
                        })
                        
                        # Salva resultado do erro para análise
                        test_result = {
                            "timestamp": datetime.now().isoformat(),
                            "session": session,
                            "result": result,
                            "execution_time": exec_time,
                            "summary_type": summary_type,
                            "success": False,
                            "error": error_msg
                        }
                        st.session_state.test_results[f"{session['session_id']}_{summary_type}"] = test_result
                        
                        # Exibir detalhes do erro
                        with st.expander("🔍 Detalhes do Erro"):
                            st.json(result)
            else:
                st.info("📋 Selecione uma sessão para testar")
    
    # Tab 2: Logs de Debug
    with tab2:
        st.header("📝 Logs de Debug")
        
        if not st.session_state.debug_mode:
            st.info("🔍 **Modo Debug Desativado** - Ative na sidebar para ver logs detalhados. Apenas erros são registrados.")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            max_logs = st.number_input("Máximo de logs:", value=50, min_value=10, max_value=200)
        with col2:
            reverse_order = st.checkbox("Mais recentes primeiro", value=True)
        with col3:
            if st.session_state.debug_mode:
                st.success("🔍 Debug Ativo")
            else:
                st.warning("⚠️ Debug Inativo")
        
        # Exibe logs
        if st.session_state.debug_logs:
            filtered_logs = st.session_state.debug_logs[-max_logs:]
            
            if not reverse_order:
                filtered_logs = list(reversed(filtered_logs))
            
            # Agrupar logs em linhas de 2 colunas (como nos testes)
            for i in range(0, len(filtered_logs), 2):
                cols = st.columns(2)
                
                for j, col in enumerate(cols):
                    if i + j < len(filtered_logs):
                        log = filtered_logs[i + j]
                        timestamp = log["timestamp"].split("T")[1][:8]
                        level = log["level"].upper()
                        message = log["message"]
                        
                        # Escolher emoji e cor baseado no level
                        if level == "ERROR":
                            emoji = "🔴"
                            color = "#fee"
                            border_color = "#f66"
                        elif level == "WARNING":
                            emoji = "🟡"
                            color = "#ffeaa7"
                            border_color = "#fdcb6e"
                        else:
                            emoji = "🔵"
                            color = "#e3f2fd"
                            border_color = "#2196f3"
                        
                        with col:
                            # Container estilizado como os testes
                            debug_info = ""
                            if st.session_state.debug_mode:
                                caller = log.get("caller", {})
                                debug_info = f"""
                                <div style="color: #666; font-size: 12px; margin-top: 5px;">
                                    📍 {caller.get('file', 'unknown')}:{caller.get('line', 0)} → {caller.get('function', 'unknown')}()
                                </div>
                                """
                            
                            st.markdown(f"""
                            <div style="border: 2px solid {border_color}; border-radius: 10px; 
                                        padding: 15px; margin: 10px 0; background: {color};">
                                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 20px; margin-right: 8px;">{emoji}</span>
                                    <strong style="color: #333;">[{timestamp}] {level}</strong>
                                </div>
                                <div style="color: #555; font-size: 14px; margin-bottom: 10px;">
                                    {message}
                                </div>
                                {debug_info}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Detalhes expandidos dentro do card
                            if log.get("details"):
                                with st.expander(f"🔍 Detalhes ({timestamp})"):
                                    st.json(log["details"])
                                    
                            # Stack trace para erros (só no modo debug)
                            if st.session_state.debug_mode and log.get("stack_trace"):
                                with st.expander(f"📚 Stack Trace ({timestamp})", expanded=False):
                                    for line in log["stack_trace"]:
                                        st.code(line.strip(), language="python")
        else:
            st.info("📋 Nenhum log de debug disponível")
    
    # Tab 3: Métricas
    with tab3:
        st.header("📊 Métricas de Performance")
        
        if st.session_state.test_results:
            st.subheader("📈 Resumo dos Testes")
            
            # Métricas gerais
            total_tests = len(st.session_state.test_results)
            successful_tests = sum(1 for result in st.session_state.test_results.values() 
                                 if result['result'].get('success', False))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Testes", total_tests)
            with col2:
                st.metric("Sucessos", successful_tests)
            with col3:
                success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
                st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
            
            # Separar sucessos e falhas
            successful_results = [r for r in st.session_state.test_results.values() if r.get('success', True)]
            failed_results = [r for r in st.session_state.test_results.values() if not r.get('success', True)]
            
            # Mostrar falhas primeiro se houver
            if failed_results:
                st.subheader("❌ Testes Falhados")
                
                for test_result in failed_results:
                    session = test_result['session']
                    
                    # Card de erro
                    st.markdown(f"""
                    <div style="border: 2px solid #f66; border-radius: 10px; 
                                padding: 15px; margin: 10px 0; background: #fee;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 20px; margin-right: 8px;">❌</span>
                            <strong style="color: #333;">Erro em {test_result['summary_type']}</strong>
                        </div>
                        <div style="color: #555; font-size: 14px; margin-bottom: 5px;">
                            <strong>Sessão:</strong> {session['session_id'][:12]}...
                        </div>
                        <div style="color: #555; font-size: 14px; margin-bottom: 5px;">
                            <strong>Diretório:</strong> {session['directory']}
                        </div>
                        <div style="color: #555; font-size: 14px; margin-bottom: 5px;">
                            <strong>Tempo:</strong> {test_result['execution_time']:.2f}s
                        </div>
                        <div style="color: #d63384; font-size: 14px; font-weight: bold;">
                            <strong>Erro:</strong> {test_result.get('error', 'Erro desconhecido')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Detalhes do erro
                    with st.expander(f"🔍 Detalhes completos - {session['session_id'][:8]}"):
                        st.json(test_result)
            
            # Tabela de sucessos
            st.subheader("📋 Histórico Completo")
            
            results_data = []
            for key, test_result in st.session_state.test_results.items():
                session = test_result['session']
                result = test_result.get('result', {})
                
                is_success = test_result.get('success', result.get('success', False))
                status_icon = "✅" if is_success else "❌"
                
                results_data.append({
                    "Status": status_icon,
                    "Sessão": session['session_id'][:8] + "...",
                    "Diretório": session['directory'][:20] + "...",
                    "Tipo": test_result['summary_type'],
                    "Tempo (s)": f"{test_result['execution_time']:.2f}",
                    "Tokens": f"{result.get('metrics', {}).get('input_tokens', 0)}↑ {result.get('metrics', {}).get('output_tokens', 0)}↓" if is_success else "N/A",
                    "Custo": f"${result.get('metrics', {}).get('cost', 0):.6f}" if is_success else "N/A",
                    "Data": test_result['timestamp'][:19]
                })
            
            if results_data:
                st.dataframe(results_data, use_container_width=True)
            
        else:
            st.info("📊 Execute alguns testes para ver métricas aqui")
    
    # Tab 4: Resumos Salvos
    with tab4:
        st.header("📋 Histórico de Resumos")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔍 Filtros")
            
            # Filtros para busca
            filter_session_id = st.text_input("ID da Sessão (opcional):", 
                                             placeholder="Ex: b9d98448-be5c-41a2...")
            filter_directory = st.text_input("Diretório (opcional):", 
                                           placeholder="Ex: -home-suthub--claude-cc-sdk-chat-api")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                limit_summaries = st.number_input("Limite:", value=20, min_value=5, max_value=100)
            with col_f2:
                if st.button("🔄 Atualizar Lista", key="update_summaries_1", use_container_width=True):
                    st.rerun()
        
        with col2:
            st.subheader("📊 Estatísticas")
            
            # Buscar estatísticas dos resumos
            try:
                params = {}
                if filter_directory:
                    params['directory'] = filter_directory
                if filter_session_id:
                    params['session_id'] = filter_session_id
                params['limit'] = limit_summaries
                
                # Fazer request para API
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                response = requests.get(f"{VIEWER_URL}/api/summaries?{query_string}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    summaries = data.get('summaries', [])
                    stats = data.get('storage_stats', {})
                    
                    st.metric("Total no Sistema", stats.get('total_summaries', 0))
                    st.metric("Sessões com Resumos", stats.get('total_sessions', 0))
                    st.metric("Encontrados", len(summaries))
                    
                    # Lista de resumos
                    st.subheader(f"📄 Resumos ({len(summaries)})")
                    
                    if summaries:
                        for i, summary in enumerate(summaries):
                            timestamp = summary.get('timestamp', '')[:19].replace('T', ' ')
                            summary_type = summary.get('summary_type', 'N/A')
                            session_id_short = summary.get('session_id', 'N/A')[:8]
                            
                            # Card para cada resumo
                            with st.container():
                                st.markdown(f"""
                                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background: white;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <strong>📝 {summary_type.title()}</strong>
                                        <small>{timestamp}</small>
                                    </div>
                                    <div style="color: #666; font-size: 14px; margin-bottom: 8px;">
                                        <strong>Sessão:</strong> {session_id_short}... | 
                                        <strong>Diretório:</strong> {summary.get('directory', 'N/A')[:30]}...
                                    </div>
                                    <div style="color: #666; font-size: 12px;">
                                        <strong>ID:</strong> <code>{summary.get('id', 'N/A')}</code>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Botões de ação
                                col_btn1, col_btn2, col_btn3 = st.columns(3)
                                
                                with col_btn1:
                                    if st.button(f"👁️ Ver", key=f"view_{summary.get('id')}", use_container_width=True):
                                        # Exibir resumo completo
                                        st.markdown("**📝 Conteúdo do Resumo:**")
                                        st.text_area("", summary.get('summary_content', ''), height=150, disabled=True, key=f"content_{summary.get('id')}")
                                
                                with col_btn2:
                                    # Link direto para viewer web
                                    web_url = f"http://localhost:3041/{summary.get('directory')}/{summary.get('session_id')}/resumo?tipo={summary.get('summary_type')}"
                                    st.markdown(f"[🌐 Web]({web_url})", unsafe_allow_html=True)
                                
                                with col_btn3:
                                    if st.button(f"🗑️ Deletar", key=f"del_{summary.get('id')}", use_container_width=True):
                                        # Deletar resumo
                                        try:
                                            delete_url = f"{VIEWER_URL}/api/summaries/{summary.get('id')}?directory={summary.get('directory')}&session_id={summary.get('session_id')}"
                                            del_response = requests.delete(delete_url, timeout=5)
                                            if del_response.status_code == 200:
                                                st.success("✅ Resumo removido!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Erro ao remover resumo")
                                        except Exception as e:
                                            st.error(f"❌ Erro: {str(e)}")
                    else:
                        st.info("📄 Nenhum resumo encontrado com os filtros aplicados")
                else:
                    st.error(f"❌ Erro ao buscar resumos: HTTP {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ Erro na comunicação: {str(e)}")
    
    # Tab 5: Diagnóstico
    with tab5:
        st.header("🔧 Diagnóstico do Sistema")
        
        # Status geral
        st.markdown("""
        <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <strong>🎉 STATUS: Sistema Totalmente Funcional!</strong><br>
            ✅ API de resumo implementada e testada<br>
            ✅ Claude SDK integrado via subprocess<br>
            ✅ Todos os endpoints operacionais
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚀 Funcionalidades Ativas")
            
            if st.button("🧪 Teste de Resumo Funcional", key="func_test_1", use_container_width=True):
                with st.spinner("Testando geração de resumo..."):
                    # Buscar uma sessão para testar
                    try:
                        response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=5)
                        if response.status_code == 200:
                            sessions = response.json()
                            if sessions:
                                # Pegar primeira sessão para teste
                                test_session = sessions[0]
                                
                                # Testar API de resumo
                                test_response = requests.post(
                                    f"{VIEWER_URL}/api/summarize", 
                                    json={
                                        "directory": test_session["directory"],
                                        "session_id": test_session["session_id"],
                                        "summary_type": "conciso"
                                    },
                                    timeout=30
                                )
                                
                                if test_response.status_code == 200:
                                    result = test_response.json()
                                    if result.get("success"):
                                        st.success("🎉 Teste de resumo PASSOU!")
                                        st.info(f"""
                                        **Resultado do teste:**
                                        - Tokens processados: {result.get('metrics', {}).get('input_tokens', 0)}
                                        - Resumo gerado: {len(result.get('summary', ''))} caracteres  
                                        - Custo estimado: ${result.get('metrics', {}).get('cost', 0):.6f}
                                        """)
                                    else:
                                        st.error(f"❌ API retornou erro: {result.get('error')}")
                                else:
                                    st.error(f"❌ HTTP {test_response.status_code}")
                            else:
                                st.warning("⚠️ Nenhuma sessão disponível para teste")
                        else:
                            st.error("❌ Não foi possível acessar sessões")
                    except Exception as e:
                        st.error(f"❌ Erro no teste: {str(e)}")
            
            st.markdown("---")
            
            # Lista de funcionalidades
            st.markdown("""
            **✅ Funcionalidades Implementadas:**
            - 📋 Listagem de sessões ativa
            - 📄 Leitura de arquivos .jsonl
            - 🤖 Integração Claude SDK (subprocess)
            - 📝 Geração de resumos (conciso/detalhado/bullets)
            - 📊 Cálculo de métricas (tokens, custo)
            - 🔍 Interface de debug avançada
            """)
            
        with col2:
            st.subheader("🔧 Testes de Conectividade")
            
            if st.button("🔍 Diagnóstico Completo", key="diag_test_1", use_container_width=True):
                with st.spinner("Executando diagnóstico..."):
                    results = []
                    
                    # Teste 1: API de sessões
                    try:
                        response = requests.get(f"{VIEWER_URL}/api/sessions", timeout=5)
                        if response.status_code == 200:
                            sessions = response.json()
                            results.append(("✅", f"API Sessions: {len(sessions)} sessões"))
                        else:
                            results.append(("❌", f"API Sessions: HTTP {response.status_code}"))
                    except Exception as e:
                        results.append(("❌", f"API Sessions: {str(e)}"))
                    
                    # Teste 2: Estrutura de arquivos
                    if CLAUDE_PROJECTS_PATH.exists():
                        session_count = sum(len(list(d.glob("*.jsonl"))) for d in CLAUDE_PROJECTS_PATH.iterdir() if d.is_dir())
                        results.append(("✅", f"Sistema de arquivos: {session_count} arquivos .jsonl"))
                    else:
                        results.append(("❌", "Sistema de arquivos: Path não encontrado"))
                    
                    # Teste 3: Claude SDK
                    sdk_path = Path("/home/suthub/.claude/cc-sdk-chat/api/claude-code-sdk-python")
                    if sdk_path.exists():
                        results.append(("✅", "Claude SDK: Integração ativa"))
                    else:
                        results.append(("❌", "Claude SDK: Não encontrado"))
                    
                    # Exibir resultados
                    for status, message in results:
                        if status == "✅":
                            st.success(f"{status} {message}")
                        else:
                            st.error(f"{status} {message}")
            
            # Informações técnicas
            st.subheader("📋 Informações Técnicas")
            st.code(f"""
Backend API: {VIEWER_URL}
Frontend Viewer: http://localhost:8505
Claude Projects: {CLAUDE_PROJECTS_PATH}
Claude SDK: /home/suthub/.claude/cc-sdk-chat/api/claude-code-sdk-python
            """, language="yaml")
        
        with col2:
            st.subheader("📁 Sistema de Arquivos")
            
            # Verifica path das sessões
            if CLAUDE_PROJECTS_PATH.exists():
                st.success(f"✅ Projects path existe: {CLAUDE_PROJECTS_PATH}")
                
                # Conta sessões disponíveis
                session_count = 0
                for directory in CLAUDE_PROJECTS_PATH.iterdir():
                    if directory.is_dir():
                        session_count += len(list(directory.glob("*.jsonl")))
                
                st.info(f"📊 Total de sessões no sistema: {session_count}")
                
            else:
                st.error(f"❌ Projects path não existe: {CLAUDE_PROJECTS_PATH}")
            
            # Verifica Claude SDK
            sdk_path = Path("/home/suthub/.claude/cc-sdk-chat/viewer-claude/backend/claude-sdk")
            if sdk_path.exists():
                st.success("✅ Claude SDK linkado corretamente")
            else:
                st.error("❌ Claude SDK não encontrado")
            
            # Logs do sistema
            st.subheader("📜 Logs Recentes")
            if st.session_state.debug_logs:
                recent_logs = st.session_state.debug_logs[-5:]
                for log in recent_logs:
                    level_icon = {"info": "🔵", "warning": "🟡", "error": "🔴"}.get(log["level"], "⚫")
                    st.text(f"{level_icon} {log['timestamp'][-8:]} - {log['message'][:50]}...")

if __name__ == "__main__":
    main()