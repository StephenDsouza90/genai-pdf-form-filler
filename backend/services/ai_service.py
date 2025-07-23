import os
import logging
from dotenv import load_dotenv

from openai.lib.azure import AsyncAzureOpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:

    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_version=os.getenv("API_VERSION"),
            api_key=os.getenv("OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT")
        )

    async def generate_question(self, field_name: str, field_type: str) -> str:
        """
        Generate a user-friendly question for a form field
        """
        try:
            prompt = f"""
            You are helping a user fill out a PDF form. Generate a clear, friendly question to ask the user for the following form field:

            Field Name: {field_name}
            Field Type: {field_type}

            Make the question:
            1. Easy to understand and conversational
            2. Specific about what information is needed
            3. Include any relevant context or examples if helpful
            4. Keep it concise but informative

            Just return the question text, nothing else.
            """

            request_body = {
                "temperature": 0.7,     # Adjust temperature for creativity
                "top_p": 1,             # Use top-p 1 as default - Do not change
                "stream": False,
                "stop": None,
                "max_tokens": 4096,     # Limit to 4096 tokens - Default for gpt-4o
                "presence_penalty": 0,  # Default presence penalty
                "frequency_penalty": 0, # Default frequency penalty
                "logit_bias": {},
                "user": "STEDSOU",      # User ID for tracking
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "data_sources": [
                    "string"
                ],
                "n": 1,
                "seed": 0,
                "response_format": {
                    "type": "text"
                },
                "tools": [
                    "string"
                ],
                "tool_choice": "string",
                "functions": [
                    "string"
                ],
                "function_call": "none"
            }

            logger.info(f"Sending request to AI service for field: {field_name}")

            response = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o",
                frequency_penalty=request_body["frequency_penalty"],
                logit_bias=request_body["logit_bias"],
                max_tokens=request_body["max_tokens"],
                n=request_body["n"],
                presence_penalty=request_body["presence_penalty"],
                response_format=request_body["response_format"],
                seed=request_body["seed"],
                stop=request_body["stop"],
                stream=request_body["stream"],
                temperature=request_body["temperature"],
                top_p=request_body["top_p"],
                user=request_body["user"],
            )

            logger.info(f"Received response from AI service for field: {field_name}")
            content =  response.choices[0].message.content
            if not content:
                raise ValueError("AI response was empty")
            logger.info(f"Generated question for field {field_name}: {content}")

            return content.strip()

        except Exception as e:
            logger.error(f"Error generating question for field {field_name}: {e}")
            # Fallback to basic question if AI fails
            return f"Please provide a value for {field_name.replace('_', ' ').title()}:"
    
    def process_answer(self, answer: str, field_type: str, field_name: str) -> str:
        """
        Process and format user answers based on field type
        """
        try:
            if field_type in ["checkbox", "radiobutton"]:
                # Convert natural language to boolean/selection
                answer_lower = answer.lower().strip()
                yes_words = ["yes", "y", "true", "1", "on", "checked", "check", "selected", "select"]
                return "yes" if any(word in answer_lower for word in yes_words) else "no"
            
            elif field_type in ["text", "combobox", "listbox"]:
                # For text fields, clean up the answer
                prompt = f"""
                Clean up and format this user input for a form field named "{field_name}":
                
                User input: "{answer}"
                Field type: {field_type}
                
                Return a clean, properly formatted version suitable for a PDF form. 
                Keep it concise and remove any unnecessary words.
                Just return the cleaned text, nothing else.
                """
                
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.3
                )
                
                return response.choices[0].message.content.strip()
            
            else:
                # For other field types, return as-is
                return answer.strip()
                
        except Exception as e:
            # Fallback to basic processing if AI fails
            if field_type in ["checkbox", "radiobutton"]:
                answer_lower = answer.lower().strip()
                yes_words = ["yes", "y", "true", "1", "on", "checked", "check", "selected", "select"]
                return "yes" if any(word in answer_lower for word in yes_words) else "no"
            return answer.strip()