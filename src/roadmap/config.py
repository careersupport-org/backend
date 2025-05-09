from langchain_openai import ChatOpenAI
from langchain.prompts import load_prompt
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema.runnable import RunnablePassthrough
from .prompt_models import RoadMap, RoadMapStep
import os

model_name = os.environ["ROADMAP_CREATE_MODEL_NAME"]
api_base = os.environ["OPENAI_API_BASE"]
api_key = os.environ["OPENAI_API_KEY"]
class LLMConfig:
    
    roadmap_create_llm = None

    @classmethod
    def get_roadmap_create_llm(cls):
        if cls.roadmap_create_llm is not None:
            return cls.roadmap_create_llm
        print(f"api_base: {api_base}")
        print(f"api_key: {api_key}")
        llm = ChatOpenAI(
            model = model_name,
            temperature=0.7,
            base_url=api_base,
            api_key=api_key,
            max_completion_tokens=2048
        )

        prompt = load_prompt("prompts/create_roadmap_prompt.json")
        parser = JsonOutputParser(pydantic_object=RoadMap)
        
        def get_format_instructions(_):
            return parser.get_format_instructions()

        chain = (
            RunnablePassthrough.assign(
            format_instructions=get_format_instructions
            ) 
            | prompt 
            | llm 
            | parser
        )

        cls.roadmap_create_llm = chain
        return cls.roadmap_create_llm