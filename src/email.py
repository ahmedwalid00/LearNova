# Compatibility shim for email imports
# This ensures that imports from 'src.email' work by re-exporting from email_config

from src.email_config import create_message, mail

__all__ = ["create_message", "mail"]