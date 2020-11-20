import QtQuick 2.15
import QtQuick.Controls 2.15

import "../"
import "../LCStyle/dimension.js" as LCDimension
import "../LCStyle/palette.js" as LCPalette


RadioButton {
    id: _root
    width: LCDimension.ButtonWidthM; height: LCDimension.ButtonHeightM

    property alias p_text: _root.text
    property alias r_active: _root.checked

    background: LCRectangle {
        id: _bgrect
        color: {
            if (r_active) {
                return LCPalette.ButtonPressed
            } else if (_area.containsMouse) {
                return LCPalette.ButtonHovered
            } else {
                return LCPalette.Transparent
            }
        }
        radius: LCDimension.RadiusS

        MouseArea {
            id: _area
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                _root.checked = !_root.checked  // r_active changed
            }
        }
    }

    contentItem: LCText {
        id: _txt
        p_color: r_active ? LCPalette.TextWhite : LCPalette.TextNormal
        p_text: _root.text
    }

    indicator: Item {}
}
