from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List
# import os

# Import LLMs from separate module
from carribulus.llms import gm, hf, orouter

# Import Tools
from carribulus.tools import (
    serper_search,   # General search
    serper_places,   # Places search (attractions, restaurants)
    serper_news,     # News search (events, safety)
    tavily_search,   # Deep search (comprehensive info)
)

# Set custom storage location
# os.environ["CREWAI_STORAGE_DIR"] = "./storage"

@CrewBase
class Carribulus():
    """Travel Agent Crew"""

    agents: List[Agent]
    tasks: List[Task]

    # Manager Agent (Supervisor + Final Summarizer)
    # =========================================================================
    # NOTE: No @agent decorator because manager_agent can't be in the agents list
    # https://docs.crewai.com/en/learn/custom-manager-agent
    def travel_manager(self) -> Agent:
        return Agent(
            role="Travel Manager",
            goal="Understand user needs, coordinate experts, and compile the final comprehensive travel plan.",
            backstory="""
                You are warm, professional, and always helpful travel assistant.
                
                Your responsibilities:
                1. Understand what the user really wants
                2. If the request is vague, ask clarifying questions FIRST
                3. Delegate specific research to the right experts
                4. COMPILE and ORGANIZE all information into a final travel plan
                
                IMPORTANT DELEGATION RULES:
                - Simple greetings (Hello, Hi) → respond directly, NO experts
                - Vague requests → ask for details, NO experts yet
                - Flights/Hotels/Transport → Transport Expert
                - Attractions/Food/Culture → Local Guide
                - Events/Safety/Weather → News Analyst
                - Image translation → Vision Translator (only when user provides image URL)
                - Full trip planning → use relevant experts, then YOU create the final itinerary:
                  * Day-by-day schedule
                  * Budget breakdown
                  * Safety notes
                  * Practical tips
            """,
            llm=gm,  # Should be a strong and clever model as supervisor
            allow_delegation=True,
            verbose=True,
            max_retry_limit=3,
            max_iter=25,
            reasoning=False
        )

    # Sub-Agents (defined in agents.yaml)
    # =========================================================================
    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    @agent
    def transport_expert(self) -> Agent:
        """Handles flights, hotels, transportation"""
        return Agent(
            config=self.agents_config['transport_expert'],
            tools=[serper_search],
            llm=orouter,
            verbose=True
        )

    @agent
    def local_guide(self) -> Agent:
        """Handles attractions, food, cultural experiences"""
        return Agent(
            config=self.agents_config['local_guide'],
            tools=[serper_places, tavily_search],
            llm=gm,
            verbose=True
        )

    @agent
    def news_analyst(self) -> Agent:
        """Handles events, weather, safety information"""
        return Agent(
            config=self.agents_config['news_analyst'],
            tools=[serper_news],
            llm=gm,
            verbose=True
        )

    @agent
    def vision_translator(self) -> Agent:
        """Handles image analysis and translation"""
        return Agent(
            config=self.agents_config['vision_translator'],
            tools=[],  # No tools needed - uses vision capability directly
            llm=hf,    
            multimodal=True,  # Enable image understanding
            verbose=True
        )

    # Task (defined in tasks.yaml)
    # =========================================================================
    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def handle_travel_request(self) -> Task:
        return Task(
            config=self.tasks_config['handle_travel_request'],
            output_file="report.md",
            human_input=False
            # No agent specified - Manager will delegate based on request
        )

    # Crew Assembly
    # =========================================================================
    # To learn how to add knowledge sources to your crew, check out the documentation:
    # https://docs.crewai.com/concepts/knowledge#what-is-knowledge
    # https://docs.crewai.com/en/concepts/crews
    @crew
    def crew(self) -> Crew:
        """Creates the Travel Agent crew with hierarchical process"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.travel_manager(),
            verbose=True,
            output_log_file=False
        )
