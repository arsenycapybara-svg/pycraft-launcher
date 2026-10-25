import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes
import "../theme"

Card {
    id: root
    property bool active: false
    property string title: ""
    property string detail: ""
    property real progress: -1        // -1 = неопределённый прогресс

    padding: 18
    spacing: 12
    opacity: active ? 1.0 : 0.0
    visible: opacity > 0.01
    Behavior on opacity { NumberAnimation { duration: Theme.animNormal } }

    function ru(s) {
        if (!s) return ""
        return s.replace(/^Download(ing)?\s*/i, "Загрузка ")
                .replace(/^Install(ing)?\s*/i, "Установка ")
                .replace(/^Running\s*/i, "Выполнение ")
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 14

        Item {
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24

            Shape {
                anchors.fill: parent
                layer.enabled: true
                layer.samples: 4
                ShapePath {
                    strokeColor: Theme.accent
                    strokeWidth: 2.5
                    fillColor: "transparent"
                    capStyle: ShapePath.RoundCap
                    PathAngleArc { centerX: 12; centerY: 12; radiusX: 9; radiusY: 9; startAngle: 0; sweepAngle: 270 }
                }
                RotationAnimator on rotation { from: 0; to: 360; duration: 900; loops: Animation.Infinite; running: root.visible }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text { text: root.title; color: Theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }
            Text {
                Layout.fillWidth: true
                text: root.ru(root.detail)
                color: Theme.textDim
                font.pixelSize: 12
                elide: Text.ElideRight
            }
        }

        Text {
            visible: root.progress >= 0
            text: Math.round(root.progress * 100) + "%"
            color: Theme.accent
            font.pixelSize: 18
            font.weight: Font.Bold
        }
    }

    Rectangle {
        id: track
        Layout.fillWidth: true
        Layout.preferredHeight: 6
        radius: 3
        color: Theme.bg
        clip: true

        Rectangle {
            visible: root.progress >= 0
            height: parent.height
            radius: 3
            color: Theme.accent
            width: parent.width * Math.max(0, Math.min(root.progress, 1))
            Behavior on width { NumberAnimation { duration: Theme.animFast } }
        }

        Rectangle {
            id: sweep
            visible: root.progress < 0
            width: parent.width * 0.3
            height: parent.height
            radius: 3
            color: Theme.accent
            SequentialAnimation on x {
                loops: Animation.Infinite
                running: root.visible && root.progress < 0
                NumberAnimation { from: -sweep.width; to: track.width; duration: 1200; easing.type: Easing.InOutQuad }
            }
        }
    }
}