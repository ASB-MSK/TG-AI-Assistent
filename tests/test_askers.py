import datetime as dt
import unittest
from unittest.mock import patch
from telegram import Chat, Message, User
from telegram.ext import CallbackContext

from bot import askers
from bot.askers import AssistantAsker, ImagineAsker, TextAsker
from bot.config import config
from tests.mocks import FakeApplication, FakeAssistant, FakeBot, FakeDalle, FakeGPT, mock_assistant_asker, mock_text_asker


class TextAskerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.ai = FakeGPT()
        mock_text_asker(self.ai)

    async def test_ask(self):
        asker = TextAsker("gpt")
        await asker.ask(
            prompt="Answer me", question="What is your name?", history=[("Hello", "Hi")]
        )
        self.assertEqual(self.ai.prompt, "Answer me")
        self.assertEqual(self.ai.question, "What is your name?")
        self.assertEqual(self.ai.history, [("Hello", "Hi")])

    async def test_reply(self):
        message, context = _create_message()
        asker = TextAsker("gpt")
        await asker.reply(message, context, answer="My name is ChatGPT.")
        self.assertEqual(context.bot.text, "My name is ChatGPT.")


class AssistantAskerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.ai = FakeAssistant()
        mock_assistant_asker(self.ai)

    async def test_ask(self):
        asker = AssistantAsker("asst_id")
        await asker.ask(
            prompt="Answer me", question="What is your name?", history=[("Hello", "Hi")]
        )
        self.assertEqual(self.ai.prompt, "Answer me")
        self.assertEqual(self.ai.question, "What is your name?")
        self.assertEqual(self.ai.history, [("Hello", "Hi")])

    async def test_reply(self):
        message, context = _create_message()
        asker = AssistantAsker("asst_id")
        await asker.reply(message, context, answer="My name is Assistant.")
        self.assertEqual(context.bot.text, "My name is Assistant.")


class ImagineAskerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.ai = FakeDalle()
        ImagineAsker.model = self.ai

    async def test_ask(self):
        asker = ImagineAsker()
        await asker.ask(prompt="answer me", question="a cat 256x256", history=[])
        self.assertEqual(self.ai.prompt, "a cat")
        self.assertEqual(self.ai.size, "256x256")

    async def test_reply(self):
        asker = ImagineAsker()
        await asker.ask(prompt="answer me", question="a cat 256x256", history=[])
        message, context = _create_message()
        await asker.reply(message, context, answer="https://image.url")
        self.assertEqual(context.bot.text, "a cat: https://image.url")

    def test_extract_size(self):
        asker = ImagineAsker()
        size = asker._extract_size(question="a cat 256x256")
        self.assertEqual(size, "256x256")
        size = asker._extract_size(question="a cat 512x512")
        self.assertEqual(size, "512x512")
        size = asker._extract_size(question="a cat 1024x1024")
        self.assertEqual(size, "1024x1024")
        size = asker._extract_size(question="a cat 256")
        self.assertEqual(size, "256x256")
        size = asker._extract_size(question="a cat 256px")
        self.assertEqual(size, "256x256")
        size = asker._extract_size(question="a cat 384")
        self.assertEqual(size, "1024x1024")

    def test_extract_caption(self):
        asker = ImagineAsker()
        caption = asker._extract_caption(question="a cat 256x256")
        self.assertEqual(caption, "a cat")
        caption = asker._extract_caption(question="a cat 512x512")
        self.assertEqual(caption, "a cat")
        caption = asker._extract_caption(question="a cat 1024x1024")
        self.assertEqual(caption, "a cat")
        caption = asker._extract_caption(question="a cat 256")
        self.assertEqual(caption, "a cat")
        caption = asker._extract_caption(question="a cat 256px")
        self.assertEqual(caption, "a cat")
        caption = asker._extract_caption(question="a cat 384")
        self.assertEqual(caption, "a cat 384")


class CreateTest(unittest.TestCase):
    def test_text_asker(self):
        with patch('bot.askers.config') as mock_config:
            mock_config.openai.assistant_id = None
            asker = askers.create(model="gpt", question="What is your name?")
            self.assertIsInstance(asker, TextAsker)

    def test_assistant_asker(self):
        with patch('bot.askers.config') as mock_config:
            mock_config.openai.assistant_id = "asst_id"
            asker = askers.create(model="gpt", question="What is your name?")
            self.assertIsInstance(asker, AssistantAsker)

    def test_imagine_asker(self):
        with patch('bot.askers.config') as mock_config:
            mock_config.openai.assistant_id = None
            asker = askers.create(model="dalle", question="/imagine a cat")
            self.assertIsInstance(asker, ImagineAsker)

        with patch('bot.askers.config') as mock_config:
            mock_config.openai.assistant_id = "asst_id"
            asker = askers.create(model="dalle", question="/imagine a cat")
            self.assertIsInstance(asker, ImagineAsker)


def _create_message() -> tuple[Message, CallbackContext]:
    bot = FakeBot("bot")
    chat = Chat(id=1, type=Chat.PRIVATE)
    chat.set_bot(bot)
    application = FakeApplication(bot)
    context = CallbackContext(application, chat_id=1, user_id=1)
    user = User(id=1, first_name="Alice", is_bot=False, username="alice")
    message = Message(
        message_id=11,
        date=dt.datetime.now(),
        chat=chat,
        from_user=user,
    )
    message.set_bot(bot)
    return message, context
