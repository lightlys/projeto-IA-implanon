import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# configuração visual da página do Streamlit
st.set_page_config(
    page_title="Assistente Virtual - SUS Canoinhas", 
    page_icon="🩺", 
    layout="centered"
)

st.title("🩺 Assistente Virtual — Implanon")
st.caption("Secretaria Municipal de Saúde • Canoinhas/SC")
st.markdown(
    "Olá! Estou aqui para esclarecer suas dúvidas sobre o protocolo municipal de inserção do implante contraceptivo (Implanon)."
)

st.info(
    "**📌 Escopo de Resposta:** Minhas respostas são baseadas **estritamente** no documento oficial do município para garantir total segurança e evitar informações incorretas."
)

# chave API gerada pelo Grok
CHAVE_PADRAO = ""

# verifica se há chave no sistema, se não, usa a colada acima
api_key = os.getenv("GROQ_API_KEY", CHAVE_PADRAO)

PDF_PATH = "Protocolo - Inserção de Implante Contraceptivo Subdérmico de Etonogestrel - Implanon.pdf"

@st.cache_resource
def inicializar_base_conhecimento(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        st.error(f"Erro: O arquivo '{caminho_pdf}' não foi encontrado na pasta do projeto.")
        return None, None

    try:
        # 1. Carregador de PDF e Divisor
        loader = PyPDFLoader(caminho_pdf)
        paginas = loader.load()
        
        # --- DIAGNÓSTICO DO PDF ---
        texto_extraido_total = "".join([p.page_content for p in paginas]).strip()
        if not texto_extraido_total:
            st.error("⚠️ ATENÇÃO: O PDF foi lido, mas nenhum texto foi extraído!")
            return None, None
        else:
            st.success(f"✅ PDF carregado! {len(paginas)} páginas encontradas. Caracteres lidos: {len(texto_extraido_total)}")
        # ---------------------------

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(paginas)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        vector_store = FAISS.from_documents(docs, embeddings)
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 6})
        
        return retriever, paginas
    
    except Exception as e:
        st.error(f"Erro ao processar o PDF: {e}")
        return None, None

# Inicializa as duas estruturas de busca do PDF
retriever, lista_paginas_pdf = inicializar_base_conhecimento(PDF_PATH)

if retriever and lista_paginas_pdf:
    # Gerenciamento do histórico do chat
    if "mensagens" not in st.session_state:
        st.session_state.mensagens = []

    for msg in st.session_state.mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Campo de entrada de perguntas
    if pergunta_usuario := st.chat_input("Ex: Quais os critérios para receber o Implanon?"):
        st.session_state.mensagens.append({"role": "user", "content": pergunta_usuario})
        with st.chat_message("user"):
            st.markdown(pergunta_usuario)

        with st.chat_message("assistant"):
            with st.spinner("Consultando o Protocolo Municipal..."):
                try:
                    # Inicializa o cliente LLM garantindo o envio correto da chave api_key
                    llm = ChatGroq(
                        model="llama-3.1-8b-instant", 
                        groq_api_key=api_key, 
                        temperature=0.0
                    )

                    # TENTATIVA 1: Busca Semântica Padrão (FAISS)
                    trechos_encontrados = retriever.invoke(pergunta_usuario)
                    contexto = "\n\n".join([doc.page_content for doc in trechos_encontrados])

                    # Depurador do FAISS
                    with st.expander("🔍 Ver trechos recuperados pelo FAISS para esta pergunta"):
                        st.write(contexto if contexto.strip() else "Nenhum trecho foi recuperado pelo FAISS.")

                    # Prompt para a tentativa com FAISS
                    prompt_faiss = (
                        "Você é um assistente virtual especializado da Secretaria Municipal de Saúde de Canoinhas/SC.\n"
                        "Sua função é responder dúvidas com base nos trechos do protocolo fornecidos abaixo.\n"
                        "REGRA: Se a resposta exata não puder ser respondida com os trechos abaixo, retorne EXATAMENTE a palavra: 'NÃO_ENCONTRADO'\n\n"
                        f"Trechos do Protocolo:\n{contexto}\n\n"
                        f"Pergunta: {pergunta_usuario}"
                    )
                    
                    response = llm.invoke(prompt_faiss)
                    resposta_final = response.content

                    # TENTATIVA 2 (PLANO B): Filtro inteligente por correspondência de strings (Evita Erro 413)
                    if "NÃO_ENCONTRADO" in resposta_final or len(resposta_final.strip()) < 15:
                        with st.info("Filtrando e analisando páginas relevantes do protocolo..."):
                            
                            termos_busca = ["idade", "anos", "critério", "elegibilidade", "adolescente", "público", "mulher", "faixa"]
                            paginas_filtradas = []
                            
                            for idx, pagina in enumerate(lista_paginas_pdf):
                                conteudo = pagina.page_content.lower()
                                if any(termo in conteudo for termo in termos_busca) or any(palavra.lower() in conteudo for palavra in pergunta_usuario.split() if len(palavra) > 4):
                                    paginas_filtradas.append(f"[Página {idx+1}]\n{pagina.page_content}")
                            
                            # Une no máximo 3 páginas para ficar totalmente seguro contra limites de tokens
                            contexto_filtrado = "\n\n---\n\n".join(paginas_filtradas[:3])
                            
                            prompt_filtro = (
                                "Você é um assistente virtual especializado da Secretaria Municipal de Saúde de Canoinhas/SC.\n"
                                "Analise os trechos de páginas selecionadas do protocolo municipal abaixo para responder à pergunta de forma exata.\n"
                                "Se mesmo nessas páginas a informação não existir, diga exatamente: 'Desculpe, mas não encontrei essa informação no documento fornecido.'\n\n"
                                f"--- TRECHOS SELECIONADOS ---\n{contexto_filtrado}\n\n"
                                f"Pergunta do usuário: {pergunta_usuario}"
                            )
                            
                            response = llm.invoke(prompt_filtro)
                            resposta_final = response.content
                    
                    st.markdown(resposta_final)
                    st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})
                    
                except Exception as e:
                    st.error(f"Ocorreu um erro na comunicação com a API da Groq: {e}")