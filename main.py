from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import openai
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models import Conversation, User, SessionLocal, engine
from pydantic import BaseModel
from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from transformers import pipeline
from sentence_transformers import SentenceTransformer

load_dotenv()

app = FastAPI()
security = HTTPBearer()

openai.api_key = os.getenv('OPENAI_API_KEY')

class ChatRequest(BaseModel):
    user_message: str
    image: UploadFile = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

search = GoogleSearchAPIWrapper()
tools = [
    Tool(
        name="Google Search",
        func=search.run,
        description="Useful for finding information on the internet."
    )
]

prompt_template = """You are a helpful AI assistant named Claude. Your goal is to help the user with a wide range of tasks and provide engaging conversation.
You have access to tools for searching the internet and analyzing images.

User: {input}
Assistant: """

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

llm = OpenAI(temperature=0.7, max_tokens=1024, model_name="gpt-4")
conversation = ConversationChain(llm=llm, prompt=PromptTemplate(input_variables=["input"], template=prompt_template), memory=memory)
agent = initialize_agent(tools, llm, agent="conversational-react-description", verbose=True, memory=memory)

text_generator = pipeline("text-generation", model="EleutherAI/gpt-neox-20b", device=0)
image_captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-large")
sentence_embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Initialize the vector database
documents = ["Here are some example documents to be used in the vector database."]
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)
embeddings = OpenAIEmbeddings()
vector_db = FAISS.from_documents(texts, embeddings)

@app.post("/chat")
async def chat(request: ChatRequest, token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    if token.credentials != os.getenv('SECRET_TOKEN'):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        user_message = request.user_message

        if request.image:
            # Process the image and generate a caption
            image = await request.image.read()
            image_caption = image_captioner(image)[0]["caption"]
            user_message += f" [Image Caption: {image_caption}]"

        # Retrieve relevant documents from the vector database
        query_embedding = sentence_embedder.encode(user_message)
        relevant_docs = vector_db.similarity_search(query_embedding, k=3)

        # Provide the relevant documents to the agent
        agent.memory.chat_memory.add_user_message(user_message)
        for doc in relevant_docs:
            agent.memory.chat_memory.add_ai_message(doc.page_content)

        # Generate the assistant's response
        assistant_response = agent.run(user_message)

        # Generate additional text if needed
        if len(assistant_response) < 50:
            generated_text = text_generator(assistant_response, max_length=100, num_return_sequences=1)[0]["generated_text"]
            assistant_response += generated_text

        # Save the conversation to the database
        new_conversation = Conversation(user_message=user_message, assistant_response=assistant_response)
        db.add(new_conversation)
        db.commit()

        return {"assistant_response": assistant_response}

    except openai.error.OpenAIError as e:
        raise HTTPException(status_code=500, detail="OpenAI API error: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))
