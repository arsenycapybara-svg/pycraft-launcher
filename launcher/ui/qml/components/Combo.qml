import QtQuick
import QtQuick.Controls
import "../theme"

ComboBox {
    id: root
    implicitHeight: 48
    font.pixelSize: 16

    background: Rectangle {
        radius: Theme.radius
        color: Theme.bg
        border.width: 1
        border.color: root.popup.visible || root.hovered ? Theme.accent : Theme.surfaceHover
        Behavior on border.color { ColorAnimation { duration: Theme.animFast } }
    }

    contentItem: Text {
        leftPadding: 14
        rightPadding: 40
        text: root.displayText
        font: root.font
        color: Theme.text
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Text {
        x: root.width - width - 14
        y: (root.height - height) / 2
        text: "▾"
        color: Theme.textDim
        font.pixelSize: 16
    }

    delegate: ItemDelegate {
        id: del
        width: root.width - 16
        height: 40
        highlighted: root.highlightedIndex === index

        contentItem: Text {
            text: modelData
            color: del.highlighted ? "white" : Theme.text
            font.pixelSize: 15
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 8
            color: del.highlighted ? Theme.accent : "transparent"
        }
    }

    popup: Popup {
        y: root.height + 4
        width: root.width
        implicitHeight: Math.min(contentItem.implicitHeight + 16, 320)
        padding: 8

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: root.popup.visible ? root.delegateModel : null
            currentIndex: root.highlightedIndex
            ScrollBar.vertical: ScrollBar {}
        }
        background: Rectangle {
            radius: Theme.radius
            color: Theme.surface
            border.width: 1
            border.color: Theme.surfaceHover
        }
        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.animFast }
        }
    }
}