# Copyright 2023 Animal Logic Pty Limited.
from pxr import Tf, Usd, Sdf, Kind

stage = Usd.Stage.CreateInMemory()


from itertools import count
objects_counter = count(start=1)
transaction_counter = count(start=1)

from AL.usd import transaction


def _onTransactionClose(notice, sender):
    notice_no = next(transaction_counter)
    changed = notice.GetChangedInfoOnlyPaths()
    resynced = notice.GetResyncedPaths()
    print(f"TR {notice_no}: Changed: {changed}")
    print(f"TR {notice_no}: Resynced: {resynced}")


def _onObjectsChanged(notice, sender):
    notice_no = next(objects_counter)
    if transaction.TransactionManager.InProgress(sender):
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
transactionNotice = Tf.Notice.Register(transaction.OpenNotice, _onTransactionClose, stage)
transactionNotice = Tf.Notice.Register(transaction.CloseNotice, _onTransactionClose, stage)

from AL.usd import undo

target_layer = stage.GetEditTarget().GetLayer()
undo.UsdUndoManager.trackLayerStates(stage, target_layer)


print(f"Block open - Total prims: {len(list(stage.TraverseAll()))}")
with undo.UsdUndoBlock(stage):
    with transaction.ScopedTransaction(stage, target_layer):
        with Sdf.ChangeBlock():
            for path in prim_paths:
                stage.OverridePrim(path)

        with Sdf.ChangeBlock():
            for path, reference in prim_paths.items():
                prim = stage.GetPrimAtPath(path)
                prim.SetSpecifier(Sdf.SpecifierDef)
                prim.GetReferences().AddReference(reference)
                modelAPI = Usd.ModelAPI(prim)
                modelAPI.SetKind(Kind.Tokens.component)


print(f"Block closed - Total prims: {len(list(stage.TraverseAll()))}")

undo.UsdUndoManager.undo(stage)
print(f"Undoing - Total prims: {len(list(stage.TraverseAll()))}")

undo.UsdUndoManager.redo(stage)
print(f"Redoing - Total prims: {len(list(stage.TraverseAll()))}")
print(target_layer.ExportToString())
