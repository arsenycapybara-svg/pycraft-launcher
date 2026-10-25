import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"

Item {
    id: page
    property string selectedId: ""
    property string selectedLabel: ""
    property string error: ""

    function installedFlag() {
        var l = versions.versions
        for (var i = 0; i < l.length; i++)
            if (l[i].id === selectedId) return l[i].installed
        return false
    }
    readonly property bool selectedInstalled: { versions.versions; selectedId; return installedFlag() }

    Component.onCompleted: versions.refresh()

    Connections {
        target: versions
        function onErrorOccurred(msg) { page.error = msg }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 16

        Text {
            text: "Версии и загрузчики"
            color: Theme.text
            font.pixelSize: 28
            font.weight: Font.Bold
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { id: "vanilla", name: "Vanilla" },
                    { id: "fabric",  name: "Fabric"  },
                    { id: "forge",   name: "Forge"   }
                ]
                Chip {
                    text: modelData.name
                    active: versions.loader === modelData.id
                    onClicked: {
                        page.selectedId = ""
                        page.selectedLabel = ""
                        page.error = ""
                        versions.setLoader(modelData.id)
                    }
                }
            }

            Item { Layout.fillWidth: true }

            Chip {
                text: versions.snapshots ? "Снапшоты: вкл" : "Снапшоты: выкл"
                active: versions.snapshots
                onClicked: versions.setSnapshots(!versions.snapshots)
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 160
            padding: 8
            spacing: 0

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ListView {
                    id: list
                    anchors.fill: parent
                    clip: true
                    spacing: 4
                    model: versions.versions
                    ScrollBar.vertical: ScrollBar {}

                    delegate: Rectangle {
                        id: row
                        property bool sel: page.selectedId === modelData.id
                        width: list.width - 12
                        height: 48
                        radius: 10
                        color: sel ? Theme.accentSoft : hover.containsMouse ? Theme.surfaceHover : "transparent"
                        border.width: sel ? 1 : 0
                        border.color: Theme.accent
                        Behavior on color { ColorAnimation { duration: Theme.animFast } }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            spacing: 10

                            Text {
                                text: modelData.mc
                                color: Theme.text
                                font.pixelSize: 15
                                font.weight: Font.DemiBold
                            }

                            Rectangle {
                                visible: modelData.mod !== ""
                                radius: 6
                                color: Theme.accentSoft
                                implicitWidth: modLabel.implicitWidth + 16
                                implicitHeight: 24

                                Text {
                                    id: modLabel
                                    anchors.centerIn: parent
                                    text: modelData.mod
                                    color: Theme.accent
                                    font.pixelSize: 12
                                    font.weight: Font.Medium
                                }
                            }

                            Text {
                                visible: modelData.type === "snapshot"
                                text: "снапшот"
                                color: Theme.textFaint
                                font.pixelSize: 12
                            }

                            Item { Layout.fillWidth: true }

                            Text {
                                visible: modelData.installed
                                text: "✓ Установлена"
                                color: Theme.success
                                font.pixelSize: 13
                                font.weight: Font.Medium
                            }
                        }

                        MouseArea {
                            id: hover
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                page.selectedId = modelData.id
                                page.selectedLabel = modelData.mc
                                    + (modelData.mod !== "" ? "  ·  " + modelData.mod : "")
                            }
                        }
                    }
                }

                Text {
                    anchors.centerIn: parent
                    visible: versions.loading
                    text: "Загрузка списка..."
                    color: Theme.textDim
                    font.pixelSize: 15
                }
                Text {
                    anchors.centerIn: parent
                    visible: !versions.loading && list.count === 0
                    text: "Нет доступных версий"
                    color: Theme.textDim
                    font.pixelSize: 15
                }
            }
        }

        ProgressPanel {
            Layout.fillWidth: true
            active: versions.installing
            title: "Установка версии"
            detail: versions.status
            progress: versions.progress > 0 ? versions.progress : -1
        }

        Btn {
            Layout.preferredHeight: 48
            Layout.preferredWidth: 380
            fontSize: 15
            text: versions.installing ? "Установка..."
                : page.selectedId === "" ? "Выберите версию"
                : page.selectedInstalled ? "Уже установлена"
                : "Установить " + page.selectedLabel
            icon: page.selectedId !== "" && !page.selectedInstalled && !versions.installing ? "versions" : ""
            enabled: !versions.installing && page.selectedId !== "" && !page.selectedInstalled
            onClicked: { page.error = ""; versions.install(page.selectedId) }
        }

        ErrorBox { message: page.error }
    }
}