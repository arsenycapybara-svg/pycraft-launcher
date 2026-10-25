import QtQuick
import QtQuick.Controls
import "../theme"

Slider {
    id: control
    implicitHeight: 28

    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: control.availableWidth
        height: 6
        radius: 3
        color: Theme.bg

        Rectangle {
            width: control.visualPosition * parent.width
            height: parent.height
            radius: 3
            color: Theme.accent
        }
    }

    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: 20
        height: 20
        radius: 10
        color: "white"
        border.width: 2
        border.color: Theme.accent
        scale: control.pressed ? 1.15 : control.hovered ? 1.08 : 1.0
        Behavior on scale { NumberAnimation { duration: 100 } }
    }
}