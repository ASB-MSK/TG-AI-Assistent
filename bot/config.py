"""Bot configuration parameters."""

import os
from typing import Any, Optional
import yaml
import dataclasses
from dataclasses import dataclass


@dataclass
class Telegram:
    token: str
    usernames: list
    admins: list
    chat_ids: list


@dataclass
class OpenAI:
    url: str
    api_key: str
    model: str
    image_model: str
    window: int
    prompt: str
    params: dict
    assistant_id: Optional[str]

    default_url = "https://api.openai.com/v1"
    default_model = "gpt-4o-mini"
    default_image_model = "dall-e-3"
    default_window = 128000
    default_prompt = "You are an AI assistant."
    default_params = {
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    def __init__(
        self,
        url: str,
        api_key: str,
        model: str,
        image_model: str,
        window: int,
        prompt: str,
        params: dict,
        assistant_id: Optional[str] = None,
    ) -> None:
        self.url = url or self.default_url
        self.api_key = api_key
        self.model = model or self.default_model
        self.image_model = image_model or self.default_image_model
        self.window = window or self.default_window
        self.prompt = prompt or self.default_prompt
        self.params = self.default_params.copy()
        self.params.update(params)
        self.assistant_id = assistant_id


@dataclass
class RateLimit:
    count: int
    period: str

    allowed_periods = ("minute", "hour", "day")
    default_period = "hour"

    def __init__(self, count: int = 0, period: str = default_period) -> None:
        self.count = count
        if period not in self.allowed_periods:
            period = self.default_period
        self.period = period

    def __bool__(self) -> bool:
        return self.count > 0


@dataclass
class Conversation:
    depth: int
    message_limit: RateLimit

    default_depth = 3

    def __init__(self, depth: int, message_limit: dict) -> None:
        self.depth = depth or self.default_depth
        self.message_limit = RateLimit(**message_limit)


@dataclass
class Imagine:
    enabled: str

    def __init__(self, enabled: str) -> None:
        self.enabled = enabled if enabled in ("none", "users_only", "users_and_groups") else "none"


class Config:
    """Config properties."""

    # Config schema version. Increments for backward-incompatible changes.
    schema_version = 5
    # Bot version.
    version = 227

    def __init__(self, filename: str, src: dict) -> None:
        # Config filename.
        self.filename = filename

        # Telegram settings.
        self.telegram = Telegram(
            token=src["telegram"]["token"],
            usernames=src["telegram"].get("usernames") or [],
            admins=src["telegram"].get("admins") or [],
            chat_ids=src["telegram"].get("chat_ids") or [],
        )

        # OpenAI settings.
        self.openai = OpenAI(
            url=src["openai"].get("url"),
            api_key=src["openai"]["api_key"],
            model=src["openai"].get("model"),
            image_model=src["openai"].get("image_model"),
            window=src["openai"].get("window"),
            prompt=src["openai"].get("prompt"),
            params=src["openai"].get("params") or {},
            assistant_id=src["openai"].get("assistant_id"),
        )

        # Conversation settings.
        self.conversation = Conversation(
            depth=src["conversation"].get("depth"),
            message_limit=src["conversation"].get("message_limit") or {},
        )

        # Image generation settings.
        self.imagine = Imagine(enabled=src["imagine"].get("enabled") or "")

        # Where to store the chat context file.
        self.persistence_path = src.get("persistence_path") or "./data/persistence.pkl"

        # Custom AI commands (additional prompts).
        self.shortcuts = src.get("shortcuts") or {}

    def as_dict(self) -> dict:
        """Converts the config into a dictionary."""
        return {
            "schema_version": self.schema_version,
            "telegram": dataclasses.asdict(self.telegram),
            "openai": dataclasses.asdict(self.openai),
            "conversation": dataclasses.asdict(self.conversation),
            "imagine": dataclasses.asdict(self.imagine),
            "persistence_path": self.persistence_path,
            "shortcuts": self.shortcuts,
        }


class ConfigEditor:
    """
    Config properties editor.
    Gets/sets config properties by their 'path',
    e.g. 'openai.params.temperature' or 'conversation.depth'.
    """

    # These properties cannot be changed at all.
    readonly = [
        "schema_version",
        "version",
        "filename",
    ]
    # Changes made to these properties take effect immediately.
    immediate = [
        "telegram",
        "openai",
        "conversation",
        "imagine",
        "shortcuts",
    ]
    # Changes made to these properties take effect after a restart.
    delayed = [
        "telegram.token",
        "persistence_path",
    ]
    # All editable properties.
    editable = immediate + delayed
    # All known properties.
    known = readonly + immediate + delayed

    def __init__(self, config: Config) -> None:
        self.config = config

    def get_value(self, property: str) -> Any:
        """Returns a config property value."""
        names = property.split(".")
        if names[0] not in self.known:
            raise ValueError(f"No such property: {property}")

        obj = self.config
        for name in names[:-1]:
            if not hasattr(obj, name):
                raise ValueError(f"No such property: {property}")
            obj = getattr(obj, name)

        name = names[-1]
        if isinstance(obj, dict):
            return obj.get(name)

        if isinstance(obj, object):
            if not hasattr(obj, name):
                raise ValueError(f"No such property: {property}")
            val = getattr(obj, name)
            if dataclasses.is_dataclass(val):
                return dataclasses.asdict(val)
            return val

        raise ValueError(f"Failed to get property: {property}")

    def set_value(self, property: str, value: str) -> tuple[bool, bool, Any]:
        """
        Changes a config property value.
        Returns a tuple `(has_changed, is_immediate, new_val)`
          - `has_changed`  = True if the value has actually changed, False otherwise.
          - `is_immediate` = True if the change takes effect immediately, False otherwise.
          - `new_val`        is the new value
        """
        try:
            val = yaml.safe_load(value)
        except Exception:
            raise ValueError(f"Invalid value: {value}")

        old_val = self.get_value(property)
        if val == old_val:
            return False, False, old_val

        # Special handling for resetting properties
        # Check this case before type checking
        special_reset = False
        if property == "openai.assistant_id" and value.lower() == "reset":
            val = None  # Set to None instead of "reset"
            special_reset = True
            
        # Special handling for imagine.enabled
        if property == "imagine.enabled":
            if value not in ["none", "users_only", "users_and_groups"]:
                raise ValueError(
                    f"Invalid value for imagine.enabled: {value}. "
                    f"Valid options are: none, users_only, users_and_groups"
                )

        if isinstance(old_val, list) and isinstance(val, str):
            # allow changing list properties by adding or removing individual items
            # e.g. /config telegram.usernames +bob
            # or   /config telegram.usernames -alice
            if val[0] == "+":
                item = yaml.safe_load(val[1:])
                val = old_val.copy()
                val.append(item)
            elif val[0] == "-":
                item = yaml.safe_load(val[1:])
                val = old_val.copy()
                val.remove(item)

        # Skip type checking for special cases like resetting assistant_id
        if not special_reset:
            old_cls = old_val.__class__
            val_cls = val.__class__
            if old_val is not None and old_cls != val_cls:
                raise ValueError(
                    f"Property {property} should be of type {old_cls.__name__}, not {val_cls.__name__}"
                )

        if not (isinstance(val, (list, str, int, float, bool)) or val is None):
            raise ValueError(f"Cannot set composite value for property: {property}")

        names = property.split(".")
        if names[0] not in self.editable:
            raise ValueError(f"Property {property} is not editable")

        is_immediate = property not in self.delayed

        obj = self.config
        for name in names[:-1]:
            obj = getattr(obj, name, val)

        name = names[-1]
        if isinstance(obj, dict):
            obj[name] = val
            return True, is_immediate, val

        if isinstance(obj, object):
            if not hasattr(obj, name):
                raise ValueError(f"No such property: {property}")
            setattr(obj, name, val)
            return True, is_immediate, val

        raise ValueError(f"Failed to set property: {property}")

    def save(self) -> None:
        """Saves the config to disk."""
        data = self.config.as_dict()
        with open(self.config.filename, "w") as file:
            yaml.safe_dump(data, file, indent=4, allow_unicode=True)


class SchemaMigrator:
    """Migrates the configuration data dictionary according to the schema version."""

    @classmethod
    def migrate(cls, data: dict) -> tuple[dict, bool]:
        """Migrates the configuration to the latest schema version."""
        has_changed = False
        if data.get("schema_version", 1) == 1:
            data = cls._migrate_v1(data)
            has_changed = True
        if data["schema_version"] == 2:
            data = cls._migrate_v2(data)
            has_changed = True
        if data["schema_version"] == 3:
            data = cls._migrate_v3(data)
            has_changed = True
        if data["schema_version"] == 4:
            data = cls._migrate_v4(data)
            has_changed = True
        return data, has_changed

    @classmethod
    def _migrate_v1(cls, old: dict) -> dict:
        data = {
            "schema_version": 2,
            "telegram": None,
            "openai": None,
            "max_history_depth": old.get("max_history_depth"),
            "imagine": old.get("imagine"),
            "persistence_path": old.get("persistence_path"),
            "shortcuts": old.get("shortcuts"),
        }
        data["telegram"] = {
            "token": old["telegram_token"],
            "usernames": old.get("telegram_usernames"),
            "chat_ids": old.get("telegram_chat_ids"),
        }
        data["openai"] = {
            "api_key": old["openai_api_key"],
            "model": old.get("openai_model"),
        }
        return data

    @classmethod
    def _migrate_v2(cls, old: dict) -> dict:
        data = {
            "schema_version": 3,
            "telegram": old["telegram"],
            "openai": old["openai"],
            "imagine": old.get("imagine"),
            "persistence_path": old.get("persistence_path"),
            "shortcuts": old.get("shortcuts"),
        }
        data["conversation"] = {"depth": old.get("max_history_depth") or Conversation.default_depth}
        return data

    @classmethod
    def _migrate_v3(cls, old: dict) -> dict:
        data = {
            "schema_version": 4,
            "telegram": old["telegram"],
            "openai": old["openai"],
            "conversation": old["conversation"],
            "persistence_path": old.get("persistence_path"),
            "shortcuts": old.get("shortcuts"),
        }
        imagine_enabled = old.get("imagine")
        imagine_enabled = True if imagine_enabled is None else imagine_enabled
        data["imagine"] = {"enabled": "users_only" if imagine_enabled else "none"}
        return data
        
    @classmethod
    def _migrate_v4(cls, old: dict) -> dict:
        data = {
            "schema_version": 5,
            "telegram": old["telegram"],
            "openai": old["openai"].copy(),
            "conversation": old["conversation"],
            "imagine": old["imagine"],
            "persistence_path": old.get("persistence_path"),
            "shortcuts": old.get("shortcuts"),
        }
        # Add the new assistant_id parameter
        data["openai"]["assistant_id"] = None
        return data


def load(filename) -> dict:
    """Loads the configuration data dictionary from a file."""
    with open(filename, "r") as f:
        data = yaml.safe_load(f)

    data, has_changed = SchemaMigrator.migrate(data)
    if has_changed:
        with open(filename, "w") as f:
            yaml.safe_dump(data, f, indent=4, allow_unicode=True)
    return data


filename = os.getenv("CONFIG", "config.yml")
_config = load(filename)
config = Config(filename, _config)
