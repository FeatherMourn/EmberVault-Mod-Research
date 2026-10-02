"""Reference occupancy vectors from the existing ArchitectVoxel algorithms."""
import json
from architect_voxel import box, hollow_square, sphere, ellipsoid, filled_cylinder, hollow_cylinder, ring

cases = {
    "box_solid": box((4, 4, 4), True),
    "box_hollow": box((4, 4, 4), False, 1),
    "box_flat_hollow": hollow_square((8, 1, 8), 1),
    "sphere_solid": sphere((4, 4, 4)),
    "sphere_hollow": ellipsoid((8, 8, 8), (4, 4, 4), True, 1),
    "cylinder_solid": filled_cylinder((4, 4, 4)),
    "cylinder_hollow": hollow_cylinder((8, 4, 8), thickness=1.5),
    "cylinder_x": filled_cylinder((5, 6, 8), axis="x"),
    "cylinder_z": filled_cylinder((5, 6, 8), axis="z"),
    "ring": ring((8, 1, 8), thickness=1.5),
}
print(json.dumps({name: {"hex": shape.payload.hex(), "count": shape.occupied_count,
                         "dimensions": list(shape.dimensions)} for name, shape in cases.items()}))
