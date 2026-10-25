import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: root
    property string message: ""

    visible: message !== ""
    Layout.fillWidth: true
    implicitHeight: Math.max(56, row.implicitHeight + 24)
    radius: Theme.radius
    color: "#2a1518"
    border.width: 1
    border.color: "#5c2a2f"

    TextEdit { id: clip; visible: false }

    RowLayout {
        id: row
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 14
        anchors.rightMargin: 12
        spacing: 12

        Text {
            Layout.fillWidth: true
            text: root.message
            color: "#ff6b6b"
            font.pixelSize: 14
            wrapMode: Text.WordWrap
        }

        Rectangle {
            id: copyBtn
            property bool done: false
            Layout.preferredWidth: 130
            Layout.preferredHeight: 34
            Layout.alignment: Qt.AlignTop
            radius: 8
            color: ma.containsMouse ? Theme.surfaceHover : Theme.surface

            Text {
                anchors.centerIn: parent
                text: copyBtn.done ? "Скопировано ✓" : "Скопировать"
                color: Theme.text
                font.pixelSize: 13
            }

            MouseArea {
                id: ma
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    clip.text = root.message
                    clip.selectAll()
                    clip.copy()
                    copyBtn.done = true
                    reset.restart()
                }
            }

            Timer { id: reset; interval: 1500; onTriggered: copyBtn.done = false }
        }
    }
}