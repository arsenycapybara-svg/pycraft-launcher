import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "../theme"
import "../components"

Item {
    id: page
    property string note: ""
    readonly property var accentColors: ["#3b82f6", "#8b5cf6", "#10b981", "#f43f5e", "#f59e0b", "#06b6d4"]

    function syncFields() {
        gameField.text = cfg.gameDir
        wField.text = cfg.resWidth
        hField.text = cfg.resHeight
        jvmField.text = cfg.javaArgs
    }

    function applyResolution() {
        cfg.setResolution(parseInt(wField.text) || 854, parseInt(hField.text) || 480)
    }

    Component.onCompleted: syncFields()

    Connections {
        target: cfg
        function onSettingsChanged() { page.syncFields() }
        function onCacheCleared(msg) { page.note = msg }
    }

    FolderDialog {
        id: folderDlg
        title: "Папка игры"
        onAccepted: cfg.setGameDir(selectedFolder.toString())
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        padding: 28
        contentWidth: availableWidth

        ColumnLayout {
            width: scroll.availableWidth
            spacing: 16

            Text {
                text: "Настройки"
                color: Theme.text
                font.pixelSize: 28
                font.weight: Font.Bold
            }

            // ----- память -----
            Card {
                Layout.fillWidth: true
                padding: 24
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        Layout.fillWidth: true
                        text: "Оперативная память"
                        color: Theme.text
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: (cfg.ramMb / 1024).toFixed(2) + " ГБ"
                        color: Theme.accent
                        font.pixelSize: 18
                        font.weight: Font.Bold
                    }
                }

                Slide {
                    Layout.fillWidth: true
                    from: 1024
                    to: cfg.maxRamMb
                    stepSize: 256
                    snapMode: Slider.SnapAlways
                    value: cfg.ramMb
                    onMoved: cfg.setRamMb(Math.round(value))
                }

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        Layout.fillWidth: true
                        text: "1 ГБ"
                        color: Theme.textFaint
                        font.pixelSize: 12
                    }
                    Text {
                        text: (cfg.maxRamMb / 1024).toFixed(0) + " ГБ"
                        color: Theme.textFaint
                        font.pixelSize: 12
                    }
                }
            }

            // ----- игра -----
            Card {
                Layout.fillWidth: true
                padding: 24
                spacing: 12

                Text {
                    text: "Игра"
                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                Text {
                    text: "Папка игры"
                    color: Theme.textDim
                    font.pixelSize: 13
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Field {
                        id: gameField
                        Layout.fillWidth: true
                        onEditingFinished: cfg.setGameDir(text)
                    }
                    Btn {
                        variant: "secondary"
                        text: "Выбрать"
                        icon: "folder"
                        onClicked: folderDlg.open()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 6

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Text {
                            text: "Хранить версии отдельно"
                            color: Theme.text
                            font.pixelSize: 14
                        }
                        Text {
                            text: "Для каждой версии своя папка с сохранениями и модами"
                            color: Theme.textFaint
                            font.pixelSize: 12
                        }
                    }
                    Toggle {
                        checked: cfg.isolate
                        onToggled: cfg.setIsolate(checked)
                    }
                }

                Text {
                    Layout.topMargin: 6
                    text: "Разрешение окна игры"
                    color: Theme.textDim
                    font.pixelSize: 13
                }

                RowLayout {
                    spacing: 10

                    Field {
                        id: wField
                        Layout.preferredWidth: 110
                        validator: IntValidator {
                            bottom: 320
                            top: 7680
                        }
                        onEditingFinished: page.applyResolution()
                    }
                    Text {
                        text: "x"
                        color: Theme.textDim
                        font.pixelSize: 16
                    }
                    Field {
                        id: hField
                        Layout.preferredWidth: 110
                        validator: IntValidator {
                            bottom: 240
                            top: 4320
                        }
                        onEditingFinished: page.applyResolution()
                    }
                }

                Text {
                    Layout.topMargin: 6
                    text: "Аргументы Java"
                    color: Theme.textDim
                    font.pixelSize: 13
                }

                Field {
                    id: jvmField
                    Layout.fillWidth: true
                    placeholderText: "-XX:+UseG1GC -XX:MaxGCPauseMillis=50"
                    onEditingFinished: cfg.setJavaArgs(text)
                }
            }

            // ----- оформление -----
                        LauncherBehaviorCard { Layout.fillWidth: true }
                        DownloadSourceCard { Layout.fillWidth: true }
            Card {
                Layout.fillWidth: true
                padding: 24
                spacing: 14

                Text {
                    text: "Цвет акцента"
                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                RowLayout {
                    spacing: 12

                    Repeater {
                        model: page.accentColors

                        Rectangle {
                            id: swatch
                            readonly property bool chosen: backend.accent.toLowerCase() === modelData

                            width: 36
                            height: 36
                            radius: 18
                            color: modelData
                            border.width: swatch.chosen ? 3 : 0
                            border.color: "white"
                            scale: swMouse.containsMouse ? 1.1 : 1.0

                            Behavior on scale {
                                NumberAnimation { duration: 100 }
                            }

                            MouseArea {
                                id: swMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: backend.setAccent(modelData)
                            }
                        }
                    }
                }
            }

            // ----- обслуживание -----
            Card {
                Layout.fillWidth: true
                padding: 24
                spacing: 14

                Text {
                    text: "Обслуживание"
                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                RowLayout {
                    spacing: 10

                    Btn {
                        variant: "secondary"
                        text: "Очистить кэш"
                        onClicked: cfg.clearCache()
                    }
                    Btn {
                        variant: "secondary"
                        text: "Открыть папку игры"
                        icon: "folder"
                        onClicked: cfg.openGameDir()
                    }
                    Text {
                        leftPadding: 6
                        text: page.note
                        color: Theme.textDim
                        font.pixelSize: 13
                    }
                }
            }

            Item { Layout.preferredHeight: 8 }
        }
    }
}