"""OpenAI Assistant API integration."""

import logging
import time
import asyncio
from typing import Dict, Optional
import openai
from openai import AsyncOpenAI

from bot.config import config

logger = logging.getLogger(__name__)

# Storage for thread IDs by user_id
thread_storage: Dict[str, str] = {}


class AssistantModel:
    """OpenAI Assistant API wrapper."""

    def __init__(self, assistant_id: str) -> None:
        """Creates a wrapper for the OpenAI Assistant API."""
        self.assistant_id = assistant_id
        self.user_id = None  # Will be set before ask is called
        
        # Configure the OpenAI client
        self.client = AsyncOpenAI(
            api_key=config.openai.api_key,
            base_url=config.openai.url if config.openai.url != "https://api.openai.com/v1" else None
        )

    async def ask(self, prompt: str, question: str, history: list[tuple[str, str]]) -> str:
        """Asks the assistant a question and returns an answer."""
        if not self.user_id:
            raise ValueError("User ID must be set before asking a question")
        
        # Get or create a thread for this user
        thread_id = await self._get_or_create_thread()
        
        # Check if there's any active run and cancel it before proceeding
        await self._cancel_active_runs(thread_id)
        
        # Get initial message count to know which messages are new
        initial_messages = await self.client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=1
        )
        initial_message_id = initial_messages.data[0].id if initial_messages.data else None
        
        # Add the user's message to the thread
        logger.debug(f"> assistant request: assistant_id={self.assistant_id}, thread_id={thread_id}")
        
        # Include the system prompt in the first message if no history
        # Otherwise just send the user's question
        message_content = question
        if not history and prompt:
            message_content = f"{prompt}\n\n{question}"
        
        # Add the user message to the thread with retry logic
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Add the user message to the thread
                message = await self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=message_content
                )
                
                # Create a run to process the thread with the assistant
                run = await self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=self.assistant_id,
                )
                
                # Wait for the run to complete
                run = await self._wait_for_run(thread_id, run.id)
                
                # If we get here, the run completed successfully
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
                if attempt == max_attempts - 1:  # Last attempt
                    raise  # Re-raise the exception if all attempts failed
                # Otherwise wait a bit and try again
                await asyncio.sleep(1)
                # Make sure any active runs are cancelled before retrying
                await self._cancel_active_runs(thread_id)
        
        # Get messages after the user's message was added
        messages = await self.client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",  # Newest first
            limit=5  # Get several messages to ensure we find the assistant's response
        )
        
        # Find the assistant's response - look through the most recent messages
        assistant_message = None
        for msg in messages.data:
            # Skip the message we just added or any previous messages
            if initial_message_id and msg.id == initial_message_id:
                break
                
            if msg.role == "assistant":
                assistant_message = msg
                break
        
        # If we didn't find an assistant message, raise an error
        if not assistant_message:
            # Try again with a larger limit
            messages = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=10
            )
            
            # Log all messages for debugging
            logger.debug(f"All messages in thread: {[(msg.id, msg.role) for msg in messages.data]}")
            
            # The run might have completed but the message isn't available yet
            # Wait a short time and try again
            logger.info("Assistant message not found, waiting and retrying...")
            await asyncio.sleep(2)
            
            messages = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=10
            )
            
            for msg in messages.data:
                if msg.role == "assistant":
                    assistant_message = msg
                    break
                    
            if not assistant_message:
                # If we still can't find it, return a friendly error message
                return "Я получил Ваш запрос, но сейчас испытываю технические трудности с формированием ответа. Пожалуйста, повторите запрос через несколько секунд."
        
        # Extract the text content from the message
        answer = ""
        for content in assistant_message.content:
            if content.type == "text":
                answer += content.text.value
        
        if not answer:
            raise ValueError("Received an empty answer from the assistant")
        
        logger.debug(f"< assistant response: thread_id={thread_id}, run_id={run.id}")
        
        return answer.strip()
    
    async def _get_or_create_thread(self) -> str:
        """Gets an existing thread or creates a new one for the user."""
        if self.user_id in thread_storage:
            return thread_storage[self.user_id]
        
        # Create a new thread
        thread = await self.client.beta.threads.create()
        thread_storage[self.user_id] = thread.id
        logger.debug(f"Created new thread {thread.id} for user {self.user_id}")
        
        return thread.id
    
    async def _wait_for_run(self, thread_id: str, run_id: str) -> dict:
        """Waits for the run to complete and returns the final run object."""
        MAX_WAIT_TIME = 240  # Увеличиваем таймаут до 4 минут
        POLLING_INTERVAL = 1.0  # Увеличиваем интервал проверки до 1 секунды
        
        start_time = time.time()
        elapsed_time = 0
        
        # Poll for run status until it's completed or failed
        while elapsed_time < MAX_WAIT_TIME:
            try:
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status == "completed":
                    # Даем API немного времени для окончательной обработки сообщений
                    await asyncio.sleep(1)
                    return run
                
                if run.status == "cancelled":
                    # If the run was cancelled, we'll return a default completed run
                    # This prevents errors when we cancel runs ourselves
                    logger.info(f"Run {run_id} was cancelled, treating as completed")
                    # Даем API немного времени для обработки
                    await asyncio.sleep(1)
                    return run
                
                if run.status in ["failed", "expired"]:
                    error_msg = getattr(run, "last_error", {})
                    error_details = f"{error_msg.get('code', 'unknown')}: {error_msg.get('message', 'unknown error')}" if error_msg else "unknown"
                    raise ValueError(f"Run failed with status: {run.status}, error: {error_details}")
                
                # Wait before polling again
                await asyncio.sleep(POLLING_INTERVAL)
                elapsed_time = time.time() - start_time
                
            except Exception as e:
                if "not_found" in str(e).lower():
                    # If the run is not found, it might have been deleted or cancelled
                    logger.warning(f"Run {run_id} not found, might have been cancelled")
                    # Create a dummy run object to return
                    return type('obj', (object,), {'id': run_id, 'status': 'completed'})
                else:
                    # For other errors, re-raise
                    raise
        
        # If we get here, we've timed out
        try:
            await self.client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run_id
            )
        except Exception as e:
            logger.warning(f"Failed to cancel timed out run: {str(e)}")
            
        raise TimeoutError(f"Run timed out after {MAX_WAIT_TIME} seconds")
    
    async def _cancel_active_runs(self, thread_id: str) -> None:
        """Check for any active runs in the thread and cancel them."""
        try:
            # List all active runs
            runs = await self.client.beta.threads.runs.list(thread_id=thread_id)
            
            # Cancel any active runs
            for run in runs.data:
                if run.status in ["queued", "in_progress", "requires_action"]:
                    logger.debug(f"Cancelling active run {run.id} in thread {thread_id}")
                    try:
                        await self.client.beta.threads.runs.cancel(
                            thread_id=thread_id,
                            run_id=run.id
                        )
                    except Exception as e:
                        # If cancellation fails, log it but continue
                        logger.warning(f"Failed to cancel run {run.id}: {str(e)}")
                        
            # Small delay to ensure cancellation is processed
            await asyncio.sleep(0.5)
            
        except Exception as e:
            # If listing runs fails, log it but continue
            logger.warning(f"Failed to list runs for thread {thread_id}: {str(e)}") 