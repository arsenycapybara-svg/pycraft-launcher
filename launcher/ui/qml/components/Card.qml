import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import "../theme"

Item {
    id: root
    property bool shadow: false
    property bool tint: false
    property color color: Theme.raised
    property color borderColor: Theme.border
    property int radius: Theme.radiusLg
    property int padding: 20
    property int spacing: 8
    default property alias content: col.data

    implicitWidth: col.implicitWidth + padding * 2
    implicitHeight: col.implicitHeight + padding * 2

    Rectangle {
        id: bg
        anchors.fill: parent
        radius: root.radius
        color: root.color
        border.width: 1
        border.color: root.borderColor
    }

    // мягкая тень: рисуется только под подложкой, содержимое карточки не копируется
    MultiEffect {
        visible: root.shadow
        source: bg
        anchors.fill: bg
        z: -1
        shadowEnabled: true
        shadowColor: "#b0000000"
        shadowBlur: 1.0
        shadowVerticalOffset: 8
        autoPaddingEnabled: true
    }

    Rectangle {
        visible: root.tint
        anchors.fill: bg
        radius: root.radius
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.22) }
            GradientStop { position: 1.0; color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.0) }
        }
    }

    ColumnLayout {
        id: col
        anchors.fill: parent
        anchors.margins: root.padding
        spacing: root.spacing
    }
}