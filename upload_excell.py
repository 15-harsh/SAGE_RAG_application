from langchain_community.document_loaders import UnstructuredExcelLoader
import pandas as pd
from chat_history import update_history, update_final_answer

def extract_text_from_excell(filepath):
    loader = UnstructuredExcelLoader(filepath, mode="elements")
    docs = loader.load()
    questions = []

    for doc in docs:
        if doc.page_content.lower() == 'question' or doc.page_content.lower() == 'questions':
            pass
        else:
            questions.append(doc.page_content)
    
    return questions


def save_answers_to_excel(history, file_name="answers.xlsx"):

    final_data = []

    for result in history:

        final_answer = (
            result["edited_answer"]
            if result["edited_answer"]
            else result["answer"]
        )

        final_data.append({
            "Question": result["question"],
            "Answer": final_answer,
            "Sources": result["sources"],
            "Confidence": result["confidence"]
        })

    df = pd.DataFrame(final_data)
    df.to_excel(file_name, index=False)




def excell_answer(questions, session_id, email, rag_chain):

    all_results = []

    for question in questions:


        question_id = update_history(
            email=email,
            session_id=session_id,
            question=question,
            answer=None,
            sources=None,
            confidence=None,
            cache_id = None,
            accepted = None,
            edited_answer = None
        )


        answer = rag_chain.invoke({
            "question": question,
            "question_id": question_id
        })



        update_final_answer(
            question_id,
            answer["answer"],
            answer["sources"],
            answer["confidence"],
            answer["cache_id"],
            answer["accepted"],
            answer["edited_answer"]
        )


        all_results.append({
            "question": question,
            "answer": answer["answer"],
            "sources": answer["sources"],
            "confidence": answer["confidence"]
        })

    return all_results


        

