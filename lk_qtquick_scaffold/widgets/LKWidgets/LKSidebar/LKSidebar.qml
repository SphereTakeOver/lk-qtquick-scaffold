import QtQuick 2.15
import ".."
import "../LKButtons"

LKRectangle {
    id: root
    width: pysize.sidebar_width
    height: pysize.sidebar_height
    clip: true
    color: pycolor.sidebar_bg

    property var  model
    //  union[list[str], list[dict]]
    //      for list[dict]:
    //          required keys:
    //              text: str
    //          optional keys:
    //              icon: str
    //              color: str
    property bool reuseItems: true

    signal clicked(int index, string text)

    onModelChanged: {
        if (root.model) {
            _listview.model = PyListView.fill_model(
                root.model, {'text': '', 'icon': '', 'color': ''}, 'text'
            )
        }
    }

    ListView {
        id: _listview
        anchors {
            fill: parent
            leftMargin: pysize.margin_m
            rightMargin: pysize.margin_m
            topMargin: pysize.margin_s
            bottomMargin: pysize.margin_s
        }
        reuseItems: root.reuseItems
        spacing: pysize.spacing_m

        delegate: LKGhostButton {
            width: _listview.width
            height: pysize.button_height_l
            iconColor: modelData.color
            iconSize: 28
            iconSource: modelData.icon
            text: modelData.text

            property int index: model.index

            onClicked: {
                root.clicked(this.index, this.text)
                _listview.currentIndex = this.index
            }

            Component.onCompleted: {
//                this.textDelegate.horizontalAlignment = Text.AlignLeft
                this.selected = Qt.binding(() => {
                    return this.index == _listview.currentIndex
                })
            }
        }
    }
}
