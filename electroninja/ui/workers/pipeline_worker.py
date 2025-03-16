import asyncio
import logging
import traceback
import time

logger = logging.getLogger('electroninja')

async def run_pipeline(user_message, evaluator, chat_generator, circuit_generator,
                       ltspice_manager, vision_processor, prompt_id=1, max_iterations=3,
                       update_callbacks=None, skip_evaluation=False):
    """
    Asynchronous pipeline worker.
    If skip_evaluation is True, the evaluation step is skipped and the request is assumed to be relevant.
    
    Args:
        user_message: The user's message or merged request
        evaluator: Instance of RequestEvaluator for determining if requests are circuit-related
        chat_generator: Instance of ChatResponseGenerator for creating text responses
        circuit_generator: Instance of CircuitGenerator for creating and refining ASC code
        ltspice_manager: Instance of LTSpiceManager for running circuit simulations
        vision_processor: Instance of VisionProcessor for analyzing circuit images
        prompt_id: Identifier for the current prompt/session
        max_iterations: Maximum number of refinement iterations to attempt
        update_callbacks: Dictionary of callback functions for UI updates
        skip_evaluation: Whether to skip the evaluation step (for follow-up requests)
    """
    pipeline_start = time.time()
    
    try:
        # Step 1: (Optionally) Evaluate if the request is circuit-related
        if not skip_evaluation:
            # Run the evaluation in a separate thread to avoid blocking the event loop
            is_circuit = await asyncio.to_thread(evaluator.is_circuit_related, user_message)
            # Callback to update UI with evaluation result
            if update_callbacks and "evaluation_done" in update_callbacks:
                update_callbacks["evaluation_done"](is_circuit)
            # If not circuit-related, generate a simple response and exit
            if not is_circuit:
                response = await asyncio.to_thread(chat_generator.generate_response, user_message)
                if update_callbacks and "non_circuit_response" in update_callbacks:
                    update_callbacks["non_circuit_response"](response)
                return
        else:
            # If skipping evaluation, assume it's a valid circuit request
            if update_callbacks and "evaluation_done" in update_callbacks:
                update_callbacks["evaluation_done"](True)

        # Step 2: Generate initial chat response and ASC code concurrently
        # Create tasks for parallel execution
        chat_task = asyncio.create_task(
            asyncio.to_thread(chat_generator.generate_response, user_message)
        )
        
        asc_task = asyncio.create_task(
            asyncio.to_thread(circuit_generator.generate_asc_code, user_message)
        )
        
        # Await the chat response first and update immediately for better UX
        chat_response = await chat_task
        if update_callbacks and "initial_chat_response" in update_callbacks:
            update_callbacks["initial_chat_response"](chat_response)
        
        # Then wait for the ASC code
        asc_code = await asc_task
        if update_callbacks and "asc_code_generated" in update_callbacks:
            update_callbacks["asc_code_generated"](asc_code)

        # Step 3: Process LTSpice for iteration 0 (initial circuit)
        ltspice_result = await asyncio.to_thread(ltspice_manager.process_circuit, asc_code, prompt_id, 0)
        if ltspice_result:
            # Unpack result tuple (asc file path, image path)
            asc_path, image_path = ltspice_result
            if update_callbacks and "ltspice_processed" in update_callbacks:
                update_callbacks["ltspice_processed"]((asc_path, image_path, 0))
        else:
            # Handle LTSpice processing failure
            logger.error("LTSpice processing failed at iteration 0")
            if update_callbacks and "ltspice_processed" in update_callbacks:
                update_callbacks["ltspice_processed"]((None, None, 0))
            return

        # Step 4: Get vision feedback for iteration 0
        # Analyze the circuit image to determine if it meets requirements
        vision_result = await asyncio.to_thread(vision_processor.analyze_circuit_image, image_path, user_message)
        if update_callbacks and "vision_feedback" in update_callbacks:
            update_callbacks["vision_feedback"](vision_result)
            
        # Always generate a final feedback response using the same function
        complete_response = await asyncio.to_thread(chat_generator.generate_feedback_response, vision_result)
        if update_callbacks and "final_complete_chat_response" in update_callbacks:
            update_callbacks["final_complete_chat_response"](complete_response)
            
        # If the circuit is already correct (vision_result is 'Y'), skip refinement
        if vision_result.strip() == 'Y':
            return

        # Step 5: Iterative refinement loop
        # Build history to track iterations for context
        history = [{"asc_code": asc_code, "vision_feedback": vision_result, "iteration": 0}]
        iteration = 1
        
        while iteration < max_iterations:
            # Update UI with current iteration
            if update_callbacks and "iteration_update" in update_callbacks:
                update_callbacks["iteration_update"](iteration)
                
            # Generate feedback response explaining what needs to be fixed
            feedback_response = await asyncio.to_thread(chat_generator.generate_feedback_response, vision_result)
            if update_callbacks and "feedback_chat_response" in update_callbacks:
                update_callbacks["feedback_chat_response"](feedback_response)
                
            # Refine the ASC code based on feedback and previous attempts
            refined_code = await asyncio.to_thread(circuit_generator.refine_asc_code, user_message, history)
            if update_callbacks and "asc_refined" in update_callbacks:
                update_callbacks["asc_refined"](refined_code)
                
            # Process refined circuit with LTSpice
            ltspice_result = await asyncio.to_thread(ltspice_manager.process_circuit, refined_code, prompt_id, iteration)
            if ltspice_result:
                # Unpack result tuple
                asc_path, image_path = ltspice_result
                if update_callbacks and "ltspice_processed" in update_callbacks:
                    update_callbacks["ltspice_processed"]((asc_path, image_path, iteration))
            else:
                # Handle LTSpice processing failure
                logger.error(f"LTSpice processing failed at iteration {iteration}")
                if update_callbacks and "ltspice_processed" in update_callbacks:
                    update_callbacks["ltspice_processed"]((None, None, iteration))
                break
                
            # Analyze the refined circuit image
            vision_result = await asyncio.to_thread(vision_processor.analyze_circuit_image, image_path, user_message)
            if update_callbacks and "vision_feedback" in update_callbacks:
                update_callbacks["vision_feedback"](vision_result)
                
            # Add this iteration to history for context in future refinements
            history.append({"asc_code": refined_code, "vision_feedback": vision_result, "iteration": iteration})
            
            # Generate complete feedback response for this iteration
            complete_response = await asyncio.to_thread(chat_generator.generate_feedback_response, vision_result)
            if update_callbacks and "final_complete_chat_response" in update_callbacks:
                update_callbacks["final_complete_chat_response"](complete_response)
                
            # If the circuit meets requirements, exit refinement loop
            if vision_result.strip() == 'Y':
                break
                
            # Increment iteration counter
            iteration += 1
            
    except Exception as e:
        # Handle any exceptions in the pipeline
        logger.error("Exception in async pipeline: " + str(e))
        traceback.print_exc()
    finally:
        # Always call the processing_finished callback to re-enable UI
        if update_callbacks and "processing_finished" in update_callbacks:
            update_callbacks["processing_finished"]()