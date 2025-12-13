import hashlib
import json
import logging
from typing import Dict, Optional
from pathlib import Path

from src.etl.exceptions import ETLStateError

logger = logging.getLogger(__name__)

class ETLState:
    """ Manage states (hashes) of files to incremental processing """

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, str]:
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Fatal error in ETLState {e}")
                raise ETLStateError(f"ETLState failed: {e}") from e
        return {}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_hash(self, key: str) -> Optional[str]:
        return self.state.get(key)

    def update_hash(self, key: str, new_hash: str):
        self.state[key] = new_hash

    @staticmethod
    def compute_content_hash(content: bytes) -> str:
        """Generate unique hash MD5 for content."""
        return hashlib.md5(content).hexdigest()