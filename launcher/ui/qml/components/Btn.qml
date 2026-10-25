import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: root
    property string text: ""
    property string icon: ""
    property string variant: "primary"   // primary | secondary | danger | ghost
    property int fontSize: 14
    property int hPadding: 18
    signal clicked()

    implicitHeight: 40
    implicitWidth: row.implicitWidth + hPadding * 2
    radius: Theme.radius
    opacity: enabled ? 1.0 : 0.45

    readonly property color baseColor: variant === "primary" ? Theme.accent
        : variant === "danger" ? "#3b1a1d"
        : variant === "secondary" ? Theme.raised : "transparent"
    readonly property color hoverColor: variant === "primary" ? Theme.accentHover
        : variant === "danger" ? "#4d2125" : Theme.surfaceHover
    readonly property color pressColor: variant === "primary" ? Theme.accentPressed
        : variant === "danger" ? "#5c282d" : Theme.border
    readonly property color fgColor: variant === "primary" ? "white"
        : variant === "danger" ? Theme.danger : Theme.text

    color: mouse.pressed ? pressColor : mouse.containsMouse ? hoverColor : baseColor
    border.width: variant === "secondary" ? 1 : 0
    border.color: Theme.border
    scale: mouse.pressed ? 0.97 : 1.0

    Behavior on color { ColorAnimation { duration: Theme.animFast } }
    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8

        Icon {
            visible: root.icon !== ""
            name: root.icon
            size: root.fontSize + 4
            color: root.fgColor
        }
        Text {
            text: root.text
            color: root.fgColor
            font.pixelSize: root.fontSize
            font.weight: Font.DemiBold
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