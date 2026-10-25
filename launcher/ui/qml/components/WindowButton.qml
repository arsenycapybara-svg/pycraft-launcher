import QtQuick
import "../theme"

Rectangle {
    id: root
    property string kind: "close"   // min | max | restore | close
    signal clicked()

    implicitWidth: 46
    implicitHeight: 38
    color: ma.containsMouse ? (kind === "close" ? "#e5484d" : Theme.surfaceHover) : Theme.bg
    Behavior on color { ColorAnimation { duration: 100 } }

    readonly property color fg: ma.containsMouse && kind === "close" ? "white" : Theme.textDim

    Rectangle {
        visible: root.kind === "min"
        anchors.centerIn: parent
        width: 10; height: 1
        color: root.fg
    }
    Rectangle {
        visible: root.kind === "max"
        anchors.centerIn: parent
        width: 10; height: 10
        color: "transparent"
        border.width: 1
        border.color: root.fg
    }
    Item {
        visible: root.kind === "restore"
        anchors.centerIn: parent
        width: 11; height: 11
        Rectangle { x: 3; y: 0; width: 8; height: 8; color: "transparent"; border.width: 1; border.color: root.fg }
        Rectangle { x: 0; y: 3; width: 8; height: 8; color: root.color; border.width: 1; border.color: root.fg }
    }
    Icon {
        visible: root.kind === "close"
        anchors.centerIn: parent
        name: "close"
        size: 14
        color: root.fg
        strokeWidth: 1.6
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()
    }
}