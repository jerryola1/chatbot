import modal
from typing import Optional, List, Dict
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import json
from fastapi.responses import JSONResponse

# Create Modal app
app = modal.App("example-llm")

# Create mount for RAG files
RAG_PATH = "/home/jerryola1/chatbot/modal-api/rag"
rag_files = modal.Mount.from_local_dir(RAG_PATH, remote_path="/root/rag")

# Create base image with all dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "numpy<2.0.0",
        "torch==2.2.1",
        "transformers[torch]>=4.35.2",
        "accelerate>=0.25.0",
        "fastapi[standard]>=0.104.1",
        "pydantic>=2.0.0",
        "faiss-cpu",
        "sentence-transformers",
    )
)

# Model configuration
MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"
MODEL_DIR = "/model"

# Create volume for model caching
model_volume = modal.Volume.from_name("model-cache", create_if_missing=True)

class Message(BaseModel):
    content: str
    is_user: bool
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[int] = None
    history: Optional[List[Message]] = None

class ChatResponse(BaseModel):
    response: str
    error: Optional[str] = None
    source_documents: List[str] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "Example response",
                    "error": None,
                    "source_documents": ["https://example.com/doc1"]
                }
            ]
        }
    }

def format_chat_history(history: List[Message]) -> str:
    """Format chat history into a string, limiting to recent messages that fit in context window"""
    formatted_history = []
    for msg in history[-5:]:  # Limit to last 5 messages to stay within context window
        role = "Previous User Question" if msg.is_user else "Previous Assistant Answer"
        formatted_history.append(f"{role}:\n{msg.content}\n")
    return "\n".join(formatted_history)

def is_library_hours_query(prompt: str) -> bool:
    """Check if the query is about library hours"""
    prompt_lower = prompt.lower()
    library_keywords = ['library']
    time_keywords = ['opening', 'hours', 'time', 'open', 'close', 'when']
    
    has_library = any(keyword in prompt_lower for keyword in library_keywords)
    has_time = any(keyword in prompt_lower for keyword in time_keywords)
    
    return has_library and has_time

