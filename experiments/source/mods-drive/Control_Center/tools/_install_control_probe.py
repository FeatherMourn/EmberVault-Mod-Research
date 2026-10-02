from pathlib import Path
from core.local_mods import LocalModService

service = LocalModService(Path('.'))
package = service.inspect(Path('research/probes/bed_clone_injection_1076226'))
print(service.install(package, Path(r'H:\SteamLibrary\steamapps\common\Enshrouded'), allow_research=True, replace=True))
