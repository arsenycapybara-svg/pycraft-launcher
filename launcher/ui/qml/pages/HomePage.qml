import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "../theme"
import "../components"

Item {
    id: page
    property string error: ""
    property bool showLog: false
    readonly property var host: Window.window
    readonly property bool installing: versions.installing
    readonly property bool hasAccount: backend.selectedName !== ""
    readonly property bool hasProfile: instances.hasCurrent
    readonly property bool profileOk: hasProfile && instances.current.ok
    readonly property bool canPlay: !installing && game.phase === "idle" && hasAccount && profileOk
    readonly property string playText: installing ? "Скачивание..."
        : game.phase === "launching" ? "Запуск..."
        : game.phase === "running" ? "Игра запущена" : "ИГРАТЬ"

    Component.onCompleted: instances.refresh()

    Connections {
        target: game
        function onErrorOccurred(msg) { page.error = msg; page.showLog = true }
        // после окончания игры обновляем наигранное время
        function onStateChanged() { if (game.phase === "idle") instances.refresh() }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 20

        // ----- левая колонка -----
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            Card {
                Layout.fillWidth: true
                tint: true
                padding: 28
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 20

                    ProfileIcon {
                        visible: page.hasProfile
                        size: 76
                        icon: page.hasProfile ? instances.current.icon : "cube"
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: "ПРОФИЛЬ"
                            color: Theme.textDim
                            font.pixelSize: 11
                            font.letterSpacing: 1.4
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: page.hasProfile ? instances.current.name : "Нет профилей"
                            color: Theme.text
                            font.pixelSize: 36
                            font.weight: Font.Bold
                            elide: Text.ElideRight
                        }

                        RowLayout {
                            spacing: 8

                            Tag {
                                visible: page.profileOk
                                text: page.profileOk ? instances.current.loader : ""
                            }
                            Tag {
                                visible: page.profileOk && instances.current.mc !== ""
                                text: page.profileOk ? instances.current.mc : ""
                                tint: Theme.textDim
                            }
                            Tag {
                                visible: page.hasProfile
                                text: page.hasProfile ? "Наиграно: " + instances.current.playText : ""
                                tint: Theme.success
                            }
                        }

                        Text {
                            text: page.hasAccount ? "Играть как " + backend.selectedName
                                                  : "Добавьте аккаунт, чтобы играть"
                            color: page.hasAccount ? Theme.textDim : Theme.warning
                            font.pixelSize: 15
                        }
                    }
                }

                RowLayout {
                    visible: page.hasProfile && !page.profileOk
                    spacing: 12

                    Text {
                        text: "В профиле не выбрана установленная версия игры."
                        color: Theme.warning
                        font.pixelSize: 14
                    }
                    Btn {
                        variant: "secondary"
                        text: "Открыть профили"
                        onClicked: if (page.host) page.host.go(1)
                    }
                }

                Item { Layout.preferredHeight: 18 }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Combo {
                        Layout.preferredWidth: 300
                        Layout.preferredHeight: 56
                        visible: page.hasProfile
                        enabled: game.phase === "idle"
                        model: instances.names
                        currentIndex: instances.selectedIndex
                        onActivated: instances.selectIndex(currentIndex)
                    }

                    Btn {
                        visible: !page.hasProfile
                        variant: "secondary"
                        text: "Создать профиль"
                        icon: "folder"
                        Layout.preferredHeight: 56
                        onClicked: if (page.host) page.host.go(1)
                    }

                    Btn {
                        Layout.preferredWidth: 240
                        Layout.preferredHeight: 56
                        fontSize: 17
                        text: page.playText
                        icon: page.canPlay ? "play" : ""
                        enabled: page.canPlay
                        onClicked: { page.error = ""; game.play() }
                    }

                    Btn {
                        visible: game.phase !== "idle"
                        variant: "danger"
                        text: "Стоп"
                        icon: "stop"
                        Layout.preferredHeight: 56
                        onClicked: game.stop()
                    }

                    Item { Layout.fillWidth: true }

                    Btn {
                        variant: "ghost"
                        text: page.showLog ? "Скрыть лог" : "Лог"
                        onClicked: page.showLog = !page.showLog
                    }
                }
            }

            ProgressPanel {
                Layout.fillWidth: true
                active: page.installing || game.phase === "launching"
                title: page.installing ? "Установка версии" : "Запуск игры"
                detail: page.installing ? versions.status : game.status
                progress: page.installing && versions.progress > 0 ? versions.progress : -1
            }

            ErrorBox { message: page.error }

            Card {
                visible: page.showLog
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 140
                color: Theme.bg
                padding: 12

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    TextArea {
                        readOnly: true
                        text: game.log
                        color: Theme.textDim
                        font.family: "monospace"
                        font.pixelSize: 12
                        wrapMode: TextEdit.NoWrap
                        background: null
                        onTextChanged: cursorPosition = length
                    }
                }
            }

            Item { Layout.fillHeight: true; visible: !page.showLog }
        }

        // ----- правая колонка: аккаунт и 3D-скин -----
        SkinCard {
            Layout.preferredWidth: 340
            Layout.fillHeight: true
        }
    }
}