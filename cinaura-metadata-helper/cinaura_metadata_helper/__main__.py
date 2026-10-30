"""Allow running the package as: python -m cinaura_metadata_helper"""

import sys
from .cli import main

sys.exit(main())

