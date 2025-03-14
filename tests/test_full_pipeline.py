# tests/test_iterative_pipeline.py
import os
import sys
import time
import logging
import argparse
import threading
import json
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from electroninja.config.settings import Config
from electroninja.llm.providers.openai import OpenAIProvider
from electroninja.llm.vector_store import VectorStore
from electroninja.core.ltspice.interface import LTSpiceInterface
from electroninja.llm.vision_analyser import VisionAnalyzer
from electroninja.llm.prompts.circuit_prompts import (
    GENERAL_INSTRUCTION,
    SAFETY_FOR_AGENT,
    CIRCUIT_RELEVANCE_EVALUATION_PROMPT,
    RAG_ASC_GENERATION_PROMPT,
    REFINEMENT_PROMPT_TEMPLATE
)
from electroninja.llm.prompts.chat_prompts import (
    CIRCUIT_CHAT_PROMPT,
    NON_CIRCUIT_CHAT_PROMPT,
    VISION_FEEDBACK_PROMPT
)

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

def extract_clean_asc_code(asc_code):
    """
    Extract only the pure ASC code starting from 'Version 4'
    This ensures we don't include descriptions in the ASC code examples
    """
    if "Version 4" in asc_code:
        idx = asc_code.find("Version 4")
        return asc_code[idx:].strip()
    return asc_code.strip()

