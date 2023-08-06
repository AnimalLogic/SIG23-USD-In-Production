# Copyright 2023 Animal Logic Pty Limited.
# Maya ships undo behavior via the mayaUSD plugin and cmds, so initialise maya to access it
from maya import standalone
standalone.initialize()
from maya import cmds
cmds.loadPlugin('mayaUsdPlugin')
import mayaUsd.lib as mayaUsdLib
# Maya setup finished

from pxr import Tf, Sdf, Usd, Kind
from pxr.Usdviewq.plugin import PluginContainer
from PySide2 import QtWidgets

import datetime
from pathlib import Path
from itertools import count

objects_counter = count(start=1)
undo_block = None
objectsChangedNotice = None


def _onObjectsChanged(notice, sender):
    notice_no = next(objects_counter)
    print(f"Internal notice: {notice_no}")


def activate(usdviewApi):
    global undo_block
    global objectsChangedNotice
    global transactionNotice
    stage = usdviewApi.stage
    objectsChangedNotice = Tf.Notice.Register(Usd.Notice.ObjectsChanged, _onObjectsChanged, stage)
    target_layer = stage.GetEditTarget().GetLayer()
    mayaUsdLib.UsdUndoManager.trackLayerStates(target_layer)


def _undo(usdviewApi):
    print("Undoing!")
    cmds.undo()


def _redo(usdviewApi):
    print("Redoing!")
    cmds.redo()


def addEntities(usdviewApi):
    # https://stackoverflow.com/questions/38252419/how-to-get-qfiledialog-to-select-and-return-multiple-folders
    file_dialog = QtWidgets.QFileDialog()
    selection_mode = QtWidgets.QAbstractItemView.ContiguousSelection
    file_dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
    file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
    file_view = file_dialog.findChild(QtWidgets.QListView, 'listView')
    # to make it possible to select multiple directories:
    if file_view:
        file_view.setSelectionMode(selection_mode)
    f_tree_view = file_dialog.findChild(QtWidgets.QTreeView)
    if f_tree_view:
        f_tree_view.setSelectionMode(selection_mode)
    file_dialog.exec()
    result = file_dialog.selectedFiles()

    def _iter_prims_to_reference(directories):
        for path in directories:
            usd_file = next(Path(path).glob("*.usda"), None)
            if not usd_file:
                print(f"no file under {path}")
                continue
            name = usd_file.stem
            yield name, str(usd_file)

    prims_to_reference = _iter_prims_to_reference(result)
    root = usdviewApi.stage.GetDefaultPrim()
    start = datetime.datetime.now()
    with mayaUsdLib.UsdUndoBlock():
        prims = _reference_prims(root, prims_to_reference)

    end = datetime.datetime.now()
    message = f"Time to bring {len(prims)} prims: {end - start}"
    QtWidgets.QMessageBox.information(None, "Finished",message)
    print(message)


def _reference_prims(root, prims_to_reference):
    stage = root.GetStage()
    root_path = root.GetPath()
    by_path = {}
    change_block = Sdf.ChangeBlock()
    with change_block:
        for name, reference in prims_to_reference:
            path = root_path.AppendChild(name)
            stage.OverridePrim(path)
            by_path[path] = reference

    prims = list()
    with change_block:
        for path, reference in by_path.items():
            prim = stage.GetPrimAtPath(path)
            prim.GetReferences().AddReference(reference)
            modelAPI = Usd.ModelAPI(prim)
            modelAPI.SetKind(Kind.Tokens.component)
            prims.append(prim)
    return prims


class EditPlugin(PluginContainer):

    def registerPlugins(self, plugRegistry, usdviewApi):
        self._add_entities_with_block = plugRegistry.registerCommandPlugin(
            "EditPlugin.add_entities",
            "Add Assets",
            addEntities)

        self._activate = plugRegistry.registerCommandPlugin(
            "EditPlugin.activate",
            "Activate Undo / Redo",
            activate)

        self._undo = plugRegistry.registerCommandPlugin(
            "EditPlugin.undo",
            "Undo",
            _undo)

        self._redo = plugRegistry.registerCommandPlugin(
            "EditPlugin.redo",
            "Redo",
            _redo)

    def configureView(self, plugRegistry, plugUIBuilder):

        tutMenu = plugUIBuilder.findOrCreateMenu("Edit Example")
        tutMenu.addSeparator()
        tutMenu.addItem(self._add_entities_with_block)
        tutMenu.addSeparator()
        tutMenu.addItem(self._activate)
        tutMenu.addItem(self._undo)
        tutMenu.addItem(self._redo)


Tf.Type.Define(EditPlugin)
