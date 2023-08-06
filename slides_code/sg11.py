from pxr import Tf, Usd, Sdf, Kind
from itertools import count
# Copyright 2023 Animal Logic Pty Limited.
from AL.usd import transaction

stage = Usd.Stage.CreateInMemory()


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

objects_counter = count(start=1)
transaction_counter = count(start=1)

objectsChangedNotice = Tf.Notice.Register(Usd.Notice.ObjectsChanged, _onObjectsChanged, stage)
transactionNotice = Tf.Notice.Register(transaction.OpenNotice, _onTransactionClose, stage)
transactionNotice = Tf.Notice.Register(transaction.CloseNotice, _onTransactionClose, stage)


prim_paths = {
    "/new/prim1": "external1.usd",
    "/new/prim2": "external2.usd",
    "/new/prim3": "external3.usd",
}

target_layer = stage.GetEditTarget().GetLayer()

with transaction.ScopedTransaction(stage, target_layer):
    with Sdf.ChangeBlock():
        for path in prim_paths:
            stage.OverridePrim(path)

    with Sdf.ChangeBlock():
        for path, reference in prim_paths.items():
            prim = stage.GetPrimAtPath(path)
            prim.GetReferences().AddReference(reference)
            modelAPI = Usd.ModelAPI(prim)
            modelAPI.SetKind(Kind.Tokens.component)

print(target_layer.ExportToString())