def validate_asc_code(asc_code):
    """
    Validate ASC code to ensure it's properly formed
    
    Args:
        asc_code (str): ASC code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check for basic structure
    if not asc_code.startswith("Version 4"):
        print("Invalid ASC code: Does not start with 'Version 4'")
        return False
        
    # Check for duplicate FLAG entries
    flag_lines = [line for line in asc_code.splitlines() if line.startswith("FLAG")]
    flag_targets = [line.split()[1:3] for line in flag_lines if len(line.split()) >= 3]
    if len(flag_targets) != len(set(tuple(target) for target in flag_targets)):
        print("Invalid ASC code: Contains duplicate FLAGS")
        return False
        
    # Check for duplicate SYMBOL entries at same coordinates
    symbol_lines = [line for line in asc_code.splitlines() if line.startswith("SYMBOL")]
    symbol_positions = []
    for line in symbol_lines:
        parts = line.split()
        if len(parts) >= 4:
            try:
                pos = (parts[-2], parts[-1])
                symbol_type = parts[1]
                key = (symbol_type, pos)
                if key in symbol_positions:
                    print(f"Invalid ASC code: Duplicate SYMBOL {symbol_type} at position {pos}")
                    return False
                symbol_positions.append(key)
            except:
                pass
                
    # Ensure there's at least one voltage source
    if not any(line.startswith("SYMBOL voltage") for line in symbol_lines):
        print("Invalid ASC code: No voltage source found")
        return False
        
    return True

def step1_evaluate_circuit_request(prompt, llm_provider):
    """
    Step 1: Evaluate if the prompt is circuit-related
    
    Args:
        prompt (str): User prompt to evaluate
        llm_provider: The LLM provider instance
        
    Returns:
        bool: True if circuit-related, False otherwise
    """
    print_separator("STEP 1: CIRCUIT RELEVANCE EVALUATION")
    print(f"Evaluating if the prompt is circuit-related: '{prompt}'")
    
    evaluation_prompt = f"{GENERAL_INSTRUCTION}\n\n{CIRCUIT_RELEVANCE_EVALUATION_PROMPT.format(prompt=prompt)}"
    
    print("\nRAW PROMPT SENT TO EVALUATION MODEL:")
    print("-" * 40)
    print(evaluation_prompt)
    print("-" * 40)
    
    # Get raw response instead of just boolean to print it
    try:
        import openai
        response = openai.ChatCompletion.create(
            model=llm_provider.evaluation_model,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )
        raw_result = response.choices[0].message.content.strip()
        is_circuit_related = raw_result.upper().startswith('Y')
        
        print("\nRAW EVALUATION RESPONSE:")
        print("-" * 40)
        print(raw_result)
        print("-" * 40)
        
        print(f"Final evaluation result: {is_circuit_related} (Circuit-related: {'Yes' if is_circuit_related else 'No'})")
        
        return is_circuit_related
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
        return False

def step2a_generate_chat_response(prompt, is_circuit_related, llm_provider):
    """
    Step 2a: Generate chat response based on whether the prompt is circuit-related
    
    Args:
        prompt (str): User prompt
        is_circuit_related (bool): Whether the prompt is related to circuits
        llm_provider: The LLM provider instance
        
    Returns:
        str: Generated chat response
    """
    print_separator("STEP 2A: CHAT RESPONSE GENERATION")
    
    if is_circuit_related:
        chat_prompt = f"{GENERAL_INSTRUCTION}\n{CIRCUIT_CHAT_PROMPT.format(prompt=prompt)}"
        print("\nUsing CIRCUIT_CHAT_PROMPT for circuit-related request")
    else:
        # For non-circuit queries, use a more direct prompt that requests a short, clear response
        chat_prompt = (
            f"{GENERAL_INSTRUCTION}\n"
            f"The user has made a request that is not related to electrical circuits: '{prompt}'.\n\n"
            f"Provide a brief, polite response explaining that this system is specifically designed "
            f"for electrical circuit design and cannot help with this particular request. "
            f"Keep your response under 3 sentences."
        )
        print("\nUsing simplified prompt for non-circuit-related request")
    
    print("\nRAW PROMPT SENT TO CHAT MODEL:")
    print("-" * 40)
    print(chat_prompt)
    print("-" * 40)
    
    try:
        import openai
        response = openai.ChatCompletion.create(
            model=llm_provider.chat_model,
            messages=[{"role": "user", "content": chat_prompt}]
        )
        
        chat_response = response.choices[0].message.content.strip()
        
        print("\nRAW CHAT RESPONSE:")
        print("-" * 40)
        print(chat_response)
        print("-" * 40)
        
        return chat_response
    except Exception as e:
        print(f"Error generating chat response: {str(e)}")
        return "Error generating response"

def step2b_generate_asc_code(prompt, llm_provider, vector_store):
    """
    Step 2b: Generate ASC code based on the prompt using RAG
    
    Args:
        prompt (str): User prompt
        llm_provider: The LLM provider instance
        vector_store: The vector store instance
        
    Returns:
        str: Generated ASC code
    """
    print_separator("STEP 2B: ASC CODE GENERATION")
    
    # Fetch examples from vector database
    print("Fetching similar examples from vector DB...")
    examples = vector_store.search(prompt)
    
    print(f"Found {len(examples)} similar examples")
    
    # Process examples for the prompt
    examples_text = ""
    for i, example in enumerate(examples, start=1):
        # Get description from metadata
        desc = example.get("metadata", {}).get("description", "No description")
        
        # Get ASC code, preferring pure_asc_code if available
        if "metadata" in example and "pure_asc_code" in example["metadata"]:
            asc_code = example["metadata"]["pure_asc_code"]
        else:
            # Fall back to asc_code field
            asc_code = example.get("asc_code", "")
        
        # Ensure we only have the clean ASC code without descriptions
        asc_code = extract_clean_asc_code(asc_code)
        
        # Format with clear separation for the prompt
        examples_text += (
            f"Example {i}:\n"
            f"Description: {desc}\n"
            f"ASC Code:\n"
            f"-----------------\n"
            f"{asc_code}\n"
            f"-----------------\n\n"
        )
    
    # Construct prompt
    system_prompt = f"{GENERAL_INSTRUCTION}\n\n{SAFETY_FOR_AGENT}"
    
    user_prompt = (
        "Below are examples of circuits similar to the user's request:\n\n"
        f"{examples_text}"
        f"User's request: {prompt}\n\n"
        f"{RAG_ASC_GENERATION_PROMPT}"
    )
    
    print("\nRAW SYSTEM PROMPT SENT TO ASC GENERATION MODEL:")
    print("-" * 40)
    print(system_prompt)
    print("-" * 40)
    
    print("\nRAW USER PROMPT SENT TO ASC GENERATION MODEL:")
    print("-" * 40)
    print(user_prompt)
    print("-" * 40)
    
    try:
        import openai
        response = openai.ChatCompletion.create(
            model=llm_provider.asc_gen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        asc_code = response.choices[0].message.content.strip()
        
        # Clean the ASC code if needed
        if asc_code.upper() != "N":
            asc_code = extract_clean_asc_code(asc_code)
        
        print("\nRAW ASC CODE GENERATED:")
        print("-" * 40)
        print(asc_code)
        print("-" * 40)
        
        # Validate the generated ASC code
        if validate_asc_code(asc_code):
            print("ASC code validation passed")
            return asc_code
        else:
            print("ASC code validation failed - will retry generation")
            # Could implement a retry mechanism here
            return asc_code  # Still return for now
            
    except Exception as e:
        print(f"Error generating ASC code: {str(e)}")
        return "Error: Failed to generate circuit"

def step3_process_ltspice(asc_code, ltspice_interface, prompt_id=1, iteration=0):
    """
    Step 3: Process the ASC code with LTSpice
    
    Args:
        asc_code (str): ASC code to process
        ltspice_interface: The LTSpice interface instance
        prompt_id (int): Prompt ID for folder structure
        iteration (int): Iteration number for folder structure
        
    Returns:
        tuple: (asc_path, image_path) on success, or None on failure
    """
    print_separator(f"STEP 3: LTSPICE PROCESSING (ITERATION {iteration})")
    
    print("Processing ASC code with LTSpice...")
    print(f"ASC code length: {len(asc_code)} characters")
    print(f"First 100 chars: {asc_code[:100]}...")
    
    # Validate ASC code before sending to LTSpice
    if not validate_asc_code(asc_code):
        print("Error: Invalid ASC code. Skipping LTSpice processing.")
        return None
    
    result = ltspice_interface.process_circuit(asc_code, prompt_id=prompt_id, iteration=iteration)
    
    if result:
        asc_path, image_path = result
        print(f"\nLTSpice processing successful!")
        print(f"ASC file saved to: {asc_path}")
        print(f"Image saved to: {image_path}")
        return result
    else:
        print("\nLTSpice processing failed!")
        return None

def step4_analyze_vision(image_path, original_request, vision_analyzer):
    """
    Step 4: Analyze the circuit image using vision model
    
    Args:
        image_path (str): Path to the circuit image
        original_request (str): Original user request
        vision_analyzer: The vision analyzer instance
        
    Returns:
        str: Vision analysis result
    """
    print_separator("STEP 4: VISION ANALYSIS")
    
    print(f"Analyzing image at: {image_path}")
    print(f"Original request: {original_request}")
    
    # Since we don't have direct access to the Vision Analyzer's raw prompt,
    # we'll just call the analyze method and print the result
    vision_feedback = vision_analyzer.analyze_circuit_image(image_path, original_request)
    
    print("\nRAW VISION FEEDBACK:")
    print("-" * 40)
    print(vision_feedback)
    print("-" * 40)
    
    return vision_feedback

def step5a_generate_feedback_response(vision_feedback, llm_provider):
    """
    Step 5a: Generate user-friendly response based on vision feedback
    
    Args:
        vision_feedback (str): Feedback from vision model
        llm_provider: The LLM provider instance
        
    Returns:
        str: User-friendly response
    """
    print_separator("STEP 5A: FEEDBACK RESPONSE")
    
    is_success = vision_feedback.strip() == 'Y'
    print(f"Circuit implementation success: {is_success}")
    
    # Build prompt based on feedback
    prompt = VISION_FEEDBACK_PROMPT.format(
        vision_feedback=vision_feedback
    )
    
    print("\nRAW PROMPT SENT TO FEEDBACK MODEL:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    try:
        import openai
        response = openai.ChatCompletion.create(
            model=llm_provider.chat_model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        feedback_response = response.choices[0].message.content.strip()
        
        print("\nRAW FEEDBACK RESPONSE:")
        print("-" * 40)
        print(feedback_response)
        print("-" * 40)
        
        return feedback_response
    except Exception as e:
        print(f"Error generating feedback response: {str(e)}")
        # Provide a default response in case of error
        if vision_feedback.strip() == 'Y':
            return "Your circuit is complete and meets the requirements."
        else:
            return "I identified some issues with the circuit that need to be addressed."

def step5b_refine_asc_code(prompt, history, llm_provider):
    """
    Step 5b: Refine ASC code based on vision feedback history
    
    Args:
        prompt (str): Original user request
        history (list): List of dictionaries containing previous iterations
        llm_provider: The LLM provider instance
        
    Returns:
        str: Refined ASC code
    """
    print_separator("STEP 5B: ASC CODE REFINEMENT")
    
    # Build refinement prompt - FIXED: use a separate variable for each part of the prompt
    refinement_prompt_parts = ["Below are previous attempts and feedback:\n\n"]
    
    for item in history:
        refinement_prompt_parts.append(f"Attempt {item.get('iteration', '?')} ASC code:\n{item['asc_code']}\n\n")
        refinement_prompt_parts.append(f"Vision feedback (Iteration {item.get('iteration','?')}): {item['vision_feedback']}\n\n")
        
    refinement_prompt_parts.append(f"Original user's request: {prompt}\n\n")
    refinement_prompt_parts.append(REFINEMENT_PROMPT_TEMPLATE)
    
    # Join the parts to create the final prompt
    refinement_prompt = "".join(refinement_prompt_parts)
    
    print("\nRAW REFINEMENT PROMPT SENT TO ASC REFINEMENT MODEL:")
    print("-" * 40)
    print(refinement_prompt)
    print("-" * 40)
    
    try:
        # Call the ASC refinement model
        import openai
        response = openai.ChatCompletion.create(
            model=llm_provider.asc_gen_model,
            messages=[
                {"role": "system", "content": GENERAL_INSTRUCTION},
                {"role": "user", "content": refinement_prompt}
            ]
        )
        
        refined_asc = response.choices[0].message.content.strip()
        
        # Clean the ASC code if needed
        if "Version 4" in refined_asc:
            refined_asc = extract_clean_asc_code(refined_asc)
        
        print("\nREFINED ASC CODE:")
        print("-" * 40)
        print(refined_asc)
        print("-" * 40)
        
        # Validate the refined ASC code
        if validate_asc_code(refined_asc):
            print("Refined ASC code validation passed")
        else:
            print("Refined ASC code validation failed")
        
        return refined_asc
    except Exception as e:
        print(f"Error refining ASC code: {str(e)}")
        return f"Error: Failed to refine circuit: {str(e)}"

def test_iterative_pipeline(prompt, prompt_id=1, max_iterations=3):
    """
    Test the entire pipeline with a given prompt for multiple iterations
    
    Args:
        prompt (str): User prompt to test
        prompt_id (int): ID for folder structure
        max_iterations (int): Maximum number of iterations to perform
    """
    # Initialize components
    config = Config()
    llm_provider = OpenAIProvider(config)
    vector_store = VectorStore(config)
    ltspice_interface = LTSpiceInterface(config)
    vision_analyzer = VisionAnalyzer(config)
    
    # Initialize result dictionary
    result = {
        "prompt": prompt,
        "prompt_id": prompt_id,
        "is_circuit_related": False,
        "chat_response": "",
        "iterations": []
    }
    
    print("\n\n")
    print("=" * 80)
    print(f"TESTING ITERATIVE PIPELINE WITH PROMPT: '{prompt}'")
    print(f"MAXIMUM ITERATIONS: {max_iterations}")
    print("=" * 80)
    print("\n")
    
    # Load vector store
    print("Loading vector store...")
    vector_store.load()
    print("Vector store loaded successfully")
    
    start_time = time.time()
    
    try:
        # Step 1: Evaluate if circuit-related
        is_circuit_related = step1_evaluate_circuit_request(prompt, llm_provider)
        result["is_circuit_related"] = is_circuit_related
        
        if not is_circuit_related:
            print_separator("NON-CIRCUIT REQUEST DETECTED")
            print("Stopping pipeline early - will only generate a brief chat response.")
            chat_response = step2a_generate_chat_response(prompt, is_circuit_related, llm_provider)
            result["chat_response"] = chat_response
            print("\nTest completed for non-circuit request.")
            return result
        
        # Only continue with circuit-related requests
        print_separator("CIRCUIT REQUEST CONFIRMED - CONTINUING PIPELINE")
        
        # Generate chat response
        chat_response = step2a_generate_chat_response(prompt, is_circuit_related, llm_provider)
        result["chat_response"] = chat_response
        
        # Generate initial ASC code
        asc_code = step2b_generate_asc_code(prompt, llm_provider, vector_store)
        
        # Check if valid ASC code was generated
        if asc_code == "N" or not asc_code or asc_code.startswith("Error"):
            print_separator("INVALID ASC CODE")
            print("ASC generation failed or request was misclassified as circuit-related.")
            return result
        
        # Start iterative process
        current_iteration = 0
        history = []
        circuit_verified = False
        current_asc_code = asc_code
        
        # Perform iterations until circuit is verified or max iterations reached
        while current_iteration < max_iterations:
            print_separator(f"STARTING ITERATION {current_iteration}")
            
            # Step 3: Process with LTSpice
            ltspice_result = step3_process_ltspice(current_asc_code, ltspice_interface, 
                                                  prompt_id=prompt_id, 
                                                  iteration=current_iteration)
            
            if not ltspice_result:
                print_separator(f"LTSPICE PROCESSING FAILED (ITERATION {current_iteration})")
                break
            
            asc_path, image_path = ltspice_result
            
            # Step 4: Analyze vision
            vision_feedback = step4_analyze_vision(image_path, prompt, vision_analyzer)
            
            # Store iteration data
            iteration_data = {
                "iteration": current_iteration,
                "asc_code": current_asc_code,
                "asc_path": asc_path,
                "image_path": image_path,
                "vision_feedback": vision_feedback
            }
            
            # Step 5a: Generate feedback response
            feedback_response = step5a_generate_feedback_response(vision_feedback, llm_provider)
            iteration_data["feedback_response"] = feedback_response
            
            # Add to history
            history.append(iteration_data)
            result["iterations"].append(iteration_data)
            
            # Check if circuit is verified
            if vision_feedback.strip() == 'Y':
                print_separator(f"CIRCUIT VERIFIED (ITERATION {current_iteration})")
                circuit_verified = True
                break
                
            # Check if we should continue
            if current_iteration >= max_iterations - 1:
                print_separator(f"REACHED MAXIMUM ITERATIONS ({max_iterations})")
                break
            
            # Step 5b: Refine ASC code for next iteration
            print_separator(f"REFINING ASC CODE FOR ITERATION {current_iteration + 1}")
            refined_asc_code = step5b_refine_asc_code(prompt, history, llm_provider)
            
            # Check if we have a valid refined ASC code
            if not refined_asc_code or refined_asc_code.startswith("Error") or not validate_asc_code(refined_asc_code):
                print_separator(f"REFINEMENT FAILED (ITERATION {current_iteration})")
                break
                
            # Update for next iteration
            iteration_data["refined_asc_code"] = refined_asc_code
            current_asc_code = refined_asc_code
            current_iteration += 1
            
        # Save complete history to JSON file
        history_path = f"pipeline_history_prompt{prompt_id}.json"
        with open(history_path, "w") as f:
            json.dump({
                "prompt": prompt,
                "chat_response": chat_response,
                "iterations": history
            }, f, indent=2)
        print(f"\nSaved complete pipeline history to {history_path}")
        
        # Set final status
        result["final_status"] = "Circuit verified" if circuit_verified else f"Circuit not verified after {current_iteration + 1} iterations"
        result["success"] = circuit_verified
        
    except Exception as e:
        print(f"ERROR in pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        result["error"] = str(e)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print_separator("PIPELINE TEST COMPLETED")
    print(f"Total processing time: {elapsed_time:.2f} seconds")
    print(f"Total iterations performed: {len(result['iterations'])}")
    print(f"Final status: {result.get('final_status', 'Unknown')}")
    
    # Print summary of each iteration
    print("\nIteration Summary:")
    for i, iteration in enumerate(result.get("iterations", [])):
        is_verified = iteration.get("vision_feedback", "") == "Y"
        status = "✓ VERIFIED" if is_verified else "✗ NOT VERIFIED"
        print(f"Iteration {i}: {status}")
    
    return result

def main():
    """Main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(description='Test the iterative LTSpice Agent pipeline')
    parser.add_argument('--prompt', '-p', type=str, default="Create a low pass filter", help='Prompt to test')
    parser.add_argument('--id', type=int, default=1, help='Prompt ID for folder structure')
    parser.add_argument('--iterations', '-i', type=int, default=3, help='Maximum number of iterations')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger('electroninja').setLevel(logging.DEBUG)
        
    # Run the test
    test_iterative_pipeline(args.prompt, prompt_id=args.id, max_iterations=args.iterations)

if __name__ == "__main__":
    main()