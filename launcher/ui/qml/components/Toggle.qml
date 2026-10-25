import QtQuick
import QtQuick.Controls
import "../theme"

Switch {
    id: control
    implicitWidth: 44
    implicitHeight: 24

    indicator: Rectangle {
        width: 44
        height: 24
        radius: 12
        color: control.checked ? Theme.accent : Theme.bg
        border.width: 1
        border.color: control.checked ? Theme.accent : Theme.border
        Behavior on color { ColorAnimation { duration: Theme.animFast } }

        Rectangle {
            y: 3
            x: control.checked ? parent.width - width - 3 : 3
            width: 18
            height: 18
            radius: 9
            color: "white"
            Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
        }
    }
    contentItem: Item {}
}