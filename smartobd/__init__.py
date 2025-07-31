"""
SmartOBD - Predictive Vehicle Maintenance Powered by OBD-II & AI

A comprehensive vehicle monitoring and predictive maintenance system that connects
to your car's OBD-II port, analyzes real-time diagnostics, and uses machine learning
to forecast when your vehicle needs servicing.
"""

__version__ = "1.0.0"
__author__ = "SmartOBD Team"
__email__ = "support@smartobd.com"
__description__ = "Predictive Vehicle Maintenance Powered by OBD-II & AI"

from .core.app import SmartOBDApp
from .core.config import Config

__all__ = [
    "SmartOBDApp",
    "Config",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
] 