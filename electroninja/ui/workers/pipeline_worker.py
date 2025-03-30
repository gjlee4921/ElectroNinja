import asyncio
import logging
import traceback
import time
import functools
import concurrent.futures
import os

logger = logging.getLogger('electroninja')

async def run_pipeline(user_message, evaluator, chat_generator, circuit_generator,
                       ltspice_manager, vision_processor, prompt_id=1, max_iterations=3,
                       update_callbacks=None, skip_evaluation=False, executor=None, 
                       description_creator=None, previous_description=None):
    """
    Asynchronous pipeline worker with description-centric workflow.
    
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
        executor: Optional thread pool executor to use for background tasks
        description_creator: Instance of CreateDescription for creating and saving circuit descriptions
        previous_description: Previous circuit description (from last prompt) if available
    """
    pipeline_start = time.time()
    active_tasks = set()
    
    # Helper function to create and track tasks
    def create_task(coro):
        task = asyncio.create_task(coro)
        active_tasks.add(task)
        task.add_done_callback(lambda t: active_tasks.discard(t))
        return task
    
    # Helper for running functions in a thread
    async def run_in_thread(func, *args, **kwargs):
        if executor:
            # Use the provided executor
            return await asyncio.get_event_loop().run_in_executor(
                executor, 
                functools.partial(func, *args, **kwargs)
            )
        else:
            # Fall back to asyncio.to_thread if no executor provided
            return await asyncio.to_thread(func, *args, **kwargs)
    
    try:
        # Step 1: (Optionally) Evaluate if the request is circuit-related
        if not skip_evaluation:
            # Run the evaluation in a separate thread to avoid blocking the event loop
            is_circuit = await run_in_thread(evaluator.is_circuit_related, user_message)
            # Callback to update UI with evaluation result
            if update_callbacks and "evaluation_done" in update_callbacks:
                update_callbacks["evaluation_done"](is_circuit)
            # If not circuit-related, generate a simple response and exit
            if not is_circuit:
                response = await run_in_thread(chat_generator.generate_response, user_message)
                if update_callbacks and "non_circuit_response" in update_callbacks:
                    update_callbacks["non_circuit_response"](response)
                return
        else:
            # If skipping evaluation, assume it's a valid circuit request
            if update_callbacks and "evaluation_done" in update_callbacks:
                update_callbacks["evaluation_done"](True)

        # Step 2: Generate circuit description first
        if description_creator:
            # Create description from previous description and new request
            description = await run_in_thread(
                description_creator.create_description,
                previous_description if previous_description else "None", 
                user_message
            )
            
            if update_callbacks and "description_generated" in update_callbacks:
                update_callbacks["description_generated"](description)
            
            # Save the description to a file
            description_path = await run_in_thread(
                description_creator.save_description, 
                description, 
                prompt_id
            )
            
            logger.info(f"Using description for ASC generation: {description}")
        else:
            # If no description creator available, use the original message
            description = user_message
            logger.info("No description creator available, using original request")

        # Step 3: Generate initial chat response and ASC code concurrently
        # Create tasks for parallel execution
        chat_task = create_task(
            run_in_thread(chat_generator.generate_response, user_message)
        )
        
        # Use description for ASC generation instead of user_message
        asc_task = create_task(
            run_in_thread(circuit_generator.generate_asc_code, description)
        )
        
        # Await the chat response first and update immediately for better UX
        chat_response = await chat_task
        if update_callbacks and "initial_chat_response" in update_callbacks:
            update_callbacks["initial_chat_response"](chat_response)
        
        # Then wait for the ASC code
        asc_code = await asc_task
        if update_callbacks and "asc_code_generated" in update_callbacks:
            update_callbacks["asc_code_generated"](asc_code)

        # Step 4: Process LTSpice for iteration 0 (initial circuit)
        ltspice_result = await run_in_thread(ltspice_manager.process_circuit, 
                                            asc_code, prompt_id, 0)
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

        # Step 5: Get vision feedback for iteration 0
        # Use the original user message for context in vision analysis
        vision_result = await run_in_thread(vision_processor.analyze_circuit_image, 
                                           image_path, user_message)
        if update_callbacks and "vision_feedback" in update_callbacks:
            update_callbacks["vision_feedback"](vision_result)
            
        # Always generate a final feedback response using the same function
        complete_response = await run_in_thread(chat_generator.generate_feedback_response, 
                                              vision_result)
        if update_callbacks and "final_complete_chat_response" in update_callbacks:
            update_callbacks["final_complete_chat_response"](complete_response)
            
        # If the circuit is already correct (vision_result is 'Y'), skip refinement
        if vision_result.strip() == 'Y':
            return

        # Step 6: Iterative refinement loop
        # Build history to track iterations for context
        history = [{"asc_code": asc_code, "vision_feedback": vision_result, "iteration": 0}]
        iteration = 1
        
        while iteration < max_iterations:
            # Update UI with current iteration
            if update_callbacks and "iteration_update" in update_callbacks:
                update_callbacks["iteration_update"](iteration)
                
            # Generate feedback response explaining what needs to be fixed
            feedback_response = await run_in_thread(chat_generator.generate_feedback_response, 
                                                  vision_result)
            if update_callbacks and "feedback_chat_response" in update_callbacks:
                update_callbacks["feedback_chat_response"](feedback_response)
                
            # Refine the ASC code based on feedback and previous attempts
            # Use the description for refinement context, not the original user message
            refined_code = await run_in_thread(circuit_generator.refine_asc_code, 
                                             description, history)
            if update_callbacks and "asc_refined" in update_callbacks:
                update_callbacks["asc_refined"](refined_code)
                
            # Process refined circuit with LTSpice
            ltspice_result = await run_in_thread(ltspice_manager.process_circuit, 
                                               refined_code, prompt_id, iteration)
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
            vision_result = await run_in_thread(vision_processor.analyze_circuit_image, 
                                              image_path, user_message)
            if update_callbacks and "vision_feedback" in update_callbacks:
                update_callbacks["vision_feedback"](vision_result)
                
            # Add this iteration to history for context in future refinements
            history.append({
                "asc_code": refined_code, 
                "vision_feedback": vision_result, 
                "iteration": iteration
            })
            
            # Generate complete feedback response for this iteration
            complete_response = await run_in_thread(chat_generator.generate_feedback_response, 
                                                  vision_result)
            if update_callbacks and "final_complete_chat_response" in update_callbacks:
                update_callbacks["final_complete_chat_response"](complete_response)
                
            # If the circuit meets requirements, exit refinement loop
            if vision_result.strip() == 'Y':
                break
                
            # Increment iteration counter
            iteration += 1
            
        logger.info(f"Pipeline completed after {iteration} iterations in "
                   f"{time.time() - pipeline_start:.2f} seconds")
            
    except asyncio.CancelledError:
        logger.info("Pipeline task cancelled")
        # Cancel any active subtasks
        for task in active_tasks:
            if not task.done():
                task.cancel()
        raise
    except Exception as e:
        # Handle any exceptions in the pipeline
        logger.error("Exception in async pipeline: " + str(e))
        traceback.print_exc()
    finally:
        # Cancel any remaining active tasks
        for task in active_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to finish cancellation (with timeout)
        if active_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*[asyncio.shield(task) for task in active_tasks], 
                                  return_exceptions=True),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Some tasks didn't complete cancellation in time: {str(e)}")
                
        # Always call the processing_finished callback to re-enable UI
        if update_callbacks and "processing_finished" in update_callbacks:
            update_callbacks["processing_finished"]()