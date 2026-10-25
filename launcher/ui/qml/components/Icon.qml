import QtQuick
import QtQuick.Shapes

Item {
    id: root
    property string name: ""
    property color color: "white"
    property real size: 20
    property real strokeWidth: 1.8

    width: size
    height: size
    implicitWidth: size
    implicitHeight: size

    readonly property var paths: ({
        "play":     "M7 4 L20 12 L7 20 Z",
        "stop":     "M7 7 H17 V17 H7 Z",
        "versions": "M12 4 V15 M7.5 10.5 L12 15 L16.5 10.5 M5 20 H19",
        "mods":     "M12 3 L20 7.5 V16.5 L12 21 L4 16.5 V7.5 Z M4 7.5 L12 12 L20 7.5 M12 12 V21",
        "settings": "M4 7 H20 M4 17 H20 M9 4.5 V9.5 M15 14.5 V19.5",
        "user":     "M12 11 A4 4 0 1 0 12 3 A4 4 0 1 0 12 11 Z M4.5 21 C4.5 16.5 8 14 12 14 C16 14 19.5 16.5 19.5 21",
        "folder":   "M3 7 H10 L12 9 H21 V19 H3 Z",
        "close":    "M6 6 L18 18 M18 6 L6 18"
    })

    Shape {
        width: 24
        height: 24
        scale: root.size / 24
        transformOrigin: Item.TopLeft
        layer.enabled: true
        layer.samples: 4

        ShapePath {
            strokeColor: root.color
            strokeWidth: root.strokeWidth
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: root.paths[root.name] || "" }
        }
    }
}