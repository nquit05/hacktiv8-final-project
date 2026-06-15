import os,streamlit as st
from groq import Groq
from retriever import get_retriever
from dotenv import load_dotenv

load_dotenv()   

st.set_page_config(page_title="Chat — Michael Araona", page_icon="💬")

SYSTEM_PROMPT = """Kamu adalah asisten AI portofolio Michael Araona.
Jawab HANYA berdasarkan konteks yang diberikan.
Jika pertanyaan di luar konteks portofolio (skill, proyek, pengalaman, kontak),
balas: "Maaf, saya hanya bisa menjawab pertanyaan seputar portofolio Michael."
Jangan mengarang informasi yang tidak ada di konteks.
Jawab singkat, ramah, profesional. Gunakan bahasa yang sama dengan pertanyaan."""

@st.cache_resource
def load_dependencies():
    groq     = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    retrieve = get_retriever(
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        qdrant_url=os.environ.get("QDRANT_URL"),
        qdrant_api_key=os.environ.get("QDRANT_API_KEY")
    )
    return groq, retrieve

groq, retrieve = load_dependencies()

st.title("💬 Tanya tentang Michael")
st.caption("AI assistant portofolio Michael Araona.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if prompt := st.chat_input("Tanya seputar skill, proyek, atau pengalaman Michael..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        context = retrieve(prompt)

        if not context:
            reply = "Maaf, saya hanya bisa menjawab pertanyaan seputar portofolio Michael."
            st.write(reply)
        else:
            system = f"{SYSTEM_PROMPT}\n\nKonteks:\n{context}"
            resp = groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system},
                    *st.session_state.messages
                ],
                max_tokens=600,
                stream=True
            )
            reply = ""
            placeholder = st.empty()
            for chunk in resp:
                delta = chunk.choices[0].delta.content or ""
                reply += delta
                placeholder.write(reply + "▌")
            placeholder.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})