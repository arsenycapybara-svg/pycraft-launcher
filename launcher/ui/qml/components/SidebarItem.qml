import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: root
    property string text: ""
    property string icon: ""
    property bool active: false
    signal clicked()

    implicitHeight: 44
    radius: Theme.radius
    color: active ? Theme.accentSoft : mouse.containsMouse ? Theme.surfaceHover : "transparent"
    Behavior on color { ColorAnimation { duration: Theme.animFast } }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 14
        spacing: 12

        Icon {
            name: root.icon
            size: 20
            color: root.active ? Theme.accent : Theme.textDim
            Behavior on color { ColorAnimation { duration: Theme.animFast } }
        }
        Text {
            Layout.fillWidth: true
            text: root.text
            font.pixelSize: 14
            font.weight: Font.Medium
            color: root.active ? Theme.text : Theme.textDim
            Behavior on color { ColorAnimation { duration: Theme.animFast } }
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}