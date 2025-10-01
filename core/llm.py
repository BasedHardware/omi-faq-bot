import os
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

class LLMService:
    def __init__(self):
        
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        self.client = None
        self.model_name = None
        self.provider = None

        
        if self.gemini_key:
            print("INFO: Initializing with Gemini client.")
            self.provider = "gemini"
            self.model_name = "gemini-2.5-flash" # Default Gemini Model
            
            
            self.client = genai.Client(api_key=self.gemini_key)
            
        elif self.openai_key:
            print("INFO: Initializing with OpenAI client.")
            self.provider = "openai"
            self.model_name = "gpt-4o-mini" # Default OpenAI Model (or gpt-4o)
            
            # OpenAI client initialization
            self.client = OpenAI(api_key=self.openai_key)
            
        else:
            raise ValueError(
                "No valid API key found. Please set GEMINI_API_KEY or OPENAI_API_KEY in your .env file."
            )

    def generate_answer(self, question, context):
        """
        Generates an answer using the initialized LLM provider (Gemini or OpenAI).
        """
        
        # NOTE: The system prompt (role, guidelines) is crucial for RAG performance
        system_instruction = f"""You are a helpful assistant for the Omi community Discord server.
Your role is to provide accurate, friendly, and concise answers based on the FAQ knowledge base.

    Guidelines:
        - Use the provided context to answer questions accurately
        - If the context contains the answer, provide it clearly
        - If the context doesn't fully answer the question, mention what information is available
        - Keep answers concise but complete
        - Format answers for Discord (you can use **bold**, *italic*, etc.)
        """

        user_prompt = f"""Question: {question}

        Context:
        {context}
        """

        try:
            """
            OPENAI
            """
            if self.provider == "openai":
                messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                )
                return response.choices[0].message.content
            

                """
                GEMINI
                """
            elif self.provider == "gemini":
                full_contents = f"{system_instruction}\n\n{user_prompt}"
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_contents,
                )
                return response.text
            
            else:
                return "Error: LLM provider not initialized."


        except Exception as e:
            pass
            #return f"An error occurred with {self.provider} while generating the answer: {e}"