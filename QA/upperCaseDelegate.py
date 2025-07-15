from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit

class UpperCaseDelegate(QStyledItemDelegate):
    """Class to update colunms with upper case """
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.textChanged.connect(lambda text: editor.setText(text.upper()))
        return editor
