from .engine import Selection, copy_selection, transform_blueprint
from construction_sdk.models import Coordinate, Piece, Transform


def main() -> None:
    selection = Selection(Coordinate(10, 20, 30), Coordinate(11, 20, 30))
    blueprint = copy_selection("example", [Piece(Coordinate(10, 20, 30), "wall", "stone")], selection)
    rotated = transform_blueprint(blueprint, Transform(rotation=90))
    print({"pieces": len(rotated.pieces), "bounds": rotated.bounds()})


if __name__ == "__main__":
    main()
