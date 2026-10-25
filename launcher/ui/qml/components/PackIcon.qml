import QtQuick
import "../theme"

Rectangle {
    id: root
    property string source: ""
    property string label: ""

    implicitWidth: 46
    implicitHeight: 46
    radius: 10
    color: Theme.accentSoft

    Image {
        id: img
        anchors.fill: parent
        anchors.margins: 3
        source: root.source
        asynchronous: true
        fillMode: Image.PreserveAspectFit
        sourceSize.width: 96
        sourceSize.height: 96
        visible: status === Image.Ready
    }

    Text {
        anchors.centerIn: parent
        visible: img.status !== Image.Ready
        text: root.label.length > 0 ? root.label[0].toUpperCase() : "?"
        color: Theme.accent
        font.bold: true
        font.pixelSize: 18
    }
}