import QtQuick
import "../theme"

Rectangle {
    id: root
    property string text: ""
    property bool active: false
    signal clicked()

    implicitHeight: 36
    implicitWidth: label.implicitWidth + 32
    radius: 10
    color: active ? Theme.accentSoft : mouse.containsMouse ? Theme.surfaceHover : "transparent"
    border.width: 1
    border.color: active ? Theme.accent : Theme.border

    Behavior on color { ColorAnimation { duration: Theme.animFast } }
    Behavior on border.color { ColorAnimation { duration: Theme.animFast } }

    Text {
        id: label
        anchors.centerIn: parent
        text: root.text
        font.pixelSize: 13
        font.weight: Font.Medium
        color: root.active ? Theme.accent : Theme.textDim
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}