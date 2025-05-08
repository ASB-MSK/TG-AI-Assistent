# Humble AI Telegram Bot

This is a Telegram chat bot (AI assistant) that uses large language models from OpenAI-compatible providers (like [OpenAI](https://platform.openai.com/), [OpenRouter](https://openrouter.ai/docs/), [Nebius](https://docs.nebius.com/) or [Gemini](https://ai.google.dev/gemini-api/docs/openai)).

Notable features:

-   Both one-on-one and group chats.
-   Direct questions, mentions, follow-ups.
-   Access external links (articles, code, data).
-   Shortcuts (custom AI commands).
-   Custom per-chat prompts and models.
-   On-the-fly configuration.
-   Support for OpenAI Assistant API.

Read on for a detailed feature description or jump to [setup](#setup).

## Personal chats

The bot acts as your personal assistant:

> 🧑 Explain Apache Kafka to a three year old
>
> 🤖 Apache Kafka is like a big mailbox that helps different toys (computers) send messages to each other. When one toy has something to say, it puts a message in the mailbox, and other toys can take that message out and read it. This way, they can talk and share things quickly!

To allow other users to use the bot, list them in the `telegram.usernames` config property.

The bot has a terrible memory, so don't expect it to remember any chat context by default. You can, however, reply with a follow-up question (`Ctrl/Cmd + ↑`). Alternatively, use a plus sign to follow up:

> 🧑 Yesterday, all my troubles seemed so far away
>
> 🤖 It sounds like you're quoting "Yesterday" by The Beatles. It's a classic song about longing and nostalgia.
>
> 🧑 + who wrote it?
>
> 🤖 "Yesterday" was written by Paul McCartney of The Beatles.

Available commands:

-   `/retry` - retry answering the last question
-   `/help` - show help
-   `/version` - show bot info

To rephrase or add to the last question, simply edit it. The bot will then answer the updated question.

## Groups

To get an answer from the bot in a group, mention it in a reply to a question:

> 🧑 I forgot who played Ramsy in the Game of Thrones 😕<br>
> 🧑 ↳ @pokitokibot help
>
> 🤖 Ramsay Bolton in Game of Thrones was played by Iwan Rheon.

Or ask a question directly:

> 🧑 @pokitokibot Who played Ramsy in the Game of Thrones?
>
> 🤖 Iwan Rheon played Ramsay Bolton in Game of Thrones.

To make the bot reply to group members, list the group id in the `telegram.chat_ids` config property. Otherwise, the bot will ignore questions from group members unless they are listed in the `telegram.usernames` config property.

If you don't know the group id, run the `/version` bot command in a group to find it:

```
Chat information:
- id: -1001405001234
- title: My Favorite Group
- type: supergroup
...
```

## External links

If you ask "vanilla" ChatGPT about external resources, it will either hallucinate or admit that it doesn't have access to remote content:

> 🧑 What is the content of https://sqlime.org/employees.sql? Make no assumptions.
>
> 🤖 As an AI language model, I cannot access external URLs on the internet.

The bot solves the problem by fetching the remote content and feeding it to the model:

> 🧑 Name 1 major feature of the Go 1.23 release https://tip.golang.org/doc/go1.23 Be brief!
>
> 🤖 A major feature of Go 1.23 is the inclusion of the "range-over-func" experiment as a standard language feature, allowing the "range" clause in "for-range" loops to accept iterator functions.

Currently only supports text content (articles, code, data), not PDFs, images or audio.

If you _don't want_ the bot to access the URL, quote it:

> 🧑 Exact contents of "https://antonz.org/robots.txt"
>
> 🤖 I can't access external websites directly. You can check the contents of a robots.txt file by visiting the URL in your browser.

## Shortcuts

Use short commands to save time and ask the bot to do something specific with your questions. For example, ask it to proofread your writing with a `!proofread` command:

> 🧑 !proofread I can has write java programz
>
> 🤖 Revised text: "I can write Java programs."
>
> Changes made:
>
> 1. Removed "has" for grammatical correctness; "can" does not require "has."
> 2. Corrected "java" to "Java" for proper capitalization as it is a proper noun.
> 3. Changed "programz" to "programs" for correct spelling and clarity.

There are several built-in shortcuts:

-   `bugfix` fixes your code.
-   `proofread` fixes your writing.
-   `translate` translates your text into English.
-   `summarize` gives a two paragraph summary of a text.

You can add your own shortcuts. See `config.example.yml` for details.

## Per-chat settings

You can customize some settings on a per-chat basis. For example, to have one prompt for your private chat with a bot and another prompt for a group chat that you manage.

### Prompt

Set a custom prompt for the current chat with the `/prompt` command:

> 🧑 /prompt You are an evil genius. Reply with an evil laugh.

To return to the default prompt, use `/prompt reset`.

The `/prompt` command in group chats is only available to admins - users listed in the `telegram.admins` property.

### Model

Set a custom AI model for the current chat with the `/model` command:

> 🧑 /model o3-mini

To return to the default model, use `/model reset`.

The `/model` command in group chats is only available to admins - users listed in the `telegram.admins` property.

## Other useful features

The convenience of working with a bot is made up of small details. Here are some situations where it can save you time and effort.

### Forwarding

Say you received a message from a colleague or read a post on a channel and want to ask a question. Simply forward the message to the bot and answer the clarifying question it asks.

### Ask with file

To ask a question about a document, send it as a file and write the question in the caption. The bot will read the file contents and answer. Currently only supports text content (plain text, code, data), not PDFs, images or audio. Sending multiple files is also not supported.

### Reply with attachment

Sometimes the AI's reply exceeds the maximum message length set by Telegram. In this case, the bot will not fail or spam you with messages. Instead, it will send the answer as an attached markdown file.

### Edited question

To rephrase or add to the last question, edit it (`↑` shortcut). The bot will notice this and respond to the clarified question.

## Bot information

Use the `/version` command to print detailed information about the current chat, bot, and AI model:

```
Chat information:
- id: -1001405001234
- title: My Favorite Group
- type: supergroup

Bot information:
- id: 5930739038
- name: @pokitokibot
- version: 129
- usernames: 6 users
- admins: 1 users
- chat IDs: []
- access to messages: True

AI information:
- provider: api.openai.com
- model: gpt-4o-mini
- history depth: 5
- shortcuts: proofread, summarize
```

## Configuration

Use the `/config` command to change almost any setting on the fly, without restarting the bot.

-   Add or remove users and chats allowed to interact with the bot (`telegram.usernames` and `telegram.chat_ids`).
-   Adjust the AI provider (`openai.url`), API key (`openai.api_key`), model (`openai.model`), prompt (`openai.prompt`) and params (`openai.params`).
-   Add or change AI shortcuts (`shortcuts`).
-   Set up an OpenAI Assistant (`openai.assistant_id`).
-   Change any other config property.

To view a specific config property, put its name after `/config`:

```
/config telegram.usernames
/config openai.prompt
/config openai.assistant_id
```

## OpenAI Assistant API

The bot supports the OpenAI Assistant API, which allows you to use custom assistants created in the OpenAI platform. 

### Enabling Assistant API

To use an OpenAI Assistant instead of the standard chat completion:

1. Create an assistant in the [OpenAI Playground](https://platform.openai.com/assistants) or using the API
2. Get the assistant ID (it looks like `asst_abc123...`)
3. Configure the bot to use it:
   ```
   /config openai.assistant_id asst_your_assistant_id
   ```

When `openai.assistant_id` is set, the bot will automatically use the Assistant API instead of the standard Chat Completion API. Each user will get their own persistent thread, enabling the assistant to maintain context across conversations.

### Disabling Assistant API

To switch back to the standard chat completion API, clear the assistant ID:

```
/config openai.assistant_id ""
```

or

```
/config openai.assistant_id reset
```

### Benefits of using Assistant API

- Better context management through persistent threads
- Support for custom assistants with specific personalities, knowledge, or capabilities
- Access to assistant-specific features like function calling, code interpreter, etc.
- Potential for more consistent responses across multiple interactions

Note that when using the Assistant API, some settings like `openai.model` and `openai.params` are ignored as these are configured in the assistant itself.

## Message limits

Heated discussions with the bot in large groups can lead to high usage of the AI API. To avoid spending your entire budget, set message limits for groups with the `conversation.message_limit` config property.

You can limit the number of messages from a user over a period of time. For example:

-   10 messages per user per hour:

```yaml
message_limit:
    count: 10
    period: hour
```

-   1 message per user per minute:

```yaml
message_limit:
    count: 1
    period: minute
```

-   30 messages per user per day:

```yaml
message_limit:
    count: 30
    period: day
```

## Setup

1. Get your AI API key (from [OpenAI](https://openai.com/api/) or other provider)

2. Get your Telegram bot token from [@BotFather](https://t.me/BotFather)

3. Clone the repo to the server:

```bash
git clone https://github.com/nalgeon/pokitoki.git
```

4. Copy `config.example.yml` to `config.yml` and specify your tokens there. Add yourself to the `telegram.usernames` property, otherwise the bot will be available to everyone.

5. Start the bot:

```bash
docker compose up --build --detach
```

To stop the bot:

```bash
docker compose stop
```

To update the bot to a new version:

```bash
docker compose down
git pull
docker compose up --build --detach
```

For older Docker distributions, use `docker-compose` instead of `docker compose`.

## Development setup

Prepare the environment:

```
python3 -m venv env
. env/bin/activate
pip install -r requirements.txt
```

Prepare the config and data directory:

```
cp config.example.yml config.yml
mkdir ./data
```

Set tokens and other settings in `config.yml`.

Run tests:

```
python -m unittest discover
```

Start the bot:

```
python -m bot.bot
```

## Contributing

Contributions are welcome. For anything other than bugfixes, please first open an issue to discuss what you want to change.

Use [Black](https://black.readthedocs.io/en/stable/) for code formatting. Be sure to add or update tests as appropriate.

## Changelog

For feature history, see [releases](https://github.com/nalgeon/pokitoki/releases).

## Credits

Originally based on [chatgpt_telegram_bot](https://github.com/karfly/chatgpt_telegram_bot), although the projects have diverged quite a bit.

# Pokitoki Bot

Telegram бот для общения с OpenAI API.

## Возможности

- Общение с OpenAI API (GPT-4o-mini)
- Генерация изображений с помощью DALL-E 3
- Настройка параметров бота через команду `/config`
- Ограничение доступа по списку пользователей и групп
- Ограничение количества сообщений от пользователей
- Настройка глубины памяти (количество сообщений, которые бот помнит)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/pokitoki.git
cd pokitoki
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл конфигурации `config.yml` на основе `config.example.yml`:
```bash
cp config.example.yml config.yml
```

4. Отредактируйте `config.yml`, указав:
   - Токен Telegram бота
   - API ключ OpenAI
   - Список разрешенных пользователей и групп
   - Другие настройки

## Запуск

```bash
python -m bot.bot
```

## Настройка через команду /config

Бот поддерживает настройку параметров через команду `/config`. Вот основные возможности:

### Просмотр текущих настроек

```
/config property
```

Например:
```
/config openai.prompt
/config conversation.depth
/config imagine.enabled
```

### Изменение настроек

```
/config property value
```

Например:
```
/config openai.prompt You are an AI assistant
/config conversation.depth 5
/config imagine.enabled users_only
```

### Основные настройки

- **Глубина памяти (conversation.depth)**
  - Устанавливает количество сообщений, которые бот помнит
  - Значение 0 отключает память (бот забывает предыдущие сообщения)
  - Пример: `/config conversation.depth 5`

- **Генерация изображений (imagine.enabled)**
  - `none` - генерация изображений отключена для всех
  - `users_only` - генерация изображений доступна только пользователям из списка telegram.usernames
  - `users_and_groups` - генерация изображений доступна как для пользователей, так и для групп
  - Пример: `/config imagine.enabled users_only`

- **Режим Assistant API (openai.assistant_id)**
  - Просмотр текущего ID ассистента: `/config openai.assistant_id`
  - Отключение режима Assistant API: `/config openai.assistant_id reset`

### Другие настройки

- Добавление пользователя в список разрешенных: `/config telegram.usernames +username`
- Удаление пользователя из списка: `/config telegram.usernames -username`
- Аналогично для групп: `/config telegram.chat_ids +group_id`

## Лицензия

MIT
