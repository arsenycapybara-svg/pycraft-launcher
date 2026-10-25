import QtQuick
import "../theme"

Rectangle {
    id: root
    property string name: ""

    implicitWidth: 40
    implicitHeight: 40
    radius: width / 2
    color: Theme.accentSoft
    border.width: 1
    border.color: Theme.accent

    Text {
        anchors.centerIn: parent
        text: root.name.length > 0 ? root.name[0].toUpperCase() : "?"
        color: Theme.accent
        font.bold: true
        font.pixelSize: root.width * 0.42
    }
}