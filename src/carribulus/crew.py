from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, TavilySearchTool
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

# OpenRouter platform models (All models included paid and free)
orouter = LLM(
    model="openrouter/nvidia/nemotron-nano-9b-v2:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Hugging Face platform models (Open Source)
hf = LLM(
    model="huggingface/Qwen/Qwen3-VL-8B-Instruct:novita"
)

# Google AI Studio platform models (Gemini)
gm = LLM(
    model="gemini/gemini-flash-latest",
    temperature=0.7
)

@CrewBase
class Carribulus():
    """Travel Agent Crew"""

    agents: List[Agent]
    tasks: List[Task]

    # Tools - Using CrewAI's built-in tools
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    serper_tool = SerperDevTool()        
    tavily_tool = TavilySearchTool()  

    # Manager Agent (Supervisor)
    # NOTE: No need @agent decorator，becuz manager_agent can't be in the list of agents
    def travel_manager(self) -> Agent:
        return Agent(
            role="Travel Concierge Manager",
            goal="Understand user needs and coordinate experts to provide the best travel advice.",
            backstory="""
                You are the head concierge at a 5-star travel agency.
                You are warm, professional, and always helpful.
                
                Your responsibilities:
                1. Understand what the user really wants
                2. If the request is vague, ask clarifying questions FIRST
                3. Delegate tasks to the right experts
                4. Ensure the final response is comprehensive
                
                IMPORTANT RULES:
                - Simple greetings (Hello, Hi) → respond directly, NO experts
                - Vague requests → ask for details, NO experts yet
                - Specific questions → use ONLY the relevant expert
                - Full trip planning → coordinate ALL experts in order:
                  1. Local Guide first (attractions, food)
                  2. Transport Expert second (flights, hotels)
                  3. Itinerary Architect last (compile everything)
            """,
            llm=gm,  # Should be a strong and clever model as supervisor
            allow_delegation=True,
            verbose=True
        )

    # Sub-Agents
    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    @agent
    def transport_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['transport_expert'],
            tools=[self.serper_tool],
            llm=gm,
            verbose=True
        )

    @agent
    def local_guide(self) -> Agent:
        return Agent(
            config=self.agents_config['local_guide'],
            tools=[self.serper_tool, self.tavily_tool],
            llm=gm,
            verbose=True
        )

    @agent
    def itinerary_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['itinerary_architect'],
            tools=[],  # No tools needed - just compiles info from other agents
            llm=gm,
            verbose=True
        )

    # Task
    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def handle_travel_request(self) -> Task:
        return Task(
            config=self.tasks_config['handle_travel_request'],
            output_file="report.md"
            # No agent specified - Manager will delegate based on request
        )

    # Crew Assembly
    # To learn how to add knowledge sources to your crew, check out the documentation:
    # https://docs.crewai.com/concepts/knowledge#what-is-knowledge
    @crew
    def crew(self) -> Crew:
        """Creates the Travel Agent crew with hierarchical process"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.travel_manager(),
            verbose=True,
            output_log_file=False,
        )
