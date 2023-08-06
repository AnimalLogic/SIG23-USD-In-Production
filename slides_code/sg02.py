# Copyright 2023 Animal Logic Pty Limited.
from pxr import Tf, Usd
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
prim = stage.DefinePrim("/hello", "Sphere")
attr = prim.GetAttribute("radius")
attr.Set(2)
