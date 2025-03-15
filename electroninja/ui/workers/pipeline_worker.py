# electroninja/ui/workers/pipeline_worker.py
import asyncio
import logging
import traceback

logger = logging.getLogger('electroninja')

async def run_pipeline(user_message, evaluator, chat_generator, circuit_generator,
                       ltspice_manager, vision_processor, prompt_id=1, max_iterations=3,
                       update_callbacks=None):
    """
    Asynchronous pipeline worker that replaces the QThread-based implementation.
    The update_callbacks parameter should be a dict of callback functions to update the UI.
    """
    try:
        # Step 1: Evaluate if the request is circuit-related.
        is_circuit = await asyncio.to_thread(evaluator.is_circuit_related, user_message)
        if update_callbacks and "evaluation_done" in update_callbacks:
            update_callbacks["evaluation_done"](is_circuit)
        if not is_circuit:
            response = await asyncio.to_thread(chat_generator.generate_response, user_message)
            if update_callbacks and "non_circuit_response" in update_callbacks:
                update_callbacks["non_circuit_response"](response)
            return

        # Step 2: Generate initial chat response and ASC code concurrently.
        chat_task = asyncio.create_task(
            asyncio.to_thread(chat_generator.generate_response, user_message)
        )
        asc_task = asyncio.create_task(
            asyncio.to_thread(circuit_generator.generate_asc_code, user_message)
        )
        # Await the chat response first and update immediately.
        chat_response = await chat_task
        if update_callbacks and "initial_chat_response" in update_callbacks:
            update_callbacks["initial_chat_response"](chat_response)
        # Then wait for the ASC code.
        asc_code = await asc_task
        if update_callbacks and "asc_code_generated" in update_callbacks:
            update_callbacks["asc_code_generated"](asc_code)

        # Step 3: Process LTSpice for iteration 0.
        ltspice_result = await asyncio.to_thread(ltspice_manager.process_circuit, asc_code, prompt_id, 0)
        if ltspice_result:
            asc_path, image_path = ltspice_result
            if update_callbacks and "ltspice_processed" in update_callbacks:
                update_callbacks["ltspice_processed"]((asc_path, image_path, 0))
        else:
            logger.error("LTSpice processing failed at iteration 0")
            if update_callbacks and "ltspice_processed" in update_callbacks:
                update_callbacks["ltspice_processed"]((None, None, 0))
            return

        # Step 4: Get vision feedback for iteration 0.
        vision_result = await asyncio.to_thread(vision_processor.analyze_circuit_image, image_path, user_message)
        if update_callbacks and "vision_feedback" in update_callbacks:
            update_callbacks["vision_feedback"](vision_result)
        if vision_result.strip() == 'Y':
            complete_response = await asyncio.to_thread(chat_generator.generate_response, "Your circuit is complete!")
            if update_callbacks and "final_complete_chat_response" in update_callbacks:
                update_callbacks["final_complete_chat_response"](complete_response)
            return

        # Step 5: Iterative refinement loop.
        history = [{"asc_code": asc_code, "vision_feedback": vision_result, "iteration": 0}]
        iteration = 1
        while iteration < max_iterations:
            if update_callbacks and "iteration_update" in update_callbacks:
                update_callbacks["iteration_update"](iteration)
            feedback_response = await asyncio.to_thread(chat_generator.generate_feedback_response, vision_result)
            if update_callbacks and "feedback_chat_response" in update_callbacks:
                update_callbacks["feedback_chat_response"](feedback_response)
            refined_code = await asyncio.to_thread(circuit_generator.refine_asc_code, user_message, history)
            if update_callbacks and "asc_refined" in update_callbacks:
                update_callbacks["asc_refined"](refined_code)
            ltspice_result = await asyncio.to_thread(ltspice_manager.process_circuit, refined_code, prompt_id, iteration)
            if ltspice_result:
                asc_path, image_path = ltspice_result
                if update_callbacks and "ltspice_processed" in update_callbacks:
                    update_callbacks["ltspice_processed"]((asc_path, image_path, iteration))
            else:
                logger.error(f"LTSpice processing failed at iteration {iteration}")
                if update_callbacks and "ltspice_processed" in update_callbacks:
                    update_callbacks["ltspice_processed"]((None, None, iteration))
                break
            vision_result = await asyncio.to_thread(vision_processor.analyze_circuit_image, image_path, user_message)
            if update_callbacks and "vision_feedback" in update_callbacks:
                update_callbacks["vision_feedback"](vision_result)
            history.append({"asc_code": refined_code, "vision_feedback": vision_result, "iteration": iteration})
            if vision_result.strip() == 'Y':
                complete_response = await asyncio.to_thread(chat_generator.generate_response, "Your circuit is complete!")
                if update_callbacks and "final_complete_chat_response" in update_callbacks:
                    update_callbacks["final_complete_chat_response"](complete_response)
                break
            iteration += 1
    except Exception as e:
        logger.error("Exception in async pipeline: " + str(e))
        traceback.print_exc()
    finally:
        if update_callbacks and "processing_finished" in update_callbacks:
            update_callbacks["processing_finished"]()
