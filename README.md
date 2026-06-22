# 🩺 Assistente Virtual - SMS Canoinhas/SC

Este projeto é uma aplicação funcional de Inteligência Artificial que utiliza a arquitetura **RAG (Retrieval-Augmented Generation)** para responder a dúvidas de cidadãos e profissionais de saúde baseando-se estritamente no **Protocolo de Inserção do Implante Contraceptivo Subdérmico de Etonogestrel (Implanon)** da Secretaria Municipal de Saúde de Canoinhas/SC.

O sistema foi desenvolvido em Python utilizando a infraestrutura de inferência de altíssima velocidade da **Groq** combinada com modelos locais de embeddings, mitigando alucinações ao delimitar o escopo das respostas estritamente ao documento oficial fornecido.

---

## 🛠️ Tecnologias Utilizadas

* **Python** (Linguagem base do ecossistema)
* **Streamlit** (Interface gráfica interativa de chat)
* **LangChain** (Orquestração das cadeias e carregamento de documentos)
* **FAISS** (Banco de dados vetorial local de alta performance)
* **Hugging Face Embeddings** (`paraphrase-multilingual-MiniLM-L12-v2` executado localmente para representação semântica em português)
* **Groq Cloud API** (Modelo avançado `llama-3.1-8b-instant` com temperatura $0.0$ para respostas exatas e determinísticas)

---

## ⚙️ Diferenciais do Sistema Integrado

1. **Diagnóstico em Tempo Real:** Validação dinâmica de leitura do arquivo PDF para assegurar que o arquivo não está corrompido ou composto apenas por imagens não indexadas (Scans).
2. **Arquitetura de Contingência Semântica:** Caso a busca vetorial padrão (FAISS) falhe em recuperar contexto suficiente (retornando `NÃO_ENCONTRADO`), o sistema ativa automaticamente um **Plano B** baseado em filtros de proximidade textual de strings para varrer as páginas do documento e enriquecer o contexto de forma dinâmica.
3. **Prevenção Rígida contra Alucinações:** Instruções de prompt em nível de sistema que forçam o modelo a admitir a falta de dados através de uma mensagem padrão de segurança caso a resposta não conste explicitamente no documento oficial.

---

## 🚀 Como Executar o Projeto Localmente

### 1. Clonar o Repositório e Preparar a Pasta
```bash
git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
cd SEU_REPOSITORIO