# Copyright 2023 Animal Logic Pty Limited.
from pxr import Tf, Usd, Sdf, Kind
from itertools import count

# from AL.usd import transaction  # not shipped with Maya (but can be built from source)
from maya import standalone
from maya import cmds
import mayaUsd.lib as mayaUsdLib
standalone.initialize()
cmds.loadPlugin('mayaUsdPlugin')
# end of maya setup

stage = Usd.Stage.CreateInMemory()

objects_counter = count(start=1)


def _onObjectsChanged(notice, sender):
    notice_no = next(objects_counter)
    changed = notice.GetChangedInfoOnlyPaths()
    resynced = notice.GetResyncedPaths()
    print(f"N {notice_no}: Changed: {changed}")
    print(f"N {notice_no}: Resynced: {resynced}")


r1 = Usd.Stage.CreateInMemory()
r2 = Usd.Stage.CreateInMemory()
r3 = Usd.Stage.CreateInMemory()
for each in r1, r2, r3:
    each.SetDefaultPrim(each.DefinePrim("/world"))

prim_paths = {
    "/new/prim1": r1.GetRootLayer().identifier,
    "/new/prim2": r2.GetRootLayer().identifier,
    "/new/prim3": r3.GetRootLayer().identifier,
}

objectsChangedNotice = Tf.Notice.Register(Usd.Notice.ObjectsChanged, _onObjectsChanged, stage)


target_layer = stage.GetEditTarget().GetLayer()
mayaUsdLib.UsdUndoManager.trackLayerStates(target_layer)

with mayaUsdLib.UsdUndoBlock():
    print(f"Block open - Total prims: {len(list(stage.TraverseAll()))}")
    with Sdf.ChangeBlock():
        for path in prim_paths:
            stage.OverridePrim(path)

    with Sdf.ChangeBlock():
        for path, reference in prim_paths.items():
            prim = stage.GetPrimAtPath(path)
            prim.GetReferences().AddReference(reference)
            modelAPI = Usd.ModelAPI(prim)
            modelAPI.SetKind(Kind.Tokens.component)


print(f"Block closed - Total prims: {len(list(stage.TraverseAll()))}")

cmds.undo()  # woops, undo
print(f"Undoing - Total prims: {len(list(stage.TraverseAll()))}")

cmds.redo()  # nevermind, redo
print(f"Redoing - Total prims: {len(list(stage.TraverseAll()))}")
print(target_layer.ExportToString())
