#!/usr/bin/env python3
"""
🎯 Streamlit Chat App - Interface Web para Claude Code SDK
Aplicativo web interativo com chat em tempo real
"""

import streamlit as st
import asyncio
import sys
import os
import logging
import traceback
import json
from datetime import datetime
from typing import List, Dict, Optional
import time

# Adiciona o diretório src ao path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

# Configuração da página
st.set_page_config(
    page_title="Claude Chat - SDK Python",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.stChatMessage {
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
}

.user-message {
    background-color: #e8f4fd;
    border-left: 4px solid #1f77b4;
}

.assistant-message {
    background-color: #f0f8f0;
    border-left: 4px solid #2ca02c;
}

.metrics-box {
    background-color: #f8f9fa;
    padding: 0.5rem;
    border-radius: 5px;
    font-size: 0.8rem;
    color: #666;
}

.title-container {
    text-align: center;
    padding: 1rem 0;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 2rem;
}

.debug-container {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 1rem;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    max-height: 300px;
    overflow-y: auto;
    margin: 1rem 0;
}

.error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 0.5rem;
    border-left: 4px solid #f44336;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.warning-message {
    background-color: #fff8e1;
    color: #ef6c00;
    padding: 0.5rem;
    border-left: 4px solid #ff9800;
    border-radius: 5px;
    margin: 0.5rem 0;
}

