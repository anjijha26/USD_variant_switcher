from PySide2 import QtWidgets, QtCore
from pxr import Usd, Tf
import hou

class VariantSwitcher(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(VariantSwitcher, self).__init__(parent)

        main = QtWidgets.QVBoxLayout(self)

        file_row = QtWidgets.QHBoxLayout()
        self.file_path = QtWidgets.QLineEdit()
        self.file_path.setPlaceholderText("Path to USD file…")
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.clicked.connect(self.browse_usd)
        file_row.addWidget(self.file_path)
        file_row.addWidget(browse_btn)
        main.addLayout(file_row)

        load_button = QtWidgets.QPushButton("Load USD")
        load_button.clicked.connect(self.load_usd)
        main.addWidget(load_button)

        self.prim_dropdown = QtWidgets.QComboBox()
        self.prim_dropdown.addItem("-- Select Prim --")
        main.addWidget(self.prim_dropdown)

        self.variantset_dropdown = QtWidgets.QComboBox()
        self.variantset_dropdown.addItem("-- Select Variant Set --")
        main.addWidget(self.variantset_dropdown)

        self.variant_dropdown = QtWidgets.QComboBox()
        self.variant_dropdown.addItem("-- Select Variant --")
        main.addWidget(self.variant_dropdown)


        apply_button = QtWidgets.QPushButton("Apply Variant")
        apply_button.clicked.connect(self.apply_variant)
        main.addWidget(apply_button)

        self.clear_button = QtWidgets.QPushButton("Clear Variants")
        self.clear_button.clicked.connect(self.clear_variants)
        main.addWidget(self.clear_button)

        self.ref_node = None

        # connect dropdown changes (only once)
        self.prim_dropdown.currentIndexChanged.connect(self.update_variantsets)
        self.variantset_dropdown.currentIndexChanged.connect(self.update_variants)

    def browse_usd(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select USD File", "", "USD Files (*.usd *.usda *.usdc);;All Files (*)"
        )
        if path:
            self.file_path.setText(path)

    def load_usd(self):
        usd_path = self.file_path.text().strip()
        if not usd_path:
            hou.ui.displayMessage("Please choose a USD file.")
            return

        stage_lop = hou.node("/stage")
        if stage_lop is None:
            stage_lop = hou.node("/").createNode("lopnet", "stage")
        if self.ref_node is None or hou.node(self.ref_node.path()) is None:
            self.ref_node = stage_lop.createNode("reference", "loaded_usd")

        self.ref_node.parm("filepath1").set(usd_path)
        try:
            stage = self.ref_node.stage()  # cooks node and returns Usd.Stage
        except Exception as e:
            hou.ui.displayMessage("Failed to load USD:\n{}".format(e))
            return

        # Scan for prims that actually have variant sets
        self.prim_dropdown.blockSignals(True)
        self.variantset_dropdown.blockSignals(True)
        self.variant_dropdown.blockSignals(True)

        self.prim_dropdown.clear()
        self.variantset_dropdown.clear()
        self.variant_dropdown.clear()

        try:
            for prim in stage.Traverse():
                vsets = prim.GetVariantSets()
                if vsets.GetNames():  # has at least one variant set
                    self.prim_dropdown.addItem(prim.GetPath().pathString)
        except Exception as e:
            hou.ui.displayMessage("Error scanning prims:\n{}".format(e))
            return
        finally:
            self.prim_dropdown.blockSignals(False)
            self.variantset_dropdown.blockSignals(False)
            self.variant_dropdown.blockSignals(False)

        if self.prim_dropdown.count() == 0:
            hou.ui.displayMessage("No prims with variant sets found in this USD.")
        else:
            self.update_variantsets()

    def update_variantsets(self):
        if self.ref_node is None or hou.node(self.ref_node.path()) is None:
            return
        prim_path = self.prim_dropdown.currentText()
        if not prim_path:
            return

        stage = self.ref_node.stage()
        prim = stage.GetPrimAtPath(prim_path)
        vsets = prim.GetVariantSets()

        self.variantset_dropdown.blockSignals(True)
        self.variant_dropdown.blockSignals(True)

        self.variantset_dropdown.clear()
        self.variant_dropdown.clear()

        for vname in vsets.GetNames():
            self.variantset_dropdown.addItem(vname)

        self.variantset_dropdown.blockSignals(False)
        self.variant_dropdown.blockSignals(False)

        if self.variantset_dropdown.count() > 0:
            self.update_variants()

    def update_variants(self):
        if self.ref_node is None or hou.node(self.ref_node.path()) is None:
            return
        prim_path = self.prim_dropdown.currentText()
        vset_name = self.variantset_dropdown.currentText()
        if not prim_path or not vset_name:
            return

        stage = self.ref_node.stage()
        prim = stage.GetPrimAtPath(prim_path)
        vset = prim.GetVariantSets().GetVariantSet(vset_name)

        self.variant_dropdown.clear()
        try:
            self.variant_dropdown.addItems(vset.GetVariantNames())
        except Exception as e:
            hou.ui.displayMessage("Failed to read variants for set '{}':\n{}".format(vset_name, e))

    def apply_variant(self):

        prim_path = self.prim_dropdown.currentText()
        vset_name = self.variantset_dropdown.currentText()
        variant_name = self.variant_dropdown.currentText()

        if not (prim_path and vset_name and variant_name):
            hou.ui.displayMessage("Please select a prim, variant set, and variant option.")
            return

        stage_lop = hou.node("/stage")
        if stage_lop is None:
            stage_lop = hou.node("/").createNode("lopnet", "stage")

        ref_node = stage_lop.node("loaded_usd")
        if ref_node is None:
            ref_node = stage_lop.createNode("reference", "loaded_usd")
            ref_node.parm("filepath1").set(self.current_usd_path)

        for n in stage_lop.children():
            if n.type().name() == "setvariant":
                try:
                    if (n.parm("primpattern1").eval() == prim_path and
                            n.parm("variantset1").eval() == vset_name and
                            n.parm("variantname1").eval() == variant_name):
                        n.setDisplayFlag(True)
                        hou.ui.displayMessage("Switched to existing node: {}".format(n.name()))
                        return
                except:
                    pass

        last_node = None
        for n in stage_lop.children():
            if n.isDisplayFlagSet():
                last_node = n
                break
        if last_node is None:
            last_node = ref_node

        unique_name = "variant_applier_" + variant_name.replace(" ", "_")
        setvar_node = stage_lop.createNode("setvariant", unique_name)
        setvar_node.setInput(0, last_node)

        setvar_node.parm("primpattern1").set(prim_path)
        setvar_node.parm("variantset1").set(vset_name)
        setvar_node.parm("variantname1").set(variant_name)

        setvar_node.setDisplayFlag(True)

        hou.ui.displayMessage("Applied {} on {} [{}]".format(
            variant_name, prim_path, vset_name
        ))

    def clear_variants(self):
        """Remove all variant_applier Set Variant nodes under /stage."""
        stage_lop = hou.node("/stage")
        if stage_lop is None:
            hou.ui.displayMessage("No /stage found.")
            return

        deleted = 0
        for n in stage_lop.children():
            if n.type().name() == "setvariant" and n.name().startswith("variant_applier"):
                n.destroy()
                deleted += 1

        hou.ui.displayMessage("Removed {} variant nodes.".format(deleted))


def onCreateInterface():
    return VariantSwitcher()
