import QtQuick 2.14
import QtQuick.Controls 2.14
import "../LCStyle/palette.js" as LCPalette

LCBaseButton {
    id: _root
    flat: true
    hoverEnabled: true

    p_autoSize: true
    p_border.width: 0
    p_colorBg0: LCPalette.Transparent
    p_colorBg1: LCPalette.Transparent
    p_colorText0: LCPalette.TextNormal
    p_colorText1: LCPalette.TextHighlight
    // more:
    //      p_active
    //      p_text
    //      p_width
    //      p_height

    __bg.color: {
        if (_root.hovered) {
            return LCPalette.ButtonHovered
        } else if (_root.pressed) {
            return LCPalette.ButtonPressed
        } else if (p_active) {
            return p_colorBg0
        } else {
            return p_colorBg1
        }
    }

    onPressed: p_active = !p_active
}