.success-message {
    background-color: #e8f5e8;
    color: #2e7d2e;
    padding: 0.5rem;
    border-left: 4px solid #4caf50;
    border-radius: 5px;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('streamlit_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Inicialização do estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    st.session_state.client = None
if "connected" not in st.session_state:
    st.session_state.connected = False
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = {"input": 0, "output": 0}
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []
if "performance_metrics" not in st.session_state:
    st.session_state.performance_metrics = []

def format_timestamp() -> str:
    """Formata timestamp para exibição"""
    return datetime.now().strftime("%H:%M:%S")

def add_debug_log(level: str, message: str, details: Optional[Dict] = None):
    """Adiciona log de debug ao estado da sessão"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "details": details or {}
    }
    
    st.session_state.debug_logs.append(log_entry)
    
    # Mantém apenas os últimos 100 logs
    if len(st.session_state.debug_logs) > 100:
        st.session_state.debug_logs = st.session_state.debug_logs[-100:]
    
    # Log também no arquivo
    logger_method = getattr(logger, level.lower(), logger.info)
    logger_method(f"{message} - Details: {details}")

def measure_performance(func_name: str):
    """Decorator para medir performance de funções"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Registra métrica de performance
                perf_metric = {
                    "function": func_name,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
                
                st.session_state.performance_metrics.append(perf_metric)
                add_debug_log("info", f"{func_name} executada", {
                    "execution_time": f"{execution_time:.3f}s",
                    "status": "success"
                })
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                
                perf_metric = {
                    "function": func_name,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                }
                
                st.session_state.performance_metrics.append(perf_metric)
                add_debug_log("error", f"Erro em {func_name}", {
                    "execution_time": f"{execution_time:.3f}s",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                
                raise e
        return wrapper
    return decorator

def get_system_info() -> Dict:
    """Coleta informações do sistema para debug"""
    return {
        "python_version": sys.version,
        "streamlit_version": st.__version__,
        "current_time": datetime.now().isoformat(),
        "session_state_keys": list(st.session_state.keys()),
        "messages_count": len(st.session_state.messages),
        "debug_logs_count": len(st.session_state.debug_logs),
        "performance_metrics_count": len(st.session_state.performance_metrics)
    }

def format_debug_message(log_entry: Dict) -> str:
    """Formata mensagem de debug para exibição"""
    timestamp = log_entry["timestamp"].split("T")[1][:8]
    level = log_entry["level"].upper()
    message = log_entry["message"]
    
    level_colors = {
        "ERROR": "🔴",
        "WARNING": "🟡", 
        "INFO": "🔵",
        "DEBUG": "⚫"
    }
    
    icon = level_colors.get(level, "⚫")
    return f"{icon} [{timestamp}] {level}: {message}"

@measure_performance("connect_client")
async def connect_client():
    """Conecta ao cliente Claude"""
    add_debug_log("info", "Tentando conectar ao cliente Claude")
    
    try:
        if not st.session_state.client:
            add_debug_log("debug", "Criando nova instância do ClaudeSDKClient")
            st.session_state.client = ClaudeSDKClient()
        
        if not st.session_state.connected:
            add_debug_log("debug", "Iniciando conexão com Claude")
            await st.session_state.client.connect()
            st.session_state.connected = True
            add_debug_log("info", "Conexão estabelecida com sucesso")
        else:
            add_debug_log("debug", "Cliente já conectado")
        
        return True
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        add_debug_log("error", "Falha ao conectar cliente", error_details)
        st.error(f"❌ Erro ao conectar: {e}")
        return False

@measure_performance("disconnect_client")
async def disconnect_client():
    """Desconecta do cliente"""
    add_debug_log("info", "Desconectando cliente Claude")
    
    try:
        if st.session_state.client and st.session_state.connected:
            add_debug_log("debug", "Fechando conexão existente")
            await st.session_state.client.disconnect()
            add_debug_log("info", "Cliente desconectado com sucesso")
        else:
            add_debug_log("debug", "Nenhuma conexão ativa para desconectar")
            
        st.session_state.connected = False
        st.session_state.client = None
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        add_debug_log("error", "Erro ao desconectar cliente", error_details)
        st.error(f"⚠️ Erro ao desconectar: {e}")

@measure_performance("send_message")
async def send_message(prompt: str):
    """Envia mensagem para o Claude"""
    add_debug_log("info", "Iniciando envio de mensagem", {
        "prompt_length": len(prompt),
        "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt
    })
    
    if not await connect_client():
        add_debug_log("error", "Falha na conexão, abortando envio")
        return
    
    # Adiciona mensagem do usuário
    user_msg = {
        "role": "user",
        "content": prompt,
        "timestamp": format_timestamp()
    }
    st.session_state.messages.append(user_msg)
    add_debug_log("debug", "Mensagem do usuário adicionada", {"message_id": len(st.session_state.messages)})
    
    try:
        # Envia query
        add_debug_log("debug", "Enviando query para Claude")
        await st.session_state.client.query(prompt)
        
        # Coleta resposta
        response_content = []
        usage_info = None
        cost_info = None
        response_start_time = time.time()
        
        add_debug_log("debug", "Iniciando coleta de resposta")
        
        async for message in st.session_state.client.receive_response():
            if isinstance(message, AssistantMessage):
                add_debug_log("debug", "Recebida mensagem do assistente", {"content_blocks": len(message.content)})
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_content.append(block.text)
            elif isinstance(message, ResultMessage):
                add_debug_log("debug", "Recebida mensagem de resultado")
                if hasattr(message, 'usage') and message.usage:
                    usage_info = message.usage
                    add_debug_log("debug", "Informações de uso coletadas", {
                        "input_tokens": getattr(usage_info, 'input_tokens', 'N/A'),
                        "output_tokens": getattr(usage_info, 'output_tokens', 'N/A')
                    })
                if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                    cost_info = message.total_cost_usd
                    add_debug_log("debug", "Custo coletado", {"cost": cost_info})
        
        response_time = time.time() - response_start_time
        add_debug_log("info", "Resposta coletada com sucesso", {
            "response_time": f"{response_time:.3f}s",
            "content_parts": len(response_content)
        })
        
        # Adiciona resposta do assistente
        full_response = "\n".join(response_content)
        if full_response.strip():
            assistant_msg = {
                "role": "assistant",
                "content": full_response,
                "timestamp": format_timestamp(),
                "usage": usage_info,
                "cost": cost_info,
                "response_time": response_time
            }
            st.session_state.messages.append(assistant_msg)
            
            # Atualiza totais
            if usage_info:
                if hasattr(usage_info, 'input_tokens'):
                    input_tokens = usage_info.input_tokens or 0
                    output_tokens = usage_info.output_tokens or 0
                elif isinstance(usage_info, dict):
                    input_tokens = usage_info.get('input_tokens', 0)
                    output_tokens = usage_info.get('output_tokens', 0)
                else:
                    input_tokens = output_tokens = 0
                
                st.session_state.total_tokens["input"] += input_tokens
                st.session_state.total_tokens["output"] += output_tokens
                
                add_debug_log("debug", "Tokens atualizados", {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_input": st.session_state.total_tokens["input"],
                    "total_output": st.session_state.total_tokens["output"]
                })
            
            if cost_info:
                st.session_state.total_cost += cost_info
                add_debug_log("debug", "Custo atualizado", {
                    "message_cost": cost_info,
                    "total_cost": st.session_state.total_cost
                })
        else:
            add_debug_log("warning", "Resposta vazia recebida do Claude")
        
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "prompt_length": len(prompt)
        }
        add_debug_log("error", "Erro ao processar mensagem", error_details)
        st.error(f"❌ Erro ao enviar mensagem: {e}")
        
        # Tenta reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "disconnect" in str(e).lower():
            add_debug_log("warning", "Tentando reconexão devido a erro de conexão")
            st.session_state.connected = False
            st.session_state.client = None

def clear_conversation():
    """Limpa a conversa e reinicia o cliente"""
    add_debug_log("info", "Limpando conversa e reiniciando cliente")
    
    # Salva estatísticas antes de limpar
    prev_stats = {
        "messages_count": len(st.session_state.messages),
        "total_input_tokens": st.session_state.total_tokens["input"],
        "total_output_tokens": st.session_state.total_tokens["output"],
        "total_cost": st.session_state.total_cost
    }
    
    add_debug_log("debug", "Estatísticas da sessão anterior", prev_stats)
    
    try:
        # Desconecta usando novo loop para evitar conflitos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(disconnect_client())
        finally:
            loop.close()
    except Exception as e:
        add_debug_log("warning", "Erro ao desconectar na limpeza", {"error": str(e)})
    
    st.session_state.messages = []
    st.session_state.client = None
    st.session_state.connected = False
    st.session_state.total_tokens = {"input": 0, "output": 0}
    st.session_state.total_cost = 0.0
    
    add_debug_log("info", "Conversa limpa com sucesso")

def render_debug_panel():
    """Renderiza painel de debug avançado"""
    if not st.session_state.debug_mode:
        return
    
    with st.expander("🔍 Debug Panel - Sistema Avançado", expanded=False):
        debug_tab1, debug_tab2, debug_tab3, debug_tab4 = st.tabs([
            "📝 Logs", 
            "📈 Performance", 
            "🔧 Sistema", 
            "📊 Métricas"
        ])
        
        # Tab 1: Logs
        with debug_tab1:
            st.subheader("📝 Logs de Debug")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                log_levels = st.multiselect(
                    "Filtrar por nível:",
                    ["ERROR", "WARNING", "INFO", "DEBUG"],
                    default=["ERROR", "WARNING", "INFO"]
                )
            with col2:
                max_logs = st.number_input("Máx logs:", value=20, min_value=5, max_value=100)
            with col3:
                if st.button("🗑️ Limpar Logs"):
                    st.session_state.debug_logs = []
                    st.rerun()
            
            # Exibe logs filtrados
            filtered_logs = [
                log for log in st.session_state.debug_logs[-max_logs:]
                if log["level"].upper() in log_levels
            ]
            
            if filtered_logs:
                log_container = st.container()
                with log_container:
                    st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                    for log in reversed(filtered_logs[-20:]):
                        formatted_msg = format_debug_message(log)
                        
                        if log["level"] == "error":
                            st.markdown(f'<div class="error-message">{formatted_msg}</div>', unsafe_allow_html=True)
                            if log["details"].get("traceback"):
                                with st.expander("Ver Traceback"):
                                    st.code(log["details"]["traceback"], language="python")
                        elif log["level"] == "warning":
                            st.markdown(f'<div class="warning-message">{formatted_msg}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="success-message">{formatted_msg}</div>', unsafe_allow_html=True)
                        
                        # Detalhes expandidos
                        if log["details"] and st.checkbox(f"Detalhes - {log['timestamp'][-8:]}", key=f"details_{log['timestamp']}"):
                            st.json(log["details"])
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("📋 Nenhum log disponível com os filtros selecionados")
        
        # Tab 2: Performance
        with debug_tab2:
            st.subheader("📈 Métricas de Performance")
            
            if st.session_state.performance_metrics:
                # Estatísticas gerais
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_time = sum(m["execution_time"] for m in st.session_state.performance_metrics) / len(st.session_state.performance_metrics)
                    st.metric("Tempo Médio", f"{avg_time:.3f}s")
                
                with col2:
                    max_time = max(m["execution_time"] for m in st.session_state.performance_metrics)
                    st.metric("Tempo Máximo", f"{max_time:.3f}s")
                
                with col3:
                    success_rate = sum(1 for m in st.session_state.performance_metrics if m["status"] == "success") / len(st.session_state.performance_metrics) * 100
                    st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
                
                with col4:
                    total_calls = len(st.session_state.performance_metrics)
                    st.metric("Total Chamadas", total_calls)
                
                # Tabela detalhada
                st.subheader("Detalhes por Função")
                perf_data = []
                for metric in st.session_state.performance_metrics[-20:]:
                    perf_data.append({
                        "Função": metric["function"],
                        "Tempo (s)": f"{metric['execution_time']:.3f}",
                        "Status": "✅" if metric["status"] == "success" else "❌",
                        "Hora": metric["timestamp"][-8:],
                        "Erro": metric.get("error", "-")
                    })
                
                if perf_data:
                    st.dataframe(perf_data, use_container_width=True)
            else:
                st.info("📊 Nenhuma métrica de performance coletada ainda")
        
        # Tab 3: Sistema
        with debug_tab3:
            st.subheader("🔧 Informações do Sistema")
            
            system_info = get_system_info()
            
            col1, col2 = st.columns(2)
            with col1:
                st.json({
                    "Python Version": system_info["python_version"].split()[0],
                    "Streamlit Version": system_info["streamlit_version"],
                    "Current Time": system_info["current_time"]
                })
            
            with col2:
                st.json({
                    "Messages Count": system_info["messages_count"],
                    "Debug Logs Count": system_info["debug_logs_count"],
                    "Performance Metrics Count": system_info["performance_metrics_count"],
                    "Session State Keys": len(system_info["session_state_keys"])
                })
            
            if st.button("📋 Exportar Debug Info"):
                debug_export = {
                    "system_info": system_info,
                    "debug_logs": st.session_state.debug_logs[-50:],
                    "performance_metrics": st.session_state.performance_metrics[-50:],
                    "export_time": datetime.now().isoformat()
                }
                
                st.download_button(
                    label="💾 Download Debug JSON",
                    data=json.dumps(debug_export, indent=2),
                    file_name=f"streamlit_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Tab 4: Métricas
        with debug_tab4:
            st.subheader("📊 Métricas da Sessão")
            
            if st.session_state.messages:
                # Métricas de tokens por mensagem
                message_metrics = []
                for i, msg in enumerate(st.session_state.messages):
                    if msg["role"] == "assistant" and msg.get("usage"):
                        usage = msg["usage"]
                        if hasattr(usage, 'input_tokens'):
                            input_tokens = usage.input_tokens or 0
                            output_tokens = usage.output_tokens or 0
                        elif isinstance(usage, dict):
                            input_tokens = usage.get('input_tokens', 0)
                            output_tokens = usage.get('output_tokens', 0)
                        else:
                            input_tokens = output_tokens = 0
                        
                        message_metrics.append({
                            "Mensagem": i//2 + 1,
                            "Input Tokens": input_tokens,
                            "Output Tokens": output_tokens,
                            "Total Tokens": input_tokens + output_tokens,
                            "Custo": f"${msg.get('cost', 0):.6f}",
                            "Tempo Resposta": f"{msg.get('response_time', 0):.2f}s"
                        })
                
                if message_metrics:
                    st.dataframe(message_metrics, use_container_width=True)
                    
                    # Gráfico de tokens
                    if len(message_metrics) > 1:
                        import pandas as pd
                        df = pd.DataFrame(message_metrics)
                        st.line_chart(df.set_index('Mensagem')[['Input Tokens', 'Output Tokens']])
                else:
                    st.info("📊 Nenhuma métrica de mensagem disponível")
            else:
                st.info("💬 Nenhuma mensagem na sessão atual")

def check_and_reconnect():
    """Verifica e reconecta automaticamente se necessário"""
    if not st.session_state.connected or not st.session_state.client:
        add_debug_log("warning", "Conexão não ativa, iniciando reconexão automática")
        # Força uma nova conexão na próxima interação
        st.session_state.connected = False
        st.session_state.client = None
        return False
    return True

def main():
    """Função principal do aplicativo"""
    
    # Verifica reconexão no início
    check_and_reconnect()
    
    # Adiciona log de início de sessão
    if len(st.session_state.debug_logs) == 0:
        add_debug_log("info", "Aplicativo Streamlit iniciado", get_system_info())
    
    # Cabeçalho
    st.markdown("""
    <div class="title-container">
        <h1>🤖 Claude Chat - SDK Python</h1>
        <p>Interface Web Interativa para Claude Code SDK</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com controles
    with st.sidebar:
        st.header("⚙️ Controles")
        
        # Status da conexão com debug
        connection_status = "Conectado" if st.session_state.connected else "Desconectado"
        if st.session_state.connected:
            st.success(f"🟢 {connection_status}")
        else:
            st.error(f"🔴 {connection_status}")
            if st.button("🔄 Reconectar Agora"):
                add_debug_log("info", "Reconexão manual solicitada")
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(connect_client())
                        add_debug_log("info", "Reconexão manual completada")
                    finally:
                        loop.close()
                except Exception as e:
                    add_debug_log("error", "Erro na reconexão manual", {
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
                    st.error(f"❌ Erro na reconexão: {str(e)[:50]}...")
                st.rerun()
        
        # Toggle Debug Mode
        st.session_state.debug_mode = st.checkbox(
            "🔍 Modo Debug", 
            value=st.session_state.debug_mode,
            help="Ativa painel de debug avançado com logs detalhados"
        )
        
        # Botões de controle
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Nova Conversa", use_container_width=True):
                clear_conversation()
                st.rerun()
        
        with col2:
            if st.button("🚪 Desconectar", use_container_width=True):
                asyncio.create_task(disconnect_client())
                st.rerun()
        
        # Métricas
        st.header("📊 Estatísticas")
        
        total_input = st.session_state.total_tokens["input"]
        total_output = st.session_state.total_tokens["output"]
        total_cost = st.session_state.total_cost
        
        st.metric("Tokens de Entrada", f"{total_input:,}")
        st.metric("Tokens de Saída", f"{total_output:,}")
        st.metric("Custo Total", f"${total_cost:.6f}")
        
        # Informações
        st.header("ℹ️ Informações")
        st.info("""
        **Como usar:**
        1. Digite sua mensagem na caixa abaixo
        2. Pressione Enter ou clique em Enviar
        3. Aguarde a resposta do Claude
        4. Continue a conversa normalmente
        
        **Comandos especiais:**
        - Use 'Nova Conversa' para limpar o contexto
        - Use 'Desconectar' para encerrar a sessão
        """)
    
    # Painel de Debug (se ativado)
    render_debug_panel()
    
    # Área principal do chat
    st.header("💬 Conversa")
    
    # Container para mensagens
    messages_container = st.container()
    
    # Exibe mensagens
    with messages_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="stChatMessage user-message">
                    <strong>👤 Você ({msg['timestamp']}):</strong><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Monta informações de métricas
                metrics_info = ""
                if msg.get('usage'):
                    usage = msg['usage']
                    if hasattr(usage, 'input_tokens'):
                        metrics_info = f"Tokens: {usage.input_tokens}↑ {usage.output_tokens}↓"
                    elif isinstance(usage, dict):
                        metrics_info = f"Tokens: {usage.get('input_tokens', 0)}↑ {usage.get('output_tokens', 0)}↓"
                
                if msg.get('cost'):
                    cost_info = f"Custo: ${msg['cost']:.6f}"
                    metrics_info = f"{metrics_info} | {cost_info}" if metrics_info else cost_info
                
                metrics_box = f'<div class="metrics-box">{metrics_info}</div>' if metrics_info else ""
                
                st.markdown(f"""
                <div class="stChatMessage assistant-message">
                    <strong>🤖 Claude ({msg['timestamp']}):</strong><br>
                    {msg['content'].replace(chr(10), '<br>')}
                    {metrics_box}
                </div>
                """, unsafe_allow_html=True)
    
    # Input para nova mensagem
    st.header("✍️ Nova Mensagem")
    
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Digite sua mensagem:",
            placeholder="Olá Claude! Como você pode me ajudar hoje?",
            height=100,
            key="user_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            send_button = st.form_submit_button("📨 Enviar", use_container_width=True)
        
        with col2:
            example_button = st.form_submit_button("💡 Exemplo", use_container_width=True)
    
    # Processa envio
    if send_button and user_input.strip():
        add_debug_log("info", "Usuário iniciou envio de mensagem")
        with st.spinner("🤖 Claude está pensando..."):
            try:
                # Usa asyncio.create_task para evitar conflitos de loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(send_message(user_input.strip()))
                    add_debug_log("info", "Mensagem processada com sucesso")
                finally:
                    loop.close()
            except Exception as e:
                add_debug_log("error", "Erro no processamento da mensagem", {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                st.error(f"❌ Erro: {str(e)[:100]}...")
        st.rerun()
    
    # Processa exemplo
    if example_button:
        example_prompt = "Olá Claude! Você pode me ajudar com uma tarefa de programação Python?"
        add_debug_log("info", "Exemplo enviado pelo usuário")
        with st.spinner("🤖 Claude está pensando..."):
            try:
                # Usa asyncio.create_task para evitar conflitos de loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(send_message(example_prompt))
                    add_debug_log("info", "Exemplo processado com sucesso")
                finally:
                    loop.close()
            except Exception as e:
                add_debug_log("error", "Erro no processamento do exemplo", {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                st.error(f"❌ Erro: {str(e)[:100]}...")
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        🚀 Claude Code SDK Python - Interface Streamlit<br>
        Desenvolvido com ❤️ usando Streamlit
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()