import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "../theme"
import "../components"

Item {
    id: page
    readonly property var host: Window.window
    property string editId: ""
    property string editVersion: ""
    property string editIcon: "grass"
    property string headId: ""
    property string customId: ""
    property bool editShared: false
    property string editPath: ""
    property bool confirmDelete: false
    property string formError: ""

    Component.onCompleted: instances.refresh()

    Connections {
        target: instances
        function onErrorOccurred(msg) { page.formError = msg }
    }

    // после окончания игры обновляем наигранное время
    Connections {
        target: game
        function onStateChanged() { if (game.phase === "idle") instances.refresh() }
    }

    Timer { id: delTimer; interval: 4000; onTriggered: page.confirmDelete = false }

    FileDialog {
        id: iconDlg
        title: "Своя иконка"
        nameFilters: ["Изображения (*.png *.jpg *.jpeg *.webp *.bmp)"]
        onAccepted: {
            var id = icons.importCustom(selectedFile.toString())
            if (id !== "") {
                page.customId = id
                page.editIcon = id
                page.formError = ""
            } else {
                page.formError = "Не удалось открыть изображение"
            }
        }
    }

    function openCreate() {
        instances.refresh()
        editId = ""
        editVersion = ""
        editIcon = "grass"
        headId = icons.makeHead()
        customId = ""
        editShared = false
        editPath = ""
        formError = ""
        confirmDelete = false
        nameField.text = ""
        argsField.text = ""
        customRam.checked = false
        ramSlide.value = Math.min(4096, cfg.maxRamMb)
        copyCombo.currentIndex = 0
        verCombo.currentIndex = Math.max(0, instances.installedVersions.indexOf(instances.selectedVersion))
        pop.open()
    }

    function openEdit(p) {
        instances.refresh()
        editId = p.id
        editVersion = p.versionId
        editIcon = p.icon
        headId = icons.makeHead()
        var own = p.icon.indexOf("custom:") === 0 || p.icon.indexOf("head:") === 0
        customId = (own && p.icon !== headId) ? p.icon : ""
        editShared = p.shared
        editPath = p.path
        formError = ""
        confirmDelete = false
        nameField.text = p.name
        argsField.text = p.javaArgs
        customRam.checked = p.ramMb > 0
        ramSlide.value = p.ramMb > 0 ? Math.min(p.ramMb, cfg.maxRamMb) : Math.min(4096, cfg.maxRamMb)
        verCombo.currentIndex = Math.max(0, instances.installedVersions.indexOf(p.versionId))
        pop.open()
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        padding: 28
        contentWidth: availableWidth

        ColumnLayout {
            width: scroll.availableWidth
            spacing: 16

            RowLayout {
                Layout.fillWidth: true

                Text {
                    Layout.fillWidth: true
                    text: "Профили"
                    color: Theme.text
                    font.pixelSize: 28
                    font.weight: Font.Bold
                }
                Btn {
                    text: "Новый профиль"
                    icon: "folder"
                    onClicked: page.openCreate()
                }
            }

            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "У каждого профиля своя версия игры и своя папка: моды, миры, ресурс-паки и настройки управления. "
                    + "Библиотеки и файлы игры общие, поэтому место не тратится дважды."
                color: Theme.textDim
                font.pixelSize: 13
            }

            Text {
                visible: instances.instances.length === 0
                text: "Профилей пока нет. Нажмите «Новый профиль»."
                color: Theme.textDim
                font.pixelSize: 14
            }

            Repeater {
                model: instances.instances

                delegate: Card {
                    Layout.fillWidth: true
                    padding: 16
                    borderColor: modelData.selected ? Theme.accent : Theme.border
                    color: modelData.selected ? Theme.surfaceHover : Theme.raised

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14

                        ProfileIcon {
                            size: 56
                            icon: modelData.icon
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            RowLayout {
                                spacing: 8

                                Text {
                                    text: modelData.name
                                    color: Theme.text
                                    font.pixelSize: 17
                                    font.weight: Font.DemiBold
                                }
                                Tag {
                                    visible: modelData.ok
                                    text: modelData.loader
                                }
                                Tag {
                                    visible: modelData.ok && modelData.mc !== ""
                                    text: modelData.mc
                                    tint: Theme.textDim
                                }
                                Tag {
                                    visible: modelData.shared
                                    text: "Общая папка"
                                    tint: Theme.warning
                                }
                                Tag {
                                    visible: !modelData.ok
                                    text: "Версия не установлена"
                                    tint: Theme.danger
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "Наиграно: " + modelData.playText + "  ·  " + modelData.lastPlayed
                                color: Theme.textDim
                                font.pixelSize: 12
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.version
                                color: Theme.textFaint
                                font.pixelSize: 12
                                elide: Text.ElideMiddle
                            }
                        }

                        Btn {
                            visible: !modelData.selected
                            variant: "secondary"
                            text: "Выбрать"
                            onClicked: instances.select(modelData.id)
                        }
                        Text {
                            visible: modelData.selected
                            text: "✓ Активный"
                            color: Theme.success
                            font.pixelSize: 13
                            font.weight: Font.Medium
                        }
                        Btn {
                            variant: "secondary"
                            text: "Папка"
                            icon: "folder"
                            onClicked: instances.openFolder(modelData.id)
                        }
                        Btn {
                            variant: "secondary"
                            text: "Изменить"
                            onClicked: page.openEdit(modelData)
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 8 }
        }
    }

    // ----- окно создания и правки профиля -----
    Popup {
        id: pop
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        width: 500
        padding: 22
        onClosed: page.confirmDelete = false

        Overlay.modal: Rectangle { color: "#99000000" }
        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 150 }
        }
        background: Rectangle {
            radius: Theme.radiusLg
            color: Theme.raised
            border.width: 1
            border.color: Theme.border
        }

        contentItem: ColumnLayout {
            spacing: 10

            Text {
                text: page.editId === "" ? "Новый профиль" : "Настройки профиля"
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.Bold
            }

            Text { text: "Иконка"; color: Theme.textDim; font.pixelSize: 13 }
            Grid {
                columns: 8
                spacing: 8

                // блоки
                Repeater {
                    model: icons.presets

                    ProfileIcon {
                        size: 46
                        icon: modelData.id
                        selected: page.editIcon === modelData.id
                        opacity: selected || presetMouse.containsMouse ? 1.0 : 0.7
                        scale: presetMouse.containsMouse ? 1.06 : 1.0
                        Behavior on opacity { NumberAnimation { duration: 100 } }
                        Behavior on scale { NumberAnimation { duration: 100 } }

                        MouseArea {
                            id: presetMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            ToolTip.visible: containsMouse
                            ToolTip.text: modelData.name
                            ToolTip.delay: 400
                            onClicked: page.editIcon = modelData.id
                        }
                    }
                }

                // голова вашего скина
                ProfileIcon {
                    visible: page.headId !== ""
                    size: 46
                    icon: page.headId !== "" ? page.headId : "grass"
                    selected: page.editIcon === page.headId
                    opacity: selected || headMouse.containsMouse ? 1.0 : 0.7
                    scale: headMouse.containsMouse ? 1.06 : 1.0
                    Behavior on opacity { NumberAnimation { duration: 100 } }
                    Behavior on scale { NumberAnimation { duration: 100 } }

                    MouseArea {
                        id: headMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        ToolTip.visible: containsMouse
                        ToolTip.text: "Мой скин (голова)"
                        ToolTip.delay: 400
                        onClicked: page.editIcon = page.headId
                    }
                }

                // своя картинка
                Item {
                    width: 46
                    height: 46
                    opacity: customMouse.containsMouse || page.editIcon === page.customId ? 1.0 : 0.7
                    scale: customMouse.containsMouse ? 1.06 : 1.0
                    Behavior on opacity { NumberAnimation { duration: 100 } }
                    Behavior on scale { NumberAnimation { duration: 100 } }

                    ProfileIcon {
                        anchors.fill: parent
                        visible: page.customId !== ""
                        size: 46
                        icon: page.customId !== "" ? page.customId : "grass"
                        selected: page.customId !== "" && page.editIcon === page.customId
                    }
                    Rectangle {
                        anchors.fill: parent
                        visible: page.customId === ""
                        radius: 9
                        color: Theme.bg
                        border.width: 1
                        border.color: Theme.border

                        Text {
                            anchors.centerIn: parent
                            text: "+"
                            color: Theme.textDim
                            font.pixelSize: 24
                        }
                    }

                    MouseArea {
                        id: customMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        ToolTip.visible: containsMouse
                        ToolTip.text: page.customId === "" ? "Загрузить свою иконку" : "Своя иконка (повторный клик — заменить)"
                        ToolTip.delay: 400
                        onClicked: {
                            if (page.customId !== "" && page.editIcon !== page.customId)
                                page.editIcon = page.customId
                            else
                                iconDlg.open()
                        }
                    }
                }
            }

            Text { text: "Название"; color: Theme.textDim; font.pixelSize: 13; topPadding: 4 }
            Field {
                id: nameField
                Layout.fillWidth: true
                placeholderText: "Например: Выживание 1.21"
            }

            Text { text: "Версия игры"; color: Theme.textDim; font.pixelSize: 13; topPadding: 4 }
            Combo {
                id: verCombo
                Layout.fillWidth: true
                visible: instances.installedVersions.length > 0
                model: instances.installedVersions
            }
            Text {
                visible: instances.installedVersions.length === 0
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Нет установленных версий. Установите версию во вкладке «Версии», затем выберите её здесь."
                color: Theme.warning
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 4
                spacing: 10

                Toggle { id: customRam }
                Text {
                    Layout.fillWidth: true
                    text: "Своя оперативная память"
                    color: Theme.text
                    font.pixelSize: 14
                }
                Text {
                    visible: customRam.checked
                    text: (ramSlide.value / 1024).toFixed(2) + " ГБ"
                    color: Theme.accent
                    font.pixelSize: 14
                    font.weight: Font.Bold
                }
            }
            Slide {
                id: ramSlide
                Layout.fillWidth: true
                visible: customRam.checked
                from: 1024
                to: cfg.maxRamMb
                stepSize: 256
                snapMode: Slider.SnapAlways
            }

            Text { text: "Дополнительные аргументы Java"; color: Theme.textDim; font.pixelSize: 13; topPadding: 4 }
            Field {
                id: argsField
                Layout.fillWidth: true
                placeholderText: "-XX:+UseG1GC"
            }

            ColumnLayout {
                visible: page.editId === ""
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "Скопировать настройки управления и список серверов из:"
                    color: Theme.textDim
                    font.pixelSize: 13
                    topPadding: 4
                }
                Combo {
                    id: copyCombo
                    Layout.fillWidth: true
                    model: ["Не копировать"].concat(instances.names)
                }
            }

            Text {
                visible: page.editId !== ""
                Layout.fillWidth: true
                wrapMode: Text.WrapAnywhere
                text: "Папка: " + page.editPath
                color: Theme.textFaint
                font.pixelSize: 12
            }

            Text {
                visible: page.formError !== ""
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: page.formError
                color: Theme.danger
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                spacing: 8

                Btn {
                    text: page.editId === "" ? "Создать" : "Сохранить"
                    onClicked: {
                        var ver = verCombo.visible ? verCombo.currentText : page.editVersion
                        var ram = customRam.checked ? Math.round(ramSlide.value) : 0
                        var copyId = ""
                        if (page.editId === "" && copyCombo.currentIndex > 0)
                            copyId = instances.idAt(copyCombo.currentIndex - 1)
                        page.formError = ""
                        if (instances.save(page.editId, nameField.text, ver, ram,
                                           argsField.text, copyId, page.editIcon))
                            pop.close()
                    }
                }
                Btn {
                    variant: "ghost"
                    text: "Отмена"
                    onClicked: pop.close()
                }

                Item { Layout.fillWidth: true }

                Btn {
                    visible: page.editId !== ""
                    variant: "danger"
                    text: page.confirmDelete
                          ? (page.editShared ? "Точно убрать?" : "Точно удалить вместе с мирами?")
                          : (page.editShared ? "Убрать из списка" : "Удалить профиль")
                    onClicked: {
                        if (!page.confirmDelete) {
                            page.confirmDelete = true
                            delTimer.restart()
                            return
                        }
                        instances.remove(page.editId, !page.editShared)
                        pop.close()
                    }
                }
            }
        }
    }
}