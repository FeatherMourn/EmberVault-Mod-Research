"""
Procedural Shape & Geometry Generator for Voxel Blueprints.
Calculates 3D coordinates for architectural shapes:
- Rings & Circles (Midpoint circle algorithm)
- Cylinders & Towers (Extruded concentric circles)
- Domes & Spheres (Calculated voxel hemispheres)
- Spiral Staircases (Helical vertical stairs)
- Hollow Rectangular Enclosures / Foundation Slabs
- Satisfactory-style Line Zoop & Wall Plane Grids
"""

import math
from typing import List, Dict, Tuple, Any


def generate_circle_ring(radius: int, thickness: int = 1, y: int = 0) -> List[Tuple[int, int, int]]:
    """
    Generates a horizontal ring of voxel coordinates using Euclidean distance.
    Returns unique sorted (x, y, z) coordinates centered at (0, y, 0).
    """
    coords = set()
    r_inner = max(0, radius - thickness)
    r_outer = radius

    for x in range(-r_outer, r_outer + 1):
        for z in range(-r_outer, r_outer + 1):
            dist = math.sqrt(x * x + z * z)
            if r_inner <= dist <= (r_outer + 0.5):
                coords.add((x, y, z))

    return sorted(list(coords))


def generate_cylinder(radius: int, height: int, thickness: int = 1) -> List[Tuple[int, int, int]]:
    """
    Generates a vertical hollow cylinder/tower across a height range [0 .. height-1].
    """
    coords = []
    base_ring = generate_circle_ring(radius, thickness, y=0)
    for y in range(height):
        for x, _, z in base_ring:
            coords.append((x, y, z))
    return coords


def generate_dome(radius: int, thickness: int = 1) -> List[Tuple[int, int, int]]:
    """
    Generates a half-sphere dome cap starting at y=0 up to y=radius.
    """
    coords = set()
    r_inner = max(0, radius - thickness)
    r_outer = radius

    for x in range(-r_outer, r_outer + 1):
        for y in range(0, r_outer + 1):
            for z in range(-r_outer, r_outer + 1):
                dist = math.sqrt(x * x + y * y + z * z)
                if r_inner <= dist <= (r_outer + 0.5):
                    coords.add((x, y, z))

    return sorted(list(coords))


def generate_spiral_staircase(radius: int, height: int, turns: float = 1.0, step_width: int = 2) -> List[Tuple[int, int, int]]:
    """
    Generates a spiral staircase wrapping around a central column.
    """
    coords = set()
    total_steps = height
    if total_steps <= 0:
        return []

    angle_step = (turns * 2.0 * math.pi) / total_steps

    for y in range(total_steps):
        theta = y * angle_step
        # Center pillar
        coords.add((0, y, 0))
        # Radius arm for stair tread
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        for r in range(1, radius + 1):
            for w in range(-step_width // 2, (step_width + 1) // 2):
                # Perpendicular offset for tread width
                px = int(round(r * cos_t - w * sin_t))
                pz = int(round(r * sin_t + w * cos_t))
                coords.add((px, y, pz))

    return sorted(list(coords))


def generate_box_perimeter(width: int, length: int, height: int, thickness: int = 1) -> List[Tuple[int, int, int]]:
    """
    Generates a hollow rectangular room or wall perimeter.
    """
    coords = set()
    half_w = width // 2
    half_l = length // 2

    for y in range(height):
        for x in range(-half_w, half_w + 1):
            for z in range(-half_l, half_l + 1):
                is_x_edge = abs(x) >= (half_w - thickness + 1)
                is_z_edge = abs(z) >= (half_l - thickness + 1)
                if is_x_edge or is_z_edge:
                    coords.add((x, y, z))

    return sorted(list(coords))


def generate_zoop_line(start: Tuple[int, int, int], end: Tuple[int, int, int], step_size: int = 4) -> List[Tuple[int, int, int]]:
    """
    Generates a Satisfactory-style straight zoop line of piece anchors between start and end.
    Snaps to the dominant axis and step_size.
    """
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]

    # Find dominant axis
    abs_x, abs_y, abs_z = abs(dx), abs(dy), abs(dz)
    max_dist = max(abs_x, abs_y, abs_z)
    if max_dist == 0:
        return [start]

    count = max(1, int(round(max_dist / step_size)))
    coords = []

    if abs_x >= abs_y and abs_x >= abs_z:
        sign = 1 if dx >= 0 else -1
        for i in range(count + 1):
            coords.append((start[0] + i * step_size * sign, start[1], start[2]))
    elif abs_y >= abs_x and abs_y >= abs_z:
        sign = 1 if dy >= 0 else -1
        for i in range(count + 1):
            coords.append((start[0], start[1] + i * step_size * sign, start[2]))
    else:
        sign = 1 if dz >= 0 else -1
        for i in range(count + 1):
            coords.append((start[0], start[1], start[2] + i * step_size * sign))

    return coords


