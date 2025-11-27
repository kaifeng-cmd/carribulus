#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from carribulus.crew import Carribulus

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the Travel Agent crew interactively.
    """
    print("=" * 60)
    print("🌏 Welcome to Carribulus Travel Agent!")
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
            
            if user_query.lower() in ['exit', 'quit', 'bye']:
                print("\n✈️ Safe travels! See you next time!")
                break

            inputs = {
                'user_query': user_query,
                'current_date': datetime.now().strftime("%Y-%m-%d")
            }

            print("\n🔍 Processing your request...\n")
            result = Carribulus().crew().kickoff(inputs=inputs)
            
            print("\n" + "=" * 60)
            print("🎯 Response:")
            print("=" * 60)
            print(result)
            print("=" * 60 + "\n")

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