@app.cls(
    gpu="A10G",
    image=image,
    volumes={MODEL_DIR: model_volume},
    mounts=[rag_files],
    secrets=[modal.Secret.from_name("huggingface-secret")]
)
class Model:
    def __init__(self):
        self.faiss_index = None
        self.document_lookup = None
        self.embedding_model = None

    @modal.enter()
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # Define cache paths
        cache_path = f"{MODEL_DIR}/cache"
        model_path = f"{cache_path}/model"
        tokenizer_path = f"{cache_path}/tokenizer"
        
        print("Loading model and tokenizer...")
        if os.path.exists(model_path):
            print("Loading from cache...")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                use_cache=True
            )
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        else:
            print("Downloading model...")
            os.makedirs(cache_path, exist_ok=True)
            
            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                use_auth_token=os.environ["HUGGING_FACE_TOKEN"],
                torch_dtype=torch.float16,
                device_map="auto",
                use_cache=True
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                MODEL_ID,
                use_auth_token=os.environ["HUGGING_FACE_TOKEN"]
            )
            
            # Save model and tokenizer
            self.model.save_pretrained(model_path)
            self.tokenizer.save_pretrained(tokenizer_path)

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        if self.tokenizer.eos_token_id is None:
            self.tokenizer.eos_token_id = self.tokenizer.convert_tokens_to_ids("</s>")

        print("Model ready")
        self._load_rag()

    def _load_rag(self):
        import faiss
        from sentence_transformers import SentenceTransformer
        
        print("Loading RAG components...")
        print(f"Checking contents of /root/rag:")
        print(os.listdir("/root/rag"))
        
        # Load embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load FAISS index
        faiss_path = "/root/rag/faiss_index.bin"
        print(f"Loading FAISS index from: {faiss_path}")
        print(f"File exists: {os.path.exists(faiss_path)}")
        self.faiss_index = faiss.read_index(faiss_path)
        
        # Load document lookup
        lookup_path = "/root/rag/document_lookup.json"
        print(f"Loading document lookup from: {lookup_path}")
        print(f"File exists: {os.path.exists(lookup_path)}")
        with open(lookup_path, "r") as f:
            self.document_lookup = json.load(f)
            
        print("RAG components loaded successfully")

    def retrieve_context(self, query: str, k: int = 5) -> tuple[str, List[str]]:
        # Check if query is about non-university topics
        non_uni_keywords = ['restaurant', 'weather', 'forecast', 'pizza', 'pub', 'council', 'tax', 
                          'cinema', 'movie', 'train', 'bus', 'shopping', 'store', 'shop']
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in non_uni_keywords):
            return "", []

        # Encode query
        query_vector = self.embedding_model.encode([query])[0]
        
        # Search FAISS index
        D, I = self.faiss_index.search(
            query_vector.reshape(1, -1).astype('float32'), 
            k
        )
        
        # Get relevant chunks
        relevant_chunks = []
        source_documents = []
        total_chars = 0
        max_chars = 2000
        
        # Track relevance score
        max_score = 0
        
        for score, idx in zip(D[0], I[0]):
            if str(idx) in self.document_lookup:
                max_score = max(max_score, score)
                chunk = self.document_lookup[str(idx)]
                chunk_text = chunk['text']
                
                # Include more chunks by being very lenient
                if score < 0.01:  # Very lenient threshold
                    continue
                
                if total_chars + len(chunk_text) > max_chars:
                    remaining_chars = max_chars - total_chars
                    if remaining_chars > 100:
                        chunk_text = chunk_text[:remaining_chars] + "..."
                        relevant_chunks.append(chunk_text)
                        if 'source_document' in chunk:
                            source_documents.append(chunk['source_document'])
                    break
                
                relevant_chunks.append(chunk_text)
                if 'source_document' in chunk:
                    source_documents.append(chunk['source_document'])
                total_chars += len(chunk_text)
                
                if total_chars >= max_chars:
                    break

        # Very lenient threshold
        if max_score < 0.01:
            return "", []
            
        # Format context
        return "\n\n".join(relevant_chunks), list(set(source_documents))

    def generate(self, prompt: str, history: Optional[List[Message]] = None) -> tuple[str, List[str]]:
        context, source_docs = self.retrieve_context(prompt)
        
        if not context.strip():
            return "No specific information available", []
        
        system_prompt = (
            "You are a University of Hull assistant. Your role is to:\n"
            "1. Provide accurate information from the context\n"
            "2. Give clear, direct answers without greetings or meta-language\n"
            "3. Keep responses concise and relevant\n"
            "4. Say 'No specific information available' when unsure\n"
            "5. Present lists and steps in a clear format"
        )

        chat_context = ""
        if history:
            chat_context = f"\nPrevious conversation:\n{format_chat_history(history)}\n"

        formatted_prompt = f"""<s>[INST] <<SYS>>
{system_prompt}

Context:
{context}

{chat_context if history else ""}
Question: {prompt} [/INST]"""

        outputs = self.model.generate(
            **self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device),
            max_new_tokens=150,
            min_new_tokens=10,
            temperature=0.1,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.2,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "[/INST]" in output_text:
            assistant_response = output_text.split("[/INST]", 1)[1].strip()
        else:
            assistant_response = output_text.strip()

        cleaned_response = assistant_response.replace("</s>", "").strip()
        
        if sum(c.isdigit() for c in cleaned_response) > len(cleaned_response) * 0.3:
            return "Error occurred. Please try again.", []
            
        # Return only the most relevant source document
        most_relevant_source = source_docs[0] if source_docs else []
        return cleaned_response, [most_relevant_source] if most_relevant_source else []

    @modal.web_endpoint(method="POST")
    async def chat(self, request: ChatRequest):
        try:
            # Get response and source docs from model
            response, source_docs = self.generate(request.prompt, request.history)
            
            # Create minimal response with single most relevant source
            return {
                "response": response,
                "source_documents": source_docs,
                "error": None
            }
            
        except Exception as e:
            return {
                "response": "",
                "source_documents": [],
                "error": str(e)
            }

@app.local_entrypoint()
def main():
    model = Model()
    response = model.generate("What are the library opening hours?")
    print("Response:", response)
