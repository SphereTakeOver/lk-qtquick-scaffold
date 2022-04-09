from PySide6.QtCore import QAbstractListModel
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import Qt

from ..pyside import slot


class T:  # 'TypeHint'
    from typing import Any, Dict, List
    
    Item = dict
    Items = List[dict]
    XItems = List[Dict[bytes, Any]]
    
    RoleName = str
    RoleNames = List[str]
    XRoleNames = Dict[int, bytes]  # the bytes is converted from RoleName.


class Model(QAbstractListModel):
    """
    references:
        https://pyblish.gitbooks.io/developer-guide/content/qml_and_python
            _interoperability.html
        https://stackoverflow.com/questions/54687953/declaring-a
            -qabstractlistmodel-as-a-property-in-pyside2
    """
    _role_names: T.XRoleNames
    _items: T.XItems
    
    def __init__(self, role_names: T.RoleNames):
        super().__init__()
        self._role_names = {
            i: n.encode(encoding='utf-8')
            for i, n in enumerate(role_names, Qt.UserRole + 1)  # noqa
        }
        self._items = []
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, index: int):
        return {k.decode(encoding='utf-8'): v
                for k, v in self._items[index].items()}
    
    # -------------------------------------------------------------------------
    # pyside api
    
    def append(self, item: T.Item):
        self.beginInsertRows(
            QModelIndex(), self.rowCount(), self.rowCount()
        )
        self._items.append({k.encode(encoding='utf-8'): v
                            for k, v in item.items()})
        self.endInsertRows()
    
    def append_many(self, items: T.Items):
        self.beginInsertRows(
            QModelIndex(), self.rowCount(), self.rowCount() + len(items) - 1
        )
        for item in items:
            self._items.append({k.encode(encoding='utf-8'): v
                                for k, v in item.items()})
        self.endInsertRows()
    
    def insert(self, index: int, item: T.Item):
        self.beginInsertRows(
            QModelIndex(), index, index
        )
        self._items.insert(index, {k.encode(encoding='utf-8'): v
                                   for k, v in item.items()})
        self.endInsertRows()
    
    def insert_many(self, index: int, items: T.Items):
        self.beginInsertRows(
            QModelIndex(), index, index + len(items) - 1
        )
        temp_list = []
        for item in items:
            temp_list.append({k.encode(encoding='utf-8'): v
                              for k, v in item.items()})
        self._items = self._items[:index] + temp_list + self._items[index:]
        self.endInsertRows()
    
    def update(self, index: int, item: dict) -> dict:
        self._items[index].update({
            k.encode(encoding='utf-8'): v for k, v in item.items()
        })
        # emit signal of `self.dataChanged` to notify qml side that some item
        # has been changed.
        # `dataChanged.emit` accepts two arguments:
        #   dataChanged.emit(QModelIndex start, QModelIndex end)
        # how to create QModelIndex instance: use `self.createIndex(row, col)`.
        # ref: https://blog.csdn.net/LaoYuanPython/article/details/102011031
        qindex = self.createIndex(index, 0)
        self.dataChanged.emit(qindex, qindex)  # noqa
        return self[index]
    
    def pop(self):
        self.beginRemoveRows(
            QModelIndex(), len(self._items) - 1, len(self._items) - 1
        )
        self._items.pop(0)
        self.endRemoveRows()
    
    def pop_many(self, count: int):
        assert count > 0
        self.beginRemoveRows(
            QModelIndex(), len(self._items) - count, len(self._items) - 1
        )
        self._items = self._items[:-count]
        self.endRemoveRows()
    
    def delete(self, index: int):
        self.beginRemoveRows(
            QModelIndex(), index, index
        )
        self._items.pop(index)
        self.endRemoveRows()
    
    def delete_many(self, index: int, count: int):
        assert count > 0
        self.beginRemoveRows(
            QModelIndex(), index, index + count - 1
        )
        self._items = self._items[:index] + self._items[index + count:]
        self.endRemoveRows()
    
    def clear(self):
        self.beginRemoveRows(
            QModelIndex(), 0, len(self._items) - 1
        )
        self._items.clear()
        self.endRemoveRows()
    
    # -------------------------------------------------------------------------
    # qml side api
    
    @slot(int, result=dict)
    def qget(self, index: int):
        return self[index]
    
    @slot(int, dict, result=dict)
    def qupdate(self, index: int, item: dict) -> dict:
        return self.update(index, item)
    
    # -------------------------------------------------------------------------
    # overrides
    
    # noinspection PyMethodOverriding
    def data(self, index, role: int):
        name = self._role_names[role]
        return self._items[index.row()].get(name, '')
    
    # noinspection PyMethodOverriding,PyTypeChecker,PyUnresolvedReferences
    def setData(self, index, value, role):
        name = self.role_names[role]
        self._items[index.row()][name] = value
        self.dataChanged.emit(index, index)
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._items)
    
    def roleNames(self):
        # lk.logt('[D5645]', self.role_names)
        return self._role_names
