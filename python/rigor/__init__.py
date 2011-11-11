""" Important application-level initialization """

from rigor.config import config
import sys

sys.path.append(config.get('sibyl', 'python_root'))
