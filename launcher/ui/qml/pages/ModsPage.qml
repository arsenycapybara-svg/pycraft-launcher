import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "../theme"
import "../components"

Item {
    id: page
    readonly property var host: Window.window
    property string tab: "installed"
    property string error: ""
    property string info: ""
    readonly property var kinds: [
        { id: "mods",          name: "Моды" },
        { id: "resourcepacks", name: "Ресурс-паки" },
        { id: "shaderpacks",   name: "Шейдеры" }
    ]

    function openSearch() {
        tab = "search"
        if (mods.results.length === 0)
            mods.search(searchField.text)
    }

    Component.onCompleted: mods.refresh()

    Connections {
        target: mods
        function onErrorOccurred(msg) { page.error = msg; page.info = "" }
        function onInfoMessage(msg) { page.info = msg; page.error = "" }
    }

    Timer {
        id: debounce
        interval: 450
        onTriggered: mods.search(searchField.text)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 14

        RowLayout {
            Layout.fillWidth: true

            Text {
                Layout.fillWidth: true
                text: "Моды и дополнения"
                color: Theme.text
                font.pixelSize: 28
                font.weight: Font.Bold
            }
            Btn {
                variant: "secondary"
                text: "Открыть папку"
                icon: "folder"
                enabled: instances.hasCurrent
                onClicked: mods.openFolder()
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: instances.hasCurrent
                  ? "Профиль: " + instances.current.name
                    + (instances.current.mc !== "" ? "  ·  " + instances.current.loader + " " + instances.current.mc : "")
                  : "Нет профиля. Создайте его во вкладке «Профили»."
            color: instances.hasCurrent ? Theme.textDim : Theme.warning
            font.pixelSize: 13
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: page.kinds
                Chip {
                    text: modelData.name
                    active: mods.kind === modelData.id
                    onClicked: {
                        mods.setKind(modelData.id)
                        if (page.tab === "search") mods.search(searchField.text)
                    }
                }
            }

            Item { Layout.fillWidth: true }

            Chip {
                text: "Установлено"
                active: page.tab === "installed"
                onClicked: page.tab = "installed"
            }
            Chip {
                text: "Каталог Modrinth"
                active: page.tab === "search"
                onClicked: page.openSearch()
            }
        }

        // ----- проверка зависимостей -----
        Card {
            visible: page.tab === "installed" && mods.kind === "mods" && mods.warnings.length > 0
            Layout.fillWidth: true
            padding: 14
            spacing: 8
            borderColor: Theme.warning

            Text {
                text: "Проверка зависимостей"
                color: Theme.warning
                font.pixelSize: 14
                font.weight: Font.DemiBold
            }

            Repeater {
                model: mods.warnings

                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        Layout.fillWidth: true
                        text: modelData.text
                        color: Theme.text
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                    Btn {
                        visible: modelData.project !== ""
                        text: "Установить"
                        enabled: !mods.installing
                        onClicked: { page.error = ""; mods.install(modelData.project) }
                    }
                }
            }
        }

        // ----- основное окно: список или каталог -----
        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 180
            padding: 8
            spacing: 0

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                // установленные файлы
                Item {
                    anchors.fill: parent
                    visible: page.tab === "installed"

                    ListView {
                        id: installedList
                        anchors.fill: parent
                        clip: true
                        spacing: 4
                        model: mods.installed
                        ScrollBar.vertical: ScrollBar {}

                        delegate: Rectangle {
                            id: row
                            property bool confirm: false
                            width: installedList.width - 12
                            height: 62
                            radius: 10
                            color: rowHover.containsMouse ? Theme.surfaceHover : "transparent"
                            Behavior on color { ColorAnimation { duration: Theme.animFast } }

                            Timer { id: confirmTimer; interval: 3000; onTriggered: row.confirm = false }

                            MouseArea {
                                id: rowHover
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.NoButton
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 12

                                PackIcon {
                                    source: modelData.icon
                                    label: modelData.title
                                    opacity: modelData.enabled ? 1.0 : 0.45
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.title
                                        color: modelData.enabled ? Theme.text : Theme.textFaint
                                        font.pixelSize: 14
                                        font.weight: Font.Medium
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: (modelData.version !== "" ? modelData.version + "  ·  " : "")
                                              + modelData.file + "  ·  " + modelData.size
                                        color: Theme.textFaint
                                        font.pixelSize: 12
                                        elide: Text.ElideMiddle
                                    }
                                }

                                Toggle {
                                    checked: modelData.enabled
                                    onToggled: mods.toggle(index)
                                }
                                Btn {
                                    variant: row.confirm ? "danger" : "ghost"
                                    text: row.confirm ? "Точно?" : "Удалить"
                                    onClicked: {
                                        if (!row.confirm) {
                                            row.confirm = true
                                            confirmTimer.restart()
                                            return
                                        }
                                        mods.remove(index)
                                    }
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        visible: installedList.count === 0
                        spacing: 6

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Здесь пока пусто"
                            color: Theme.textDim
                            font.pixelSize: 15
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Найдите дополнения в каталоге Modrinth или положите файлы в папку профиля"
                            color: Theme.textFaint
                            font.pixelSize: 12
                        }
                    }

                    Text {
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 6
                        visible: mods.checking || mods.note !== ""
                        text: mods.checking ? "Проверка через Modrinth..." : mods.note
                        color: Theme.textFaint
                        font.pixelSize: 11
                    }
                }

                // каталог
                ColumnLayout {
                    anchors.fill: parent
                    visible: page.tab === "search"
                    spacing: 8

                    Field {
                        id: searchField
                        Layout.fillWidth: true
                        placeholderText: "Поиск на Modrinth..."
                        onTextChanged: debounce.restart()
                        onAccepted: { debounce.stop(); mods.search(text) }
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        ListView {
                            id: resultsList
                            anchors.fill: parent
                            clip: true
                            spacing: 4
                            model: mods.results
                            ScrollBar.vertical: ScrollBar {}

                            footer: Item {
                                width: resultsList.width - 12
                                height: mods.canLoadMore ? 56 : 8

                                Btn {
                                    anchors.centerIn: parent
                                    visible: mods.canLoadMore
                                    variant: "secondary"
                                    text: mods.searching ? "Загрузка..." : "Показать ещё"
                                    enabled: !mods.searching
                                    onClicked: mods.loadMore()
                                }
                            }

                            delegate: Rectangle {
                                width: resultsList.width - 12
                                height: 88
                                radius: 10
                                color: resHover.containsMouse ? Theme.surfaceHover : "transparent"
                                Behavior on color { ColorAnimation { duration: Theme.animFast } }

                                MouseArea {
                                    id: resHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    acceptedButtons: Qt.NoButton
                                }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 12

                                    PackIcon {
                                        Layout.preferredWidth: 56
                                        Layout.preferredHeight: 56
                                        source: modelData.icon
                                        label: modelData.title
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 3

                                        RowLayout {
                                            spacing: 8
                                            Text {
                                                text: modelData.title
                                                color: Theme.text
                                                font.pixelSize: 15
                                                font.weight: Font.DemiBold
                                            }
                                            Text {
                                                text: "от " + modelData.author
                                                color: Theme.textFaint
                                                font.pixelSize: 12
                                            }
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData.description
                                            color: Theme.textDim
                                            font.pixelSize: 12
                                            wrapMode: Text.WordWrap
                                            maximumLineCount: 2
                                            elide: Text.ElideRight
                                        }
                                    }

                                    ColumnLayout {
                                        spacing: 6

                                        Text {
                                            Layout.alignment: Qt.AlignHCenter
                                            text: "↓ " + modelData.downloads
                                            color: Theme.textFaint
                                            font.pixelSize: 12
                                        }
                                        Btn {
                                            text: modelData.installed ? "✓ Установлено" : "Установить"
                                            variant: modelData.installed ? "secondary" : "primary"
                                            enabled: !modelData.installed && !mods.installing
                                            onClicked: { page.error = ""; page.info = ""; mods.install(modelData.id) }
                                        }
                                    }
                                }
                            }
                        }

                        Text {
                            anchors.centerIn: parent
                            visible: mods.searching && resultsList.count === 0
                            text: "Поиск..."
                            color: Theme.textDim
                            font.pixelSize: 15
                        }
                        Text {
                            anchors.centerIn: parent
                            visible: !mods.searching && resultsList.count === 0
                            text: "Ничего не найдено"
                            color: Theme.textDim
                            font.pixelSize: 15
                        }
                    }
                }
            }
        }

        ProgressPanel {
            Layout.fillWidth: true
            active: mods.installing
            title: "Установка"
            detail: mods.status
            progress: mods.progress > 0 ? mods.progress : -1
        }

        Text {
            visible: page.info !== ""
            Layout.fillWidth: true
            text: page.info
            color: Theme.success
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }

        ErrorBox { message: page.error }
    }
}