def generate_beveled_trim(length: int, thickness: int = 2) -> List[Tuple[int, int, int]]:
    """
    Generates a 45-degree beveled cornice/trim edge for architectural detailing.
    """
    coords = set()
    for z in range(length):
        for step in range(thickness):
            for x in range(step, thickness):
                coords.add((x, step, z))
    return sorted(list(coords))


def generate_roman_arch(span: int, height: int, depth: int = 2) -> List[Tuple[int, int, int]]:
    """
    Generates a Roman semicircular archway frame for doors and window headers.
    """
    coords = set()
    radius = span / 2.0
    half_span = int(span // 2)

    for z in range(depth):
        # Vertical arch jambs / pillars
        for y in range(height):
            coords.add((-half_span, y, z))
            coords.add((half_span, y, z))

        # Semicircular arch curve
        for x_step in range(-half_span, half_span + 1):
            rel_x = float(x_step)
            if abs(rel_x) <= radius:
                arch_y = height + int(round(math.sqrt(max(0.0, radius**2 - rel_x**2))))
                coords.add((x_step, arch_y, z))

    return sorted(list(coords))


def generate_gothic_arch(span: int, height: int, depth: int = 2) -> List[Tuple[int, int, int]]:
    """
    Generates a pointed Gothic lancet arch using dual intersecting circle arcs.
    """
    coords = set()
    half_span = int(span // 2)
    radius = float(span) * 0.85  # Gothic lancet radius

    for z in range(depth):
        for y in range(height):
            coords.add((-half_span, y, z))
            coords.add((half_span, y, z))

        for x_step in range(-half_span, half_span + 1):
            x = float(x_step)
            # Left arc centered at -half_span, right arc centered at +half_span
            if x <= 0:
                dx = x - float(half_span * 0.4)
            else:
                dx = x + float(half_span * 0.4)
            rad_sq = radius**2 - dx**2
            if rad_sq >= 0:
                arch_y = height + int(round(math.sqrt(rad_sq) - (radius - half_span * 1.2)))
                coords.add((x_step, max(height, arch_y), z))

    return sorted(list(coords))


def generate_ground_leveler(width: int, length: int, thickness: int = 1) -> List[Tuple[int, int, int]]:
    """
    Generates a perfectly flat foundation slab / excavation bed to level terrain.
    """
    coords = []
    half_w = width // 2
    half_l = length // 2
    for x in range(-half_w, half_w + 1):
        for z in range(-half_l, half_l + 1):
            for y in range(thickness):
                coords.append((x, -y, z))
def generate_zoop_plane(start: Tuple[int, int, int], end: Tuple[int, int, int], step_size: int = 4) -> List[Tuple[int, int, int]]:
    """
    Generates a 2D Zoop Plane (Floor / Wall grid) spanning the bounding rectangle between start and end.
    """
    x1, y1, z1 = start
    x2, y2, z2 = end

    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    min_z, max_z = min(z1, z2), max(z1, z2)

    dx = max_x - min_x
    dy = max_y - min_y
    dz = max_z - min_z

    coords = []
    # If flat horizontal plane (Floor/Ceiling Zoop)
    if dy <= step_size:
        for x in range(min_x, max_x + 1, max(1, step_size)):
            for z in range(min_z, max_z + 1, max(1, step_size)):
                coords.append((x, min_y, z))
    # If X-Y vertical wall plane
    elif dz <= step_size:
        for x in range(min_x, max_x + 1, max(1, step_size)):
            for y in range(min_y, max_y + 1, max(1, step_size)):
                coords.append((x, y, min_z))
    # If Y-Z vertical wall plane
    else:
        for z in range(min_z, max_z + 1, max(1, step_size)):
            for y in range(min_y, max_y + 1, max(1, step_size)):
                coords.append((min_x, y, z))

    return coords if coords else [start]


def generate_zoop_stairs(start: Tuple[int, int, int], end: Tuple[int, int, int], step_size: int = 2) -> List[Tuple[int, int, int]]:
    """
    Generates a 45-degree continuous diagonal staircase zoop between start and end elevation.
    """
    x1, y1, z1 = start
    x2, y2, z2 = end

    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1

    height = abs(dy)
    if height == 0:
        return generate_zoop_line(start, end, step_size)

    sign_y = 1 if dy >= 0 else -1
    sign_x = 1 if dx >= 0 else -1
    sign_z = 1 if dz >= 0 else -1

    horiz_dist = max(abs(dx), abs(dz))
    count = max(1, height)

    coords = []
    for step in range(count + 1):
        curr_y = y1 + step * sign_y
        if abs(dx) >= abs(dz):
            curr_x = x1 + int(round(step * (abs(dx) / count))) * sign_x
            curr_z = z1
        else:
            curr_x = x1
            curr_z = z1 + int(round(step * (abs(dz) / count))) * sign_z

        coords.append((curr_x, curr_y, curr_z))
        # Add tread width
        if abs(dx) >= abs(dz):
            coords.append((curr_x, curr_y, curr_z + 1))
            coords.append((curr_x, curr_y, curr_z - 1))
        else:
            coords.append((curr_x + 1, curr_y, curr_z))
            coords.append((curr_x - 1, curr_y, curr_z))

    return sorted(list(set(coords)))


def generate_conical_turret_roof(base_radius: int, height: int, thickness: int = 1) -> List[Tuple[int, int, int]]:
    """
    Generates a conical roof / witch-hat spire tapering from base_radius up to a tip.
    """
    coords = set()
    for y in range(height + 1):
        # Linear taper from base_radius to 0
        r_current = max(0, int(round(base_radius * (1.0 - y / max(1, height)))))
        ring = generate_circle_ring(r_current, thickness=thickness, y=y)
        coords.update(ring)
    return sorted(list(coords))


def generate_flying_buttress(span: int, height: int, pier_width: int = 2) -> List[Tuple[int, int, int]]:
    """
    Generates a Gothic flying buttress with supportive outer pier and curved arch flyer.
    """
    coords = set()
    # 1. Outer ground pier
    for y in range(height):
        for x in range(span - pier_width, span + 1):
            coords.add((x, y, 0))
            coords.add((x, y, 1))

    # 2. Arched flyer spanning from wall (x=0) to outer pier (x=span)
    for x in range(0, span):
        t = x / max(1, span)
        # Parabolic flyer arch
        arch_y = int(round(height * 0.5 + (height * 0.5) * (t**1.4)))
        coords.add((x, arch_y, 0))
        coords.add((x, arch_y, 1))
        coords.add((x, arch_y + 1, 0))

    return sorted(list(coords))


def generate_onion_dome(base_radius: int, height: int) -> List[Tuple[int, int, int]]:
    """
    Generates an Eastern European / Byzantine pointed onion dome with a swollen midsection and spire.
    """
    coords = set()
    for y in range(height + 1):
        ny = y / max(1, height)
        # Swell factor: expands to 1.3x at 30% height, then tapers to 0 at spire
        if ny < 0.35:
            r = base_radius * (1.0 + 0.35 * math.sin(ny / 0.35 * (math.pi / 2)))
        else:
            r = (base_radius * 1.35) * (1.0 - ((ny - 0.35) / 0.65)**1.8)

        radius_int = max(0, int(round(r)))
        ring = generate_circle_ring(radius_int, thickness=1, y=y)
        coords.update(ring)

    return sorted(list(coords))


def generate_machicolations(wall_length: int, projection: int = 2) -> List[Tuple[int, int, int]]:
    """
    Generates defensive corbelled machicolations along a castle parapet with murder holes.
    """
    coords = set()
    for z in range(wall_length):
        is_bracket = (z % 3 == 0)
        for x in range(projection + 1):
            if is_bracket:
                # Solid corbel bracket support
                coords.add((x, 0, z))
                coords.add((x, 1, z))
            else:
                # Cantilevered floor leaving 1-voxel murder hole opening
                if x > 1:
                    coords.add((x, 1, z))

        # Outer battlement parapet
        coords.add((projection, 2, z))
        if z % 2 == 0:
            coords.add((projection, 3, z))  # Merlon

    return sorted(list(coords))


def generate_aqueduct_arcade(total_length: int, pier_height: int = 12, span_width: int = 8) -> List[Tuple[int, int, int]]:
    """
    Generates a multi-bay Roman aqueduct arcade with top water conduit.
    """
    coords = set()
    bays = max(1, total_length // span_width)

    for b in range(bays):
        base_x = b * span_width
        # Pier columns
        for y in range(pier_height):
            for z in range(2):
                coords.add((base_x, y, z))
                coords.add((base_x + 1, y, z))

        # Semicircular arch spanning base_x to base_x + span_width
        r = span_width / 2.0
        for step in range(span_width):
            x = base_x + step
            rel = (step - r) / r
            if abs(rel) <= 1.0:
                arch_y = pier_height + int(round(r * math.sqrt(max(0.0, 1.0 - rel**2))))
                for z in range(2):
                    coords.add((x, arch_y, z))

    # Continuous upper roadway / water conduit
    deck_y = pier_height + int(span_width / 2) + 1
    for x in range(total_length):
        coords.add((x, deck_y, 0))
        coords.add((x, deck_y, 1))
        # Sidewalls of water channel
        coords.add((x, deck_y + 1, 0))
        coords.add((x, deck_y + 1, 1))

    return sorted(list(coords))


def import_obj_to_voxels(obj_text: str, grid_size: int = 32) -> List[Tuple[int, int, int]]:
    """
    Reads wavefront .obj vertex geometry and converts into normalized 3D microvoxels.
    """
    vertices = []
    for line in obj_text.splitlines():
        line = line.strip()
        if line.startswith("v "):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    vx, vy, vz = float(parts[1]), float(parts[2]), float(parts[3])
                    vertices.append((vx, vy, vz))
                except ValueError:
                    pass

    if not vertices:
        return []

    # Calculate bounding box
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)
    min_z = min(v[2] for v in vertices)
    max_z = max(v[2] for v in vertices)

    span = max(max_x - min_x, max_y - min_y, max_z - min_z, 0.0001)
    scale = (grid_size - 1) / span

    voxel_set = set()
    for vx, vy, vz in vertices:
        gx = int(round((vx - min_x) * scale))
        gy = int(round((vy - min_y) * scale))
        gz = int(round((vz - min_z) * scale))
        voxel_set.add((gx, gy, gz))

    return sorted(list(voxel_set))


def generate_crenellated_rampart(
    length: int = 16,
    base_height: int = 2,
    merlon_height: int = 2,
    merlon_width: int = 2,
    embrasure_width: int = 2,
    thickness: int = 1
) -> List[Tuple[int, int, int]]:
    """
    Generates castle ramparts / battlements with alternating merlons and embrasures.
    """
    coords = set()
    period = merlon_width + embrasure_width

    for x in range(length):
        # Continuous base walkway / breastwork
        for y in range(base_height):
            for z in range(thickness):
                coords.add((x, y, z))

        # Alternating crenels / merlons on top
        if (x % period) < merlon_width:
            for y in range(base_height, base_height + merlon_height):
                for z in range(thickness):
                    coords.add((x, y, z))

    return sorted(list(coords))


def generate_balcony_parapet(
    width: int = 8,
    depth: int = 4,
    railing_height: int = 2
) -> List[Tuple[int, int, int]]:
    """
    Generates a cantilevered balcony floor slab with perimeter safety railings and corner posts.
    """
    coords = set()
    # Floor slab (1 voxel thick at y=0)
    for x in range(width):
        for z in range(depth):
            coords.add((x, 0, z))

    # Perimeter railings (front, left, right edges)
    for y in range(1, railing_height + 1):
        # Front edge (z = depth - 1)
        for x in range(width):
            if (x % 2 == 0) or (y == railing_height): # Balusters + top rail
                coords.add((x, y, depth - 1))
        # Left edge (x = 0)
        for z in range(depth):
            if (z % 2 == 0) or (y == railing_height):
                coords.add((0, y, z))
        # Right edge (x = width - 1)
        for z in range(depth):
            if (z % 2 == 0) or (y == railing_height):
                coords.add((width - 1, y, z))

    return sorted(list(coords))


def generate_groin_vault(
    span: int = 10,
    height: int = 8,
    depth: int = 10
) -> List[Tuple[int, int, int]]:
    """
    Generates a classic intersecting 4-corner Romanesque/Gothic groin vault ceiling.
    """
    coords = set()
    r_x = span / 2.0
    r_z = depth / 2.0

    for x in range(span + 1):
        rel_x = (x - r_x) / r_x
        h_x = height * math.sqrt(max(0.0, 1.0 - rel_x * rel_x)) if abs(rel_x) <= 1.0 else 0

        for z in range(depth + 1):
            rel_z = (z - r_z) / r_z
            h_z = height * math.sqrt(max(0.0, 1.0 - rel_z * rel_z)) if abs(rel_z) <= 1.0 else 0

            # The groin vault ceiling is the minimum height of the two intersecting barrel vaults
            vault_y = int(round(min(h_x, h_z)))
            if vault_y >= 0:
                coords.add((x, vault_y, z))

    return sorted(list(coords))


def generate_chimney_flue(
    height: int = 12,
    width: int = 4,
    depth: int = 4,
    thickness: int = 1
) -> List[Tuple[int, int, int]]:
    """
    Generates a vertical hollow stone chimney with an arched hearth opening and top cap.
    """
    coords = set()
    for y in range(height):
        for x in range(width):
            for z in range(depth):
                is_outer = (x < thickness or x >= width - thickness or z < thickness or z >= depth - thickness)
                # Hearth opening at front base (y < 4, front face)
                is_hearth_opening = (y < 4 and z == 0 and 0 < x < width - 1)
                if is_outer and not is_hearth_opening:
                    coords.add((x, y, z))

    # Chimney crown / cap
    for x in range(-1, width + 1):
        for z in range(-1, depth + 1):
            if x == -1 or x == width or z == -1 or z == depth:
                coords.add((x, height - 1, z))

    return sorted(list(coords))


def export_blueprint_json(
    name: str,
    shape_type: str,
    coords: List[Tuple[int, int, int]],
    voxel_material_id: int = 67,
    multi_material: bool = False,
    foundation_mat_id: int = 67,  # Stone
    wall_mat_id: int = 42,        # Wood
    roof_mat_id: int = 89         # Castle Slate
) -> Dict[str, Any]:
    """
    Formats the procedural coordinate collection into standard blueprint JSON format.
    Supports Multi-Material Layer Theming (Option 2): Stone Foundation + Wood Walls + Slate Roof.
    """
    min_x = min((c[0] for c in coords), default=0)
    max_x = max((c[0] for c in coords), default=0)
    min_y = min((c[1] for c in coords), default=0)
    max_y = max((c[1] for c in coords), default=0)
    min_z = min((c[2] for c in coords), default=0)
    max_z = max((c[2] for c in coords), default=0)

    total_h = max(1, max_y - min_y + 1)
    base_split = min_y + max(1, int(total_h * 0.25))
    roof_split = min_y + max(2, int(total_h * 0.75))

    coord_list = []
    for c in coords:
        y = c[1]
        if multi_material:
            if y <= base_split:
                m_id = foundation_mat_id
            elif y <= roof_split:
                m_id = wall_mat_id
            else:
                m_id = roof_mat_id
        else:
            m_id = voxel_material_id

        coord_list.append({"x": c[0], "y": c[1], "z": c[2], "material_id": m_id})

    return {
        "blueprint_version": "1.1.0",
        "name": name,
        "shape_type": shape_type,
        "default_material_id": voxel_material_id,
        "multi_material_theming": multi_material,
        "total_voxels": len(coords),
        "bounds": {
            "size_x": max_x - min_x + 1,
            "size_y": max_y - min_y + 1,
            "size_z": max_z - min_z + 1,
        },
        "coordinates": coord_list
    }
