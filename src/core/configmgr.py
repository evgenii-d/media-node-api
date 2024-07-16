"""Configuration Manager."""
import configparser
from pathlib import Path
from contextlib import suppress
from typing import Any, TypeAlias

ConfigDict: TypeAlias = dict[str, dict[str, Any]]


class ConfigManager:
    """
    A class to manage configuration files 
    using the `configparser` module.
    """

    def __init__(self, path: Path, default_data: ConfigDict = None) -> None:
        """Initialize a new ConfigManager instance.

        Args:
            path (Path): Path to the configuration file.

            default_data (ConfigDict):
                If provided and the file at `path` doesn't exist,
                a new config file will be created with this data.
                Defaults to None.
        """
        self.path = path
        self.config = configparser.ConfigParser()
        self.config.optionxform = lambda option: option
        if not path.exists() and default_data:
            self.save(default_data)

    def _convert_value(self, value: str) -> int | float | bool | str:
        """
        Attempt to convert a string value 
        to an appropriate data type.
        """
        with suppress(ValueError):
            return int(value)

        with suppress(ValueError):
            return float(value)

        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        return value

    def _filter_default_dict(self, default: dict, section: dict) -> dict:
        """ 
        Filters section to exclude values from 'DEFAULT' section.
        Creates a new dictionary with key-value pairs from the section 
        that are not defined in 'DEFAULT' or have different values.
        """
        result = {}
        for key in section.keys():
            if key not in default.keys():
                result[key] = section[key]
                continue
            if (key in default.keys()
                    and default[key] != section[key]):
                result[key] = section[key]
        return result

    def _write_config(self) -> None:
        with open(self.path, "w", encoding="utf-8") as file:
            self.config.write(file)

    def _section_exists(self, section_name: str) -> bool:
        return (section_name in self.config.sections()
                + [self.config.default_section])

    def load_section(self, section: str = "DEFAULT",
                     convert_values: bool = False) -> dict[str, Any]:
        """Load a specific section from the configuration file.

        Args:
            section (str, optional): 
                The name of the section to load. Defaults to "DEFAULT".

            convert_values (bool, optional): 
                Whether to convert string values to other data types.
                Defaults to False.

        Returns:
            dict[str, Any]: 
                A dictionary containing the section's values.
        """
        self.config.read(self.path)
        if not self._section_exists(section):
            return {}

        if section == self.config.default_section:
            result = self.config.defaults()
        else:
            result = self._filter_default_dict(
                self.config.defaults(), dict(self.config[section]))

        if convert_values:
            return {
                k: self._convert_value(v)
                for k, v in result.items()
            }
        return result

    def load(self, convert_values: bool = False) -> ConfigDict:
        """Load the entire configuration file.

        Args:
            convert_values (bool, optional): 
                Whether to convert string values to other data types.
                Defaults to False.
        Returns:
            ConfigDict: 
                A dictionary containing all sections and their values.
        """
        self.config.read(self.path)
        result: ConfigDict = {}

        for section in self.config.items():
            section_name: str
            section_name, section_values = section

            if section_name == self.config.default_section:
                result[section_name] = dict(section_values)
            else:
                result[section_name] = self._filter_default_dict(
                    self.config.defaults(), dict(section_values))

        if convert_values:
            for _, section in result.items():
                section: dict
                for k, v in section.items():
                    section[k] = self._convert_value(v)
        return result

    def save_section(self, data: dict, section: str = "DEFAULT",
                     overwrite: bool = False) -> None:
        """Save a section to the configuration file.

        Args:
            data (dict): A dictionary containing the section's data.

            section (str, optional): 
                The name of the section to save. Defaults to "DEFAULT".

            overwrite (bool, optional): 
                Whether to overwrite an existing section. 
                Defaults to False.
        """
        self.config.read(self.path)
        if not self._section_exists(section):
            self.config.add_section(section)

        if overwrite:
            self.config[section] = data
        else:
            if section == self.config.default_section:
                self.config[section] = dict(self.config[section]) | data
            else:
                self.config[section] = self._filter_default_dict(
                    self.config.defaults(), data)

        self._write_config()

    def save(self, data: ConfigDict, overwrite_sections: bool = False,
             overwrite_config: bool = False) -> None:
        """ 
        Save multiple sections 
        or the entire configuration to the file.

        Args:
            data (ConfigDict): 
                A dictionary containing sections and their data.

            overwrite_sections (bool, optional): 
                Whether to overwrite existing sections. 
                Defaults to False.

            overwrite_config (bool, optional): 
                Whether to overwrite the entire configuration file.
                Defaults to False.
        """
        if overwrite_config:
            for section, values in data.items():
                self.config[section] = values
            self._write_config()
            return

        self.config.read(self.path)
        for section, values in data.items():
            if not self._section_exists(section):
                self.config.add_section(section)

            if overwrite_sections:
                self.config[section] = values
                continue

            if section == self.config.default_section:
                self.config["DEFAULT"] = self.config.defaults() | values
            else:
                tmp_dict = self._filter_default_dict(
                    self.config.defaults(), self.config[section])
                self.config[section] = tmp_dict | values

        self._write_config()
