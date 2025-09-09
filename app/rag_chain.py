from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.llms import LLM
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.vectorstores import VectorStoreRetriever


def create_rag_chain(retriever: VectorStoreRetriever, llm: LLM) -> Runnable:
    """
    Creates a Retrieval-Augmented Generation (RAG) chain.

    Args:
        retriever: The retriever object to fetch relevant documents.
        llm: The language model to generate the answer.

    Returns:
        A runnable chain object.
    """
    # This prompt template is structured to guide the LLM to answer
    # based on the provided context.
    template = """
    You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.

    Question: {question}
    Context: {context}
    Answer:
    """
    prompt = ChatPromptTemplate.from_template(template)

    # This chain uses LangChain Expression Language (LCEL)
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
