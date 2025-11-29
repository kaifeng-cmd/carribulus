from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List

# Import LLMs and Tools from separate modules
from carribulus.llms import gm
from carribulus.tools import serper_tool, tavily_tool


@CrewBase
class Carribulus():
    """Travel Agent Crew"""

    agents: List[Agent]
    tasks: List[Task]

    # Manager Agent (Supervisor + Final Summarizer)
    # NOTE: No @agent decorator because manager_agent can't be in the agents list
    # https://docs.crewai.com/concepts/crews
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
                
                IMPORTANT RULES:
                - Simple greetings (Hello, Hi) → respond directly, NO experts
                - Vague requests → ask for details, NO experts yet
                - Specific questions → use ONLY the relevant expert
                - Full trip planning → use experts, then YOU create the final itinerary:
                  * Day-by-day schedule
                  * Budget breakdown
                  * Practical tips
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
            tools=[serper_tool],
            llm=gm,
            verbose=True
        )

    @agent
    def local_guide(self) -> Agent:
        return Agent(
            config=self.agents_config['local_guide'],
            tools=[tavily_tool],
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
            output_file="report.md",
            human_input=True
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
            output_log_file=False
        )
