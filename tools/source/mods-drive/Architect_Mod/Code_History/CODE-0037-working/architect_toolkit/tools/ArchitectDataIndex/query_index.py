#!/usr/bin/env python3
import argparse,json,sqlite3
from pathlib import Path

def rows(db,sql,args):return [dict(r) for r in db.execute(sql,args).fetchall()]
def query(db,command,value):
    if command=="item":return rows(db,"SELECT i.*,r.guid FROM items i LEFT JOIN resources r ON r.id=i.resource_id WHERE i.item_id=?",(int(value),))
    if command=="item-name":return rows(db,"SELECT i.*,r.guid FROM items i LEFT JOIN resources r ON r.id=i.resource_id WHERE i.debug_name LIKE ? COLLATE NOCASE ORDER BY i.debug_name,i.item_id LIMIT 100",(f"%{value}%",))
    if command=="material-id":
        result=rows(db,"SELECT i.*,r.guid FROM items i LEFT JOIN resources r ON r.id=i.resource_id WHERE i.place_voxel_material_id=?",(int(value),))
        result.extend(rows(db,"SELECT t.*,r.guid FROM terrain_configs t LEFT JOIN resources r ON r.id=t.resource_id WHERE t.material_id=?",(int(value),)))
        return result
    table={"template":"templates","impact":"impact_programs"}[command]
    return rows(db,f"SELECT x.*,r.guid,r.debug_name FROM {table} x JOIN resources r ON r.id=x.resource_id WHERE r.guid=? COLLATE NOCASE",(value,))
def main():
    root=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument("command",choices=("item","item-name","material-id","template","impact"));p.add_argument("value");p.add_argument("--database",type=Path,default=root/"data"/"architect_game_data_1076226.sqlite");p.add_argument("--json",action="store_true");a=p.parse_args()
    db=sqlite3.connect(a.database);db.row_factory=sqlite3.Row; result=query(db,a.command,a.value);db.close()
    if a.json:print(json.dumps(result,indent=2))
    elif not result:print("No matching locally indexed records.")
    else:
        for row in result:print(" | ".join(f"{k}={v}" for k,v in row.items() if v is not None))
if __name__=="__main__":main()
