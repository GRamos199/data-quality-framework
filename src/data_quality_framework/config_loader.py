"""
Configuration loader for validation rules
"""

import yaml
import json
from typing import Dict, Any, List
from pathlib import Path
from .exceptions import ConfigError


class ConfigLoader:
    """Loads and manages configuration files for validators"""

    @staticmethod
    def load_yaml(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                if config is None:
                    raise ConfigError(f"Configuration file {config_path} is empty")
                return config
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML configuration: {e}")

    @staticmethod
    def load_json(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to JSON configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Error parsing JSON configuration: {e}")

    @staticmethod
    def validate_config_structure(config: Dict[str, Any]) -> bool:
        """
        Validate that configuration has required structure.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid, raises ConfigError otherwise
        """
        required_keys = ["dataset", "layer", "rules"]

        for key in required_keys:
            if key not in config:
                raise ConfigError(
                    f"Configuration missing required key: {key}"
                )

        if not isinstance(config.get("rules"), list):
            raise ConfigError("Configuration 'rules' must be a list")

        return True

    @staticmethod
    def merge_configs(base_config: Dict, override_config: Dict) -> Dict:
        """
        Merge two configuration dictionaries (override_config takes precedence).

        Args:
            base_config: Base configuration
            override_config: Configuration to merge in

        Returns:
            Merged configuration
        """
        result = base_config.copy()
        result.update(override_config)
        return result
