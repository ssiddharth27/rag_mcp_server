from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
import os
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
persist_path = "faiss_mcp"
def load_qa_chain():

    custom_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
        You are a knowledgeable and helpful assistant that explains technical content and generates code when required.

        Use the information provided in the context below as your **primary reference** to answer the user's question **clearly and accurately**.

        ⚠️ Guidelines:
        - If the context includes references like "Clause 9.1.2.2" or "Table 6.2.1.3.11", do NOT just mention these references.
        - Instead, explain the actual content or meaning described in those clauses or tables, **based only on what's given in the context**.
        - If the context does NOT contain enough detail to answer the question, use your best understanding and general technical knowledge to respond.
        - If the question asks for code, provide the most appropriate and working code snippet, even if the context does not include code examples.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        )
    # model = GoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.environ["GOOGLE_API_KEY"], temperature=0.4)
    # model = ChatGroq(groq_api_key=os.environ["GROQ_API_KEY"], model_name = "llama-3.1-8b-instant")
    model = ChatGroq(groq_api_key=os.environ["GROQ_API_KEY"], model_name = "openai/gpt-oss-120b")
    # llm = Ollama(model="deepseek-r1:14b", temperature=0.4)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vectorstore = FAISS.load_local(persist_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 7})
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=model,
        retriever=retriever,
        chain_type_kwargs={"prompt": custom_prompt},
        return_source_documents=True
    )
    return qa_chain

chain = load_qa_chain()

def ask_rag_question(question: str) -> str:
    result = chain(question)
    # print("\nAnswer:\n")
    return result['result']

    # print("\nSources:\n")
    # for doc in result['source_documents']:
    #     print(" -", doc.metadata.get("source", "N/A"))
    # return result

