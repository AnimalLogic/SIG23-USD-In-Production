# Copyright 2023 Animal Logic Pty Limited.
from pxr import Tf, Usd, Sdf, Kind
from itertools import count
counter = count(start=1)


def _onObjectsChanged(notice, sender):
    notice_no = next(counter)
    changed = notice.GetChangedInfoOnlyPaths()
    resynced = notice.GetResyncedPaths()
    print(f"{notice_no}: Changed: {changed}")
    print(f"{notice_no}: Resynced: {resynced}")


stage = Usd.Stage.CreateInMemory()

notice = Tf.Notice.Register(Usd.Notice.ObjectsChanged, _onObjectsChanged, stage)

prim_paths = {
    "/new/prim1": "external1.usd",
    "/new/prim2": "external2.usd",
    "/new/prim3": "external3.usd",
}

target_layer = stage.GetEditTarget().GetLayer()
with Sdf.ChangeBlock():
    prefixes = set()
    for path in prim_paths:
        spec = Sdf.CreatePrimInLayer(target_layer, path)
        prefixes.update(spec.path.GetPrefixes())
    for prefix in prefixes:
        target_layer.GetPrimAtPath(prefix).specifier = Sdf.SpecifierDef

with Sdf.ChangeBlock():
    for path, reference in prim_paths.items():
        prim = stage.GetPrimAtPath(path)
        prim.GetReferences().AddReference(reference)
        modelAPI = Usd.ModelAPI(prim)
        modelAPI.SetKind(Kind.Tokens.component)

print(target_layer.ExportToString())
