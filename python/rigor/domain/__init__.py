import pkgutil
import os.path

kModules = [package[1] for package in pkgutil.iter_modules([os.path.dirname(__file__), ]) if package[1] != 'domain']
