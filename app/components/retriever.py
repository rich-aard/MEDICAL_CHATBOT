from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.components.llm import load_llm
from app.components.vector_store import load_vector_store


logger = get_logger(__name__)

CUSTOM_PROMPT_TEMPLATE = """Answer the following medical question in 2-3 lines maximum using only the information provided in the context. If you do not know the answer based on the context, say that you don't know.

Context:
{context}

Question:
{question}

Answer:
"""


def set_custom_prompt() -> PromptTemplate:
    return PromptTemplate(
        template=CUSTOM_PROMPT_TEMPLATE, input_variables=["context", "question"]
    )


def format_docs(docs):
    """Helper function to combine retrieved document chunks into one string."""
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_qa_chain():
    try:
        logger.info("Loading vector store for QA chain...")
        vector_store = load_vector_store()

        if vector_store is None:
            raise CustomException("Vector store initialization returned None.")

        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        logger.info("Loading Groq Chat model...")
        llm = load_llm()

        if llm is None:
            raise CustomException("LLM initialization returned None.")

        prompt = set_custom_prompt()

        logger.info("Combining to RAG Chain..")

        qa_rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        logger.info("RAG QA Chain created successfully.")

        return qa_rag_chain

    except Exception as e:
        err_mesg = CustomException("Failed to make a QA chain", original_error=e)
        logger.error(str(err_mesg))
        raise err_mesg
