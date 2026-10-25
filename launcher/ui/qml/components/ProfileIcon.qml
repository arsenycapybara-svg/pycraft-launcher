import QtQuick
import "../theme"

Rectangle {
    id: root
    property string icon: "grass"
    property real size: 48
    property bool selected: false
    // своя картинка уже с закруглёнными углами, поэтому рисуем её без подложки
    readonly property bool full: icon.indexOf("custom:") === 0

    width: size
    height: size
    implicitWidth: size
    implicitHeight: size
    radius: size * 0.2
    color: full ? "transparent" : Theme.bg
    border.width: full ? 0 : (selected ? 2 : 1)
    border.color: selected ? Theme.accent : Theme.border

    Behavior on border.color { ColorAnimation { duration: 120 } }

    Image {
        anchors.fill: parent
        anchors.margins: root.full ? 0 : root.size * 0.06
        source: icons.url(root.icon)
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
        asynchronous: true
        sourceSize.width: 128
        sourceSize.height: 128
    }

    // рамка выбора поверх своей картинки
    Rectangle {
        anchors.fill: parent
        radius: root.radius
        color: "transparent"
        border.width: root.full && root.selected ? 2 : 0
        border.color: Theme.accent
    }
}