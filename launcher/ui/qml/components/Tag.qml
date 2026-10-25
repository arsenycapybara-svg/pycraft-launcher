import QtQuick
import "../theme"

Rectangle {
    id: root
    property string text: ""
    property color tint: Theme.accent

    implicitWidth: label.implicitWidth + 16
    implicitHeight: 24
    radius: 6
    color: Qt.rgba(tint.r, tint.g, tint.b, 0.14)

    Text {
        id: label
        anchors.centerIn: parent
        text: root.text
        color: root.tint
        font.pixelSize: 12
        font.weight: Font.Medium
    }
}