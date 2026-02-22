from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
import os
from langchain_community.llms import LlamaCpp

from chunking_embedding import retriever_function
from semantic_caching import search_cache, store_in_chroma, generate_cache_id, save_cache_to_chat_history, get_from_chat_history



def load_llm():
    local_llm = LlamaCpp(
        #model_path=r"models\Phi-3-mini-4k-instruct-q4.gguf",
        # model_path=r"models\llama-2-7b-chat.Q4_K_M.gguf", 
        # model_path=r"models\mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        # model_path=r"models\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        #model_path=r"models\mistral-4.2B.Q4_K.gguf",
        model_path=r"models\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        n_ctx=2048,
        n_threads=6,
        n_gpu_layers=0,
        temperature=0.3,
        max_tokens=200,
        stop=["Note"], 
        verbose=False 
    )
    
    return local_llm


vector_store = retriever_function()

local_llm = load_llm()


def similarity_search_with_score(question, k=3):

    docs_with_scores = vector_store.similarity_search_with_score(question, k=k)

    docs = []

    for doc, score in docs_with_scores:

        # CHANGE 3: Convert distance → similarity
        similarity = 1 - score

        doc.metadata["similarity_score"] = similarity

        docs.append(doc)
        
        docs = sorted(
            docs,
            key=lambda d: d.metadata.get("similarity_score", 0),
            reverse=True
        )
        
    return docs


def calculate_confidence(docs):

    scores = [
        doc.metadata.get("similarity_score", 0)
        for doc in docs
    ]

    confidence = (
        0.6 * scores[0] +
        0.25 * scores[1] +
        0.15 * scores[2]
    )

    return round(confidence * 100, 2)


def format_docs(docs):

    if not docs:
        return "No relevant context found."

    return "\n\n".join(doc.page_content for doc in docs)


def extract_sources(docs):

    sources = []

    for i, doc in enumerate(docs, 1):

        source = doc.metadata.get("source",)
        page = doc.metadata.get("page",) + 1
        
        file_name = os.path.basename(source)

        sources.append(f"[{i}] {file_name} (Page {page})")

    return "\n".join(sources)


def chat_pipeline():

    prompt = ChatPromptTemplate.from_template(
        """You are a QA Medical assistant. Use the following pieces of context to answer the question. If you don't know the answer, just say that "I don't know", don't try to make up an answer. Provide a summarized and well-formed answer in 2-4 sentences maximum, do not stop mid-sentence. Finish the response completely. 

        Context:
        {context}

        Question:
        {question}

        Answer:""")

    def process(inputs):

        question = inputs["question"]
        question_id = inputs["question_id"]

        cache_id = search_cache(question)

        if not cache_id:

            docs = similarity_search_with_score(question)

            context = format_docs(docs)
            sources = extract_sources(docs)
            confidence = calculate_confidence(docs)

            formatted_prompt = prompt.format(
                context=context,
                question=question
            )

            answer = local_llm.invoke(formatted_prompt)

            cache_id = generate_cache_id()

            save_cache_to_chat_history(cache_id, question_id)

            store_in_chroma(question, cache_id)

            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "cache_id": cache_id,
                "accepted" : None,
                "edited_answer" : None
            }

        else:

            cached_answer = get_from_chat_history(cache_id)

            if cached_answer:

                return {
                    "answer": cached_answer["answer"],
                    "sources": cached_answer["sources"],
                    "confidence": cached_answer["confidence"],
                    "cache_id": cached_answer["cache_id"],
                    "accepted" : cached_answer["accepted"],
                    "edited_answer" : cached_answer["edited_answer"],
                }               
    return RunnableLambda(process)


