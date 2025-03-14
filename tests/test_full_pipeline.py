# tests/new_test_full_pipeline.py
import os
import sys
import time
import logging
import argparse
import openai
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.backend.workflow_orchestrator import WorkflowOrchestrator

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('electroninja')

def print_separator(title=None):
    """Print a formatted separator line with an optional title."""
    width = 80
    if title:
        print("\n" + "=" * 20 + f" {title} " + "=" * (width - len(title) - 22) + "\n")
    else:
        print("\n" + "=" * width + "\n")

def test_full_pipeline(prompt, prompt_id=1, max_iterations=3):
    """
    Test the full pipeline workflow using the WorkflowOrchestrator
    
    Args:
        prompt (str): User prompt to test
        prompt_id (int): ID for folder structure
        max_iterations (int): Maximum number of iterations to perform
    
    Returns:
        dict: Complete result with all workflow data
    """
    print("\n\n")
    print("=" * 80)
    print(f"TESTING FULL PIPELINE WITH WORKFLOW ORCHESTRATOR")
    print(f"Prompt: '{prompt}'")
    print(f"Prompt ID: {prompt_id}")
    print(f"Maximum iterations: {max_iterations}")
    print("=" * 80)
    print("\n")
    
    start_time = time.time()
    
    # Initialize components
    config = Config()
    config.MAX_ITERATIONS = max_iterations  # Override the max iterations setting
    
    llm_provider = OpenAIProvider(config)
    
    # Get all prompt templates for reference
    from electroninja.llm.prompts.circuit_prompts import (
        GENERAL_INSTRUCTION, 
        SAFETY_FOR_AGENT,
        CIRCUIT_RELEVANCE_EVALUATION_PROMPT,
        RAG_ASC_GENERATION_PROMPT,
        REFINEMENT_PROMPT_TEMPLATE,
        VISION_IMAGE_ANALYSIS_PROMPT
    )
    from electroninja.llm.prompts.chat_prompts import (
        CIRCUIT_CHAT_PROMPT,
        NON_CIRCUIT_CHAT_PROMPT,
        VISION_FEEDBACK_PROMPT
    )
    
    # Intercept the OpenAI API call to capture all exact prompts and responses
    original_create = openai.ChatCompletion.create
    
    def create_wrapper(**kwargs):
        # Determine which model and type of call this is
        model = kwargs.get("model", "unknown")
        
        # Try to determine what type of prompt this is
        prompt_type = "Unknown"
        if len(kwargs["messages"]) > 0:
            content = kwargs["messages"][0]["content"] if kwargs["messages"][0]["content"] else ""
            if CIRCUIT_RELEVANCE_EVALUATION_PROMPT.format(prompt="").split()[0] in content:
                prompt_type = "Circuit Evaluation"
            elif CIRCUIT_CHAT_PROMPT.format(prompt="").split()[0] in content:
                prompt_type = "Circuit Chat Response"
            elif NON_CIRCUIT_CHAT_PROMPT.split()[0] in content:
                prompt_type = "Non-Circuit Chat Response"
            elif SAFETY_FOR_AGENT.split()[0] in content:
                prompt_type = "ASC Generation"
            elif REFINEMENT_PROMPT_TEMPLATE.split()[0] in content:
                prompt_type = "ASC Refinement"
            elif "vision_feedback" in content:
                prompt_type = "Vision Feedback Response"
        
        # Print the exact prompt going to the model
        print(f"\n=== EXACT PROMPT SENT TO {model} ({prompt_type}) ===")
        for message in kwargs["messages"]:
            print(f"Role: {message['role']}")
            
            # For vision content, just note that there's an image rather than dumping binary data
            if isinstance(message['content'], list):
                print("Content: [Contains image data and the following text]")
                for item in message['content']:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        print(f"Text content: {item['text']}")
            else:
                # Truncate very long prompts for readability
                if message['content'] and len(message['content']) > 2000:
                    print(f"Content (truncated): {message['content'][:2000]}...[truncated]")
                else:
                    print(f"Content: {message['content']}")
        print("===========================\n")
        
        # Call the original API
        response = original_create(**kwargs)
        
        # Print the exact raw response from the model
        print(f"\n=== EXACT RAW RESPONSE FROM {model} ({prompt_type}) ===")
        raw_response = response.choices[0].message.content.strip()
        
        # Truncate very long responses for readability
        if len(raw_response) > 2000:
            print(f"{raw_response[:2000]}...[truncated]")
        else:
            print(raw_response)
        print("===========================\n")
        
        return response
    
    # Replace the API method temporarily
    openai.ChatCompletion.create = create_wrapper
    
    try:
        # Create workflow orchestrator
        orchestrator = WorkflowOrchestrator(llm_provider, config)
        
        # Process the request
        print_separator("STARTING FULL PIPELINE WORKFLOW")
        result = orchestrator.process_request(prompt, prompt_id)
        
        # Print summary
        print_separator("WORKFLOW SUMMARY")
        print(f"Is circuit-related: {result['is_circuit_related']}")
        print(f"Chat response: {result['chat_response']}")
        print(f"Number of iterations: {len(result['iterations'])}")
        print(f"Final status: {result['final_status']}")
        print(f"Success: {result['success']}")
        print(f"Processing time: {result['processing_time']:.2f} seconds")
        
        # Print iteration summary
        if result["iterations"]:
            print("\nIteration Summary:")
            for i, iteration in enumerate(result["iterations"]):
                verified = "✓ VERIFIED" if iteration.get("vision_feedback") == "Y" else "✗ NOT VERIFIED"
                print(f"Iteration {i}: {verified}")
                
                # Print image and ASC paths for reference
                if "image_path" in iteration:
                    print(f"  Image: {iteration['image_path']}")
                if "asc_path" in iteration:
                    print(f"  ASC: {iteration['asc_path']}")
        
        return result
        
    except Exception as e:
        print(f"Error in full pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        # Restore original method
        openai.ChatCompletion.create = original_create
        
        # Print execution time
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nTotal execution time: {elapsed_time:.2f} seconds")

def main():
    """Main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(description='Test the full ElectroNinja pipeline')
    parser.add_argument('--prompt', '-p', type=str, default="Create a low pass filter", help='Prompt to test')
    parser.add_argument('--id', type=int, default=1, help='Prompt ID for folder structure')
    parser.add_argument('--iterations', '-i', type=int, default=2, help='Maximum number of iterations')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger('electroninja').setLevel(logging.DEBUG)
    
    # Run the test
    test_full_pipeline(args.prompt, prompt_id=args.id, max_iterations=args.iterations)

if __name__ == "__main__":
    main()