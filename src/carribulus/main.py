import os
import sys
import warnings
import time

from datetime import datetime
from dotenv import load_dotenv
from carribulus.crew import Carribulus

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

load_dotenv()

# MLflow Tracing
# =============================================================================
# I've set ENABLE_TRACING=true in the .env, so auto tracing is enabled by default.
# U can set ENABLE_TRACING=false if don't want to use MLflow tracing.
#
# Command to open monitoring interface (copy & run in terminal):
#   mlflow ui --backend-store-uri sqlite:///mlflow.db --workers 1
#   Then open this: http://127.0.0.1:5000

if os.getenv("ENABLE_TRACING", "true").lower() == "true":
    import mlflow
    
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    
    mlflow.crewai.autolog()
    mlflow.set_experiment("Carribulus-TravelAgent")
    print("📊 MLflow Tracing: ENABLED [sqlite:///mlflow.db]")
else:
    print("📊 MLflow Tracing: DISABLED")


def print_usage_metrics(crew_output):
    """Print token usage and execution metrics"""
    print("\n" + "=" * 100)
    print("🪶  Usage Metrics:")
    print("=" * 100)
    
    # Token usage from CrewOutput
    # NOTE: token_usage is a UsageMetrics object, not a dict
    if hasattr(crew_output, 'token_usage') and crew_output.token_usage:
        usage = crew_output.token_usage
        
        # Access attributes directly (UsageMetrics is a Pydantic model)
        total = getattr(usage, 'total_tokens', None)
        prompt = getattr(usage, 'prompt_tokens', None)
        completion = getattr(usage, 'completion_tokens', None)
        
        print(f"  🎇 Total Tokens: {total if total else 'N/A'}")
        print(f"  🌿 Prompt Tokens: {prompt if prompt else 'N/A'}")
        print(f"  📝 Completion Tokens: {completion if completion else 'N/A'}")
        
    else:
        print("  ⚠️ Token usage not available")

def run():
    """
    Run the Travel Agent crew interactively.
    """
    print("=" * 60)
    print("🌏 Welcome to Travel Assistant!")
    print("=" * 60)
    print("\nI can help you with:")
    print("  • Flight, train, bus bookings")
    print("  • Hotel recommendations")
    print("  • Local attractions & food")
    print("  • Complete trip planning")
    print("\nType 'exit' or 'quit' to leave.\n")

    while True:
        try:
            user_query = input("You: ").strip()
            
            if not user_query:
                continue
            
            if user_query.lower() in ['exit', 'quit']:
                print("\n✈️  Safe travels! See you next time!")
                break

            inputs = {
                'user_query': user_query,
                'current_date': datetime.now().strftime("%Y-%m-%d")
            }

            print("\n🔍 Processing your request...\n")
            
            # Track execution time
            start_time = time.time()
            
            crew_instance = Carribulus().crew()
            result = crew_instance.kickoff(inputs=inputs)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print("\n" + "=" * 100)
            print("🎯 Response:")
            print("=" * 100 + "\n")
            print(result)
            
            # Print usage metrics
            print_usage_metrics(result)
            print(f"  ⏱️  Execution Time: {execution_time:.2f}s")
            print("=" * 100 + "\n")

        except KeyboardInterrupt:
            print("\n\n✈️ Safe travels! See you next time!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            print("Please try again with a different question.\n")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        Carribulus().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Carribulus().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        Carribulus().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = Carribulus().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
