from pathlib import Path

class SafetyChecker:
    def __init__(self, config):
        self.config = config
        self.allowed_extensions = set(config.get("allowed_extensions", []))
        self.safe_root = Path(config.get("safe_root", "C:/Users/Velix/Documents"))

    def is_safe_file(self, file_path):
        path = Path(file_path)
        
        # Rule: Must exist
        if not path.exists():
            return False

        # Rule: Allowed extension
        if path.suffix.lower() not in self.allowed_extensions:
            return False

        # Rule: Not a system file (simple check)
        if path.name.startswith('.') or path.name.startswith('~'):
            return False

        return True

    def is_safe_action(self, source, destination):
        # Rule: Destination must be within safe_root
        dest_path = Path(destination)
        try:
            # resolve() handles symlinks and relative paths
            # is_relative_to ensures it's inside the root
            if not dest_path.resolve().is_relative_to(self.safe_root.resolve()):
                return False
        except ValueError:
            return False

        return True
