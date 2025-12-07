"""
Configuration loader
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required sections
    required_sections = ['search', 'platforms', 'agents', 'report']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")
    
    return config


def get_enabled_platforms(config: Dict[str, Any]) -> list:
    """
    Get list of enabled platforms from config
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of enabled platform names
    """
    return [
        platform 
        for platform, settings in config['platforms'].items() 
        if settings.get('enabled', False)
    ]


def get_enabled_agents(config: Dict[str, Any]) -> list:
    """
    Get list of enabled agents from config
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of enabled agent names
    """
    return [
        agent 
        for agent, settings in config['agents'].items() 
        if settings.get('enabled', True)  # Default to enabled
    ]
