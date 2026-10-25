import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import "../theme"

Rectangle {
    id: bar
    property var win: null
    readonly property bool maximized: win !== null && win.visibility === Window.Maximized

    color: Theme.bg

    function toggleMax() {
        if (!win) return
        if (maximized) win.showNormal()
        else win.showMaximized()
    }

    DragHandler {
        target: null
        onActiveChanged: if (active && bar.win) bar.win.startSystemMove()
    }
    TapHandler { onDoubleTapped: bar.toggleMax() }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Item { Layout.preferredWidth: 16 }
        Rectangle {
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
            radius: 5
            color: Theme.accent
            Text { anchors.centerIn: parent; text: "P"; color: "white"; font.pixelSize: 11; font.bold: true }
        }
        Item { Layout.preferredWidth: 10 }
        Text { text: "PyCraft Launcher"; color: Theme.textDim; font.pixelSize: 12; font.weight: Font.Medium }
        Item { Layout.fillWidth: true }

        WindowButton { Layout.fillHeight: true; kind: "min"; onClicked: if (bar.win) bar.win.showMinimized() }
        WindowButton { Layout.fillHeight: true; kind: bar.maximized ? "restore" : "max"; onClicked: bar.toggleMax() }
        WindowButton { Layout.fillHeight: true; kind: "close"; onClicked: if (bar.win) bar.win.close() }
    }

    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.border }
}