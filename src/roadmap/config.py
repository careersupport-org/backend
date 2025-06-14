from langchain_openai import ChatOpenAI
from langchain.prompts import load_prompt
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema.runnable import RunnablePassthrough
from .prompt_models import RoadMap, LearningResourcePromptModel
import os

model_name = os.environ["ROADMAP_CREATE_MODEL_NAME"]
api_base = os.environ["OPENAI_API_BASE"]
api_key = os.environ["OPENAI_API_KEY"]

class LLMConfig:
    
    roadmap_create_llm = None
    recommend_resource_llm = None
    step_guide_llm = None
    roadmap_assistant_llm = None
    subroadmap_create_llm = None
    @classmethod
    def get_roadmap_create_llm(cls):
        if cls.roadmap_create_llm is not None:
            return cls.roadmap_create_llm

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
    
    @classmethod
    def get_recommend_resource_llm(cls):
        if cls.recommend_resource_llm is not None:
            return cls.recommend_resource_llm
        
        llm = ChatOpenAI(
            model = model_name,
            temperature=0.7,
            base_url=api_base,
            api_key=api_key,
            max_completion_tokens=2048
        )

        prompt = load_prompt("prompts/recommend_learning_resource_prompt.json")
        parser = JsonOutputParser(pydantic_object=LearningResourcePromptModel)

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

        cls.recommend_resource_llm = chain
        return cls.recommend_resource_llm

    @classmethod
    def get_step_guide_llm(cls):
        if cls.step_guide_llm is not None:
            return cls.step_guide_llm

        llm = ChatOpenAI(
            model = model_name,
            temperature=0.7,
            base_url=api_base,
            api_key=api_key,
            max_completion_tokens=2048
        )

        prompt = load_prompt("prompts/guide_step_prompt.json")
        chain = prompt | llm

        cls.step_guide_llm = chain
        return cls.step_guide_llm

    @classmethod
    def get_roadmap_assistant_llm(cls):
        if cls.roadmap_assistant_llm is not None:
            return cls.roadmap_assistant_llm

        llm = ChatOpenAI(
            model = model_name,
            temperature=0.7,
            base_url=api_base,
            api_key=api_key,
            max_completion_tokens=2048
        )

        prompt = load_prompt("prompts/roadmap_assistant_prompt.json")
        chain = prompt | llm

        cls.roadmap_assistant_llm = chain
        return cls.roadmap_assistant_llm


    @classmethod
    def get_subroadmap_create_llm(cls):
        if cls.subroadmap_create_llm is not None:
            return cls.subroadmap_create_llm
        
        llm = ChatOpenAI(
            model = model_name,
            temperature=0.7,
            base_url=api_base,
            api_key=api_key,
            max_completion_tokens=4096
        )
        
        prompt = load_prompt("prompts/subroadmap_create_prompt.json")

        subroadmap_parser = JsonOutputParser(pydantic_object=RoadMap)

        def get_format_instructions(_):
            return subroadmap_parser.get_format_instructions()
        
        chain = (
            RunnablePassthrough.assign(
            format_instructions=get_format_instructions
            ) 
            | prompt 
            | llm 
            | subroadmap_parser
        )

        cls.subroadmap_create_llm = chain
        return cls.subroadmap_create_llm