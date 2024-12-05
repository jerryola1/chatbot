import modal
from typing import Optional
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

# Create Modal app
app = modal.App("example-llm")

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
    )
)

# Model configuration
MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"
MODEL_DIR = "/model"

# Create volume for caching
volume = modal.Volume.from_name("model-cache", create_if_missing=True)

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str
    error: Optional[str] = None

@app.cls(
    gpu="A10G",
    image=image,
    volumes={MODEL_DIR: volume},
    secrets=[modal.Secret.from_name("huggingface-secret")]
)
class Model:
    @modal.enter()
    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        cache_path = f"{MODEL_DIR}/cache"
        if os.path.exists(f"{cache_path}/model"):
            print("Loading from cache...")
            self.tokenizer = AutoTokenizer.from_pretrained(f"{cache_path}/tokenizer")
            self.model = AutoModelForCausalLM.from_pretrained(
                f"{cache_path}/model",
                torch_dtype=torch.float16,
                device_map="auto"
            )
        else:
            print("Downloading model...")
            os.makedirs(cache_path, exist_ok=True)

            self.tokenizer = AutoTokenizer.from_pretrained(
                MODEL_ID,
                use_auth_token=os.environ["HUGGING_FACE_TOKEN"]
            )
            self.tokenizer.save_pretrained(f"{cache_path}/tokenizer")

            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                use_auth_token=os.environ["HUGGING_FACE_TOKEN"],
                torch_dtype=torch.float16,
                device_map="auto"
            )
            self.model.save_pretrained(f"{cache_path}/model")

        # Set pad_token_id and eos_token_id
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        if self.tokenizer.eos_token_id is None:
            self.tokenizer.eos_token_id = self.tokenizer.convert_tokens_to_ids("</s>")

        print("Model ready")

    def generate(self, prompt: str) -> str:
        # Use the provided system prompt
        system_prompt = (
        "You are a helpful assistant trained on University of Hull data. "
            "Provide concise and clear answers to the user's questions without mentioning any policies or guidelines directly. "
            "If the information is not available, admit that you do not have that information. "
            "Do not include any unnecessary preamble or apologies; go straight to the answer."
        )

        # Format the prompt according to Llama 2's expected format
        formatted_prompt = f"""<s>[INST] <<SYS>>
{system_prompt}
<</SYS>>

{prompt} [/INST]"""

        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract the assistant's response
        # The assistant's response should be after the [/INST] token
        if "[/INST]" in output_text:
            assistant_response = output_text.split("[/INST]", 1)[1].strip()
        else:
            assistant_response = output_text.strip()

        # Remove any leftover special tokens
        assistant_response = assistant_response.replace("</s>", "").strip()

        return assistant_response

    @modal.web_endpoint(method="POST")
    async def chat(self, request: ChatRequest) -> ChatResponse:
        try:
            # Add CORS headers
            headers = {
                "Access-Control-Allow-Origin": "*",  # Replace * with your frontend domain in production
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
            
            response = self.generate(request.prompt)
            return ChatResponse(response=response), headers
        except Exception as e:
            return ChatResponse(response="", error=str(e)), headers

@app.local_entrypoint()
def main():
    model = Model()
    response = model.generate("What are the library opening hours?")
    print("Response:", response)
