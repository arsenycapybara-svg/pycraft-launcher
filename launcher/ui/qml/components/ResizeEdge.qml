import QtQuick
import QtQuick.Window

MouseArea {
    property int edges: 0
    readonly property var w: Window.window

    enabled: !!w && w.visibility !== Window.Maximized && w.visibility !== Window.FullScreen
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton
    onPressed: if (w) w.startSystemResize(edges)
}