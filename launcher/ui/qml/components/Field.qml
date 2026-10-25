import QtQuick
import QtQuick.Controls
import "../theme"

TextField {
    id: root
    color: Theme.text
    placeholderTextColor: Theme.textDim
    font.pixelSize: 15
    leftPadding: 14
    rightPadding: 14
    implicitHeight: 44
    selectByMouse: true

    background: Rectangle {
        radius: Theme.radius
        color: Theme.bg
        border.width: 1
        border.color: root.activeFocus ? Theme.accent : Theme.surfaceHover
        Behavior on border.color { ColorAnimation { duration: Theme.animFast } }
    }
}