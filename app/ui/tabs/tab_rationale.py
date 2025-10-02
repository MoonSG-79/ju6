
from PyQt5 import QtWidgets, QtCore
import pandas as pd
from app.core.db import get_session, RationaleItem, RationaleWeight
from sqlalchemy import delete

class RationaleTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        v = QtWidgets.QVBoxLayout(self)

        top = QtWidgets.QHBoxLayout()
        self.btn_open_tpl = QtWidgets.QPushButton("Open Template Path")
        self.btn_load_xlsx = QtWidgets.QPushButton("Load Excel")
        self.btn_save = QtWidgets.QPushButton("Save to DB (normalize to 100 each profile)")
        self.chk_selected = QtWidgets.QCheckBox("Use Checked Only")
        top.addWidget(self.btn_open_tpl); top.addWidget(self.btn_load_xlsx); top.addWidget(self.btn_save); top.addWidget(self.chk_selected)
        v.addLayout(top)

        self.table = QtWidgets.QTableWidget()
        v.addWidget(self.table)
        self.lbl = QtWidgets.QLabel("")
        v.addWidget(self.lbl)

        self.btn_open_tpl.clicked.connect(self.open_tpl_info)
        self.btn_load_xlsx.clicked.connect(self.load_excel)
        self.btn_save.clicked.connect(self.save_db)

        self.df = None

    def open_tpl_info(self):
        QtWidgets.QMessageBox.information(self, "Template", "Project template path: data/templates/rationale_template.xlsx")

    def load_excel(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Excel", "", "Excel Files (*.xlsx)")
        if not path: return
        self.df = pd.read_excel(path)
        if "Use" not in self.df.columns:
            self.df["Use"] = True
        self.render_table(self.df)
        self.lbl.setText(f"Loaded: {path}")

    def render_table(self, df):
        cols = list(df.columns)
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(df))
        self.table.setHorizontalHeaderLabels(cols)
        for r in range(len(df)):
            for c, col in enumerate(cols):
                if col == "Use":
                    chk = QtWidgets.QTableWidgetItem()
                    chk.setFlags(chk.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    chk.setCheckState(QtCore.Qt.Checked if bool(df.iloc[r][col]) else QtCore.Qt.Unchecked)
                    self.table.setItem(r, c, chk)
                else:
                    it = QtWidgets.QTableWidgetItem(str(df.iloc[r][col]))
                    if col in ("Scalp_Weight","Day_Weight","Mid_Weight"):
                        it.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                    self.table.setItem(r, c, it)
        self.table.resizeColumnsToContents()

    def save_db(self):
        if self.df is None:
            QtWidgets.QMessageBox.warning(self, "Warn", "Load Excel first.")
            return
        df = self.df.copy()
        if "Use" not in df.columns:
            df["Use"] = True
        use_idx = list(df.columns).index("Use")
        for r in range(self.table.rowCount()):
            it = self.table.item(r, use_idx)
            df.at[r, "Use"] = (it.checkState() == QtCore.Qt.Checked) if it else True

        for prof, col in {"scalp":"Scalp_Weight", "day":"Day_Weight", "mid":"Mid_Weight"}.items():
            mask = df["Use"].astype(bool) & df[col].fillna(0).astype(float).gt(0)
            s = df.loc[mask, col].astype(float)
            total = s.sum()
            if total == 0: continue
            df.loc[mask, col] = (s / total) * 100.0

        with get_session() as s:
            s.execute(delete(RationaleItem)); s.execute(delete(RationaleWeight)); s.commit()
            for i, row in df.iterrows():
                if not bool(row.get("Use", True)): continue
                item = RationaleItem(name=str(row["지표명"]), note=str(row.get("근거(메모)","")), idx=int(row["번호"]))
                s.add(item); s.flush()
                for prof, col in {"scalp":"Scalp_Weight", "day":"Day_Weight", "mid":"Mid_Weight"}.items():
                    w = float(row.get(col, 0.0) or 0.0)
                    s.add(RationaleWeight(profile=prof, item_id=item.id, weight=w))
            s.commit()
        QtWidgets.QMessageBox.information(self, "Saved", "Weights saved & normalized per profile.")
