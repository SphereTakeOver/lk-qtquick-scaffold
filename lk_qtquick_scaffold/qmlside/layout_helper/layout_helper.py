from __future__ import annotations

import typing as t
from functools import partial

from ..js_evaluator import eval_js
from ...qt_core import QObject
from ...qt_core import bind_func  # noqa
from ...qt_core import slot


class T:
    Orientation = t.Literal['h', 'horizontal', 'v', 'vertical']


class LayoutHelper(QObject):
    
    @slot(object, result=int)
    @slot(object, str, result=int)
    def get_content_width(self, text_item: QObject, text: str = None) -> int:
        if not text:
            return text_item.property('contentWidth')
        old, new = text_item.property('text'), text
        text_item.setProperty('text', text)
        size = text_item.property('contentWidth')
        text_item.setProperty('text', old)
        return size
    
    @slot(object, str)
    def auto_align(self, container: QObject, alignment: str):
        """
        args:
            alignment: accept multiple options, separated by comma (no space
                between).
                for example: 'hcenter,stretch'
                options list:
                    hcenter: child.horizontalCenter = container.horizontalCenter
                    vcenter: child.verticalCenter = container.verticalCenter
                    hfill: child.with = container.width
                    vfill: child.height = container.height
                    stretch
        """
        children = container.children()
        
        for a in alignment.split(','):
            if a == 'hcenter':
                for child in children:
                    eval_js('''
                        $child.anchors.horizontalCenter = Qt.binding(() => {
                            return $container.horizontalCenter
                        })
                    ''', {'child': child, 'container': container})
            
            elif a == 'vcenter':
                for child in children:
                    eval_js('''
                        $child.anchors.verticalCenter = Qt.binding(() => {
                            return $container.verticalCenter
                        })
                    ''', {'child': child, 'container': container})
            
            elif a == 'hfill' or a == 'vfill':
                def resize_children(orientation: str):
                    nonlocal container
                    prop = 'width' if orientation == 'h' else 'height'
                    for child in container.children():
                        child.setProperty(prop, container.property(prop))
                
                if a == 'hfill':
                    container.widthChanged.connect(
                        partial(resize_children, 'h')
                    )
                    container.widthChanged.emit()
                else:
                    container.heightChanged.connect(
                        partial(resize_children, 'v')
                    )
                    container.heightChanged.emit()
            
            elif a == 'stretch':
                container_type = self._detect_container_type(container)
                
                def stretch_children(orientation: str):
                    nonlocal container
                    prop = 'width' if orientation == 'h' else 'height'
                    children = container.children()
                    size_total = (container.property(prop)
                                  - container.property('spacing')
                                  * (len(children) - 1))
                    size_aver = size_total / len(children)
                    # print(':v', prop, size_total, size_aver)
                    for child in container.children():
                        child.setProperty(prop, size_aver)
                
                if container_type == 0:
                    container.widthChanged.connect(
                        partial(stretch_children, 'h')
                    )
                    container.widthChanged.emit()
                elif container_type == 1:
                    container.heightChanged.connect(
                        partial(stretch_children, 'v')
                    )
                    container.heightChanged.emit()
    
    @slot(object, str, result=bool)
    def auto_size_children(
            self,
            container: QObject,
            orientation: T.Orientation
    ) -> bool:
        """
        size policy:
            0: auto stretch to spared space.
            0 ~ 1: the ratio of spared space.
            1+: regular pixel point.
        
        workflow:
            1. get total space
            2. consume used space
            3. allocate unused space

        TODO: method rename (candidate names):
            mobilize
            auto_pack
        
        return: is dynamical binding effective?
            True means whenever container's size changed, this method should be
            called again.
        """
        prop_name = 'width' if orientation in ('h', 'horizontal') else 'height'
        # if container.property(prop_name) <= 0: return False
        
        children = container.children()
        
        elastic_items: dict[int, float] = {}  # dict[int index, float ratio]
        stretch_items: dict[int, int] = {}  # dict[int index, int _]
        #   note: stretch_items.values() are useless (they are all zeros). it
        #   is made just for keeping the same form with elastic_items.
        
        claimed_size = 0
        for idx, item in enumerate(children):
            size = item.property(prop_name)
            if size < 0:
                raise ValueError('cannot allocate negative size', idx, item)
            elif size == 0:
                stretch_items[idx] = 0
            elif 0 < size < 1:
                elastic_items[idx] = size
            else:
                claimed_size += size
        
        if not elastic_items and not stretch_items:
            return False
        
        self._auto_size_children(
            container, orientation, claimed_size,
            elastic_items, stretch_items
        )
        
        # print(':l', 'overview container and children sizes:',
        #       (container.property('width'), container.property('height')),
        #       {(x.property('objectName') or 'child') + f'#{idx}': (
        #           x.property('width'), x.property('height')
        #       ) for idx, x in enumerate(children)})
        
        # TODO: if children count is changed, trigger this method again.
        bind_func(
            container, f'{prop_name}Changed',
            partial(
                self._auto_size_children,
                container=container,
                orientation=orientation,
                claimed_size=claimed_size,
                elastic_items=elastic_items,
                stretch_items=stretch_items,
            )
        )
        
        return True
    
    def _auto_size_children(
            self,
            container: QObject,
            orientation: T.Orientation,
            claimed_size: int,
            elastic_items: dict[int, float],
            stretch_items: dict[int, int]
    ) -> None:
        """
        note: param `stretch_items`.values() are useless (they are all zero), 
            it is made just for keeping same type form with `elastic_items`.
        """
        prop_name = 'width' if orientation in ('h', 'horizontal') else 'height'
        
        children = container.children()
        total_spare_size = self._get_total_available_size_for_children(
            container, len(children), orientation)
        unclaimed_size = total_spare_size - claimed_size
        # print(container.property(prop_name), total_spare_size, claimed_size,
        #       unclaimed_size, orientation, len(children), ':l')
        
        if unclaimed_size <= 0:
            # fast finish leftovers
            for idx, item in enumerate(children):
                if idx in elastic_items:
                    item.setProperty(prop_name, 0)
                # note: no need to check if idx in stretch_items, because their
                # size is already 0.
            return
        
        # allocate elastic items
        total_unclaimed_size = unclaimed_size
        for idx, ratio in elastic_items.items():
            child = children[idx]
            size = total_unclaimed_size * ratio
            child.setProperty(prop_name, size)
            unclaimed_size -= size
        
        if unclaimed_size <= 0:
            return
        
        # allocate stretch items
        total_unclaimed_size = unclaimed_size
        stretch_items_count = len(stretch_items)
        stretch_item_size_aver = total_unclaimed_size / stretch_items_count
        for idx in stretch_items.keys():
            child = children[idx]
            child.setProperty(prop_name, stretch_item_size_aver)
    
    @staticmethod
    def _get_total_available_size_for_children(
            item: QObject,
            children_count: int,
            orientation: T.Orientation
    ) -> int:
        # print(':lp', {p: item.property(p) for p in (
        #     'width', 'height', 'spacing', 'padding',
        #     'leftPadding', 'rightPadding', 'topPadding', 'bottomPadding'
        # )})
        if orientation in ('h', 'horizontal'):
            return (
                    item.property('width')
                    - item.property('leftPadding')
                    - item.property('rightPadding')
                    - item.property('spacing') * (children_count - 1)
            )
        else:
            return (
                    item.property('height')
                    - item.property('topPadding')
                    - item.property('bottomPadding')
                    - item.property('spacing') * (children_count - 1)
            )
    
    @slot(list, result=tuple)
    @slot(list, int, result=tuple)
    @slot(list, int, int, result=tuple)
    def calc_text_block_size(
            self, lines: list[str],
            char_width=10, line_height=20
    ):
        lines = tuple(map(str, lines))
        # OPTM: use different char_width for non-ascii characters.
        width = max(map(len, lines)) * char_width
        height = (len(lines) + 1) * line_height
        return width, height
    
    @slot(object, str)
    def equal_size_children(self, container: QObject, orientation: str):
        # roughly equal size children
        children = container.children()
        if orientation in ('horizontal', 'h'):
            prop = 'width'
        else:
            prop = 'height'
        average_size = container.property(prop) / len(children)
        for item in children:
            item.setProperty(prop, average_size)
    
    @staticmethod
    def _detect_container_type(container: QObject) -> int:
        """
        return: 0 for row, 1 for column.
        help: if container is row, it has property 'effectiveLayoutDirection'
            (the value is Qt.LeftToRight(=0) or Qt.RightToLeft(=1)), while
            column doesn't have this property(=None).
        """
        if container.property('effectiveLayoutDirection') is not None:
            return 0  # row
        else:
            return 1  # column


pylayout = LayoutHelper()
