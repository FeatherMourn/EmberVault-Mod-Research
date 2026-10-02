# Visual variant manual validation runbook

Use this runbook only with a disposable game copy containing the externally
published RenderModel variant. Do not install the research probe into the
stable live profile.

## Capture sequence

1. Start the disposable client and capture the main menu as a startup record.
2. Choose **Play**, then **Private**, and load the disposable test world.
3. Open the Carpenter menu and navigate to the relevant furniture category.
4. Capture a screenshot showing the custom catalog tile and its selected item
   information. Record whether the icon/model differs from the donor.
5. Place one copy of the item in the world and capture the complete placed
   object in view beside a donor object for comparison.
6. Save the world, exit to desktop, relaunch the disposable client, and load
   the same world again.
7. Capture the object after relaunch and record whether it remains present and
   whether its appearance is unchanged.

## Evidence requirements

Record the target build, disposable directory, item ID, replacement model GUID,
and exact screenshot paths. A world-loaded screenshot without the custom object
does not count. A catalog screenshot without the selected custom item does not
count. Do not promote the capability unless catalog, placed-object, and fresh
launch persistence evidence are all present and the probe has been removed.

## Current boundary

Archive publication and client startup are verified. Catalog appearance,
placed-object appearance, and fresh-launch persistence remain unverified until
this sequence is completed.
