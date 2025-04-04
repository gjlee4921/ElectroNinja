import asyncio
import logging
import time
import functools
import traceback

logger = logging.getLogger('electroninja')

async def run_pipeline(user_message, evaluator, chat_generator, circuit_generator,
                       ltspice_manager, vision_processor, prompt_id, max_iterations,
                       update_callbacks=None, not_first_eval=False, executor=None, 
                       description_creator=None, previous_description=None):
    """
    Asynchronous pipeline worker that implements the full circuit generation and refinement loop.

    Steps:
      1. Evaluate if the request is circuit-related.
         - If the evaluation returns 'N', a non-circuit response is generated and the function returns False.
      2. Generate (or update) the circuit description and save it.
      3. Generate an initial chat response and ASC code concurrently.
      4. Process the initial ASC code with LTSpice (iteration 0) and display results.
      5. Run vision analysis on the generated image using the saved description.
         - If vision feedback equals 'Y', finish the pipeline.
         - Otherwise, enter an iterative refinement loop.
      6. In the refinement loop, generate refined ASC code using vision feedback,
         process it with LTSpice, and re-run vision analysis until requirements are met
         or max iterations are reached.
      7. If we exit the loop without a correct circuit, optionally send a final note.
      8. Finally, call the processing_finished callback.
      
    Returns:
       True if the request is circuit-related and processed; False if the evaluation returned 'N'.
    """
    pipeline_start = time.time()

    async def run_in_thread(func, *args, **kwargs):
        if executor:
            return await asyncio.get_event_loop().run_in_executor(
                executor, functools.partial(func, *args, **kwargs))
        else:
            return await asyncio.to_thread(func, *args, **kwargs)

    try:
        # Step 1: Evaluate if the request is circuit-related.
        if not_first_eval:
            # For modification requests: evaluate and merge with previous components.
            new_eval = await run_in_thread(evaluator.provider.evaluate_circuit_request, user_message)
            eval_result = await run_in_thread(evaluator.merge_components, new_eval, prompt_id - 1, prompt_id)
            if update_callbacks and "evaluation_done" in update_callbacks:
                update_callbacks["evaluation_done"](eval_result)
            if eval_result.strip().upper() == 'N':
                response = await run_in_thread(chat_generator.generate_response, user_message)
                if update_callbacks and "non_circuit_response" in update_callbacks:
                    update_callbacks["non_circuit_response"](response)
                return False
        else:
            # For the initial request, use the standard evaluation method.
            eval_result = await run_in_thread(evaluator.is_circuit_related, user_message)
            if update_callbacks and "evaluation_done" in update_callbacks:
                update_callbacks["evaluation_done"](eval_result)
            if eval_result.strip().upper() == 'N':
                response = await run_in_thread(chat_generator.generate_response, user_message)
                if update_callbacks and "non_circuit_response" in update_callbacks:
                    update_callbacks["non_circuit_response"](response)
                return False

        # Step 2: Generate circuit description.
        if description_creator:
            desc = await run_in_thread(
                description_creator.create_description,
                previous_description if previous_description else "None", 
                user_message
            )
            if update_callbacks and "description_generated" in update_callbacks:
                update_callbacks["description_generated"](desc)
            await run_in_thread(description_creator.save_description, desc, prompt_id)
            description = desc
        else:
            description = user_message
        logger.info(f"Using description: {description}")

        # Step 3: Generate initial chat response and ASC code concurrently.
        chat_task = asyncio.create_task(
            run_in_thread(chat_generator.generate_response, user_message)
        )
        asc_task = asyncio.create_task(
            run_in_thread(circuit_generator.generate_asc_code, description, prompt_id)
        )

        chat_response = await chat_task
        if update_callbacks and "initial_chat_response" in update_callbacks:
            update_callbacks["initial_chat_response"](chat_response)

        asc_code = await asc_task
        if update_callbacks and "asc_code_generated" in update_callbacks:
            update_callbacks["asc_code_generated"](asc_code)

        # Step 4: Process initial ASC code with LTSpice (iteration 0)
        ltspice_result = await run_in_thread(
            ltspice_manager.process_circuit, asc_code, prompt_id, 0
        )
        if ltspice_result:
            asc_path, image_path = ltspice_result
            if update_callbacks and "ltspice_processed" in update_callbacks:
                update_callbacks["ltspice_processed"]((asc_path, image_path, 0))
        else:
            logger.error("LTSpice processing failed at iteration 0")
            if update_callbacks and "ltspice_processed" in update_callbacks:
                update_callbacks["ltspice_processed"]((None, None, 0))
            # Even if LTSpice fails, the request was circuit-related.
            return True

        # Step 5: Get vision feedback for iteration 0 using saved description.
        vision_feedback = await run_in_thread(
            vision_processor.analyze_circuit_image, prompt_id, 0
        )
        if update_callbacks and "vision_feedback" in update_callbacks:
            update_callbacks["vision_feedback"](vision_feedback)

        # Use the feedback callback for intermediate responses.
        intermediate_response = await run_in_thread(
            chat_generator.generate_feedback_response, vision_feedback
        )
        if update_callbacks and "feedback_chat_response" in update_callbacks:
            update_callbacks["feedback_chat_response"](intermediate_response)

        # If circuit verified, we’re done.
        if vision_feedback.strip().upper() == 'Y':
            return True

        # Step 6: Iterative refinement loop.
        iteration = 1
        while iteration < max_iterations:
            if update_callbacks and "iteration_update" in update_callbacks:
                update_callbacks["iteration_update"](iteration)

            refined_code = await run_in_thread(
                circuit_generator.refine_asc_code, prompt_id, iteration, vision_feedback
            )
            if update_callbacks and "asc_refined" in update_callbacks:
                update_callbacks["asc_refined"](refined_code)

            ltspice_result = await run_in_thread(
                ltspice_manager.process_circuit, refined_code, prompt_id, iteration
            )
            if ltspice_result:
                asc_path, image_path = ltspice_result
                if update_callbacks and "ltspice_processed" in update_callbacks:
                    update_callbacks["ltspice_processed"]((asc_path, image_path, iteration))
            else:
                logger.error(f"LTSpice processing failed at iteration {iteration}")
                if update_callbacks and "ltspice_processed" in update_callbacks:
                    update_callbacks["ltspice_processed"]((None, None, iteration))
                break

            vision_feedback = await run_in_thread(
                vision_processor.analyze_circuit_image, prompt_id, iteration
            )
            if update_callbacks and "vision_feedback" in update_callbacks:
                update_callbacks["vision_feedback"](vision_feedback)

            feedback_response = await run_in_thread(
                chat_generator.generate_feedback_response, vision_feedback
            )
            if update_callbacks and "feedback_chat_response" in update_callbacks:
                update_callbacks["feedback_chat_response"](feedback_response)

            if vision_feedback.strip().upper() == 'Y':
                return True
            iteration += 1

        # Step 7: If we got here and the circuit was never verified as correct,
        # optionally provide a final note.
        if vision_feedback.strip().upper() != 'Y':
            final_note = "Maximum iterations reached. The circuit may need further manual adjustments."
            if update_callbacks and "final_complete_chat_response" in update_callbacks:
                update_callbacks["final_complete_chat_response"](final_note)

        total_time = time.time() - pipeline_start
        logger.info(f"Pipeline completed after {iteration} iterations in {total_time:.2f} seconds")
        return True

    except asyncio.CancelledError:
        logger.info("Pipeline task cancelled")
        raise
    except Exception as e:
        logger.error("Exception in pipeline: " + str(e))
        traceback.print_exc()
    finally:
        if update_callbacks and "processing_finished" in update_callbacks:
            update_callbacks["processing_finished"]